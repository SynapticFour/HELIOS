"""MANE transcript usage check with NCBI MANE cache support."""

from __future__ import annotations

import gzip
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext

MANE_BASE_URL = "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/"
MANE_GLOB_REFERENCE = f"{MANE_BASE_URL}MANE.GRCh38.v*.summary.txt.gz"
MANE_PATTERN = re.compile(r"MANE\.GRCh38\.v[0-9.]+\.summary\.txt\.gz")


class MANETranscriptCheck(BaseCheck):
    """Cross-reference VCF transcript annotations with MANE Select/Plus Clinical."""

    check_id = "GA4GH-MANE-001"
    name = "MANE Transcript Usage"
    description = "Assess fraction of variant transcript annotations using MANE."
    severity = "warning"
    standards = ["ACMG-2023-reporting", "GA4GH-GKS-1.0"]

    def __init__(self, cache_dir: Path | None = None, ttl_days: int = 7) -> None:
        self.cache_dir = cache_dir or Path("~/.helios/cache/mane").expanduser()
        self.ttl_days = ttl_days

    def run(self, context: RunContext) -> CheckResult:
        """Run transcript coverage check using MANE summary list."""
        vcfs = [
            p
            for p in context.artifacts
            if p.suffix in {".vcf", ".gz"} and "vcf" in p.name.lower()
        ]
        if not vcfs:
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message="No VCF artifacts available for MANE transcript check.",
                evidence={},
            )

        mane_ids, mane_version = self._load_mane_summary()
        total_variants = 0
        mane_annotated = 0
        non_mane_seen: list[str] = []
        for vcf in vcfs:
            for line in vcf.read_text(encoding="utf-8").splitlines():
                if not line or line.startswith("#"):
                    continue
                transcripts = self._extract_transcript_ids(line)
                if not transcripts:
                    continue
                total_variants += 1
                if any(tx in mane_ids for tx in transcripts):
                    mane_annotated += 1
                else:
                    non_mane_seen.extend(transcripts[:2])

        if total_variants == 0:
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message="No transcript annotations found in VCF outputs.",
                evidence={
                    "total_variants": 0,
                    "mane_annotated": 0,
                    "non_mane_transcripts": [],
                    "mane_version": mane_version,
                },
            )
        ratio = mane_annotated / total_variants
        evidence = {
            "total_variants": total_variants,
            "mane_annotated": mane_annotated,
            "non_mane_transcripts": sorted(set(non_mane_seen))[:10],
            "mane_version": mane_version,
        }
        if ratio >= 0.9:
            return CheckResult(
                check_id=self.check_id,
                status="pass",
                message=f"MANE transcript usage {ratio:.1%} meets threshold.",
                evidence=evidence,
            )
        if ratio >= 0.5:
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message=f"MANE transcript usage {ratio:.1%} is partial.",
                evidence=evidence,
            )
        return CheckResult(
            check_id=self.check_id,
            status="fail",
            message=f"MANE transcript usage {ratio:.1%} is below minimum expectations.",
            evidence=evidence,
        )

    def _extract_transcript_ids(self, vcf_line: str) -> list[str]:
        info_field = vcf_line.split("\t", maxsplit=8)[7] if "\t" in vcf_line else ""
        annotations: list[str] = []
        for token in info_field.split(";"):
            if token.startswith("ANN=") or token.startswith("CSQ="):
                annotations.extend(token.split("=", 1)[1].split(","))
        transcript_ids: list[str] = []
        for annotation in annotations:
            fields = annotation.split("|")
            for field in fields:
                if field.startswith("NM_") or field.startswith("ENST"):
                    transcript_ids.append(field.split(".")[0])
        return transcript_ids

    def _load_mane_summary(self) -> tuple[set[str], str]:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cached = self._latest_cached_file()
        if cached and self._is_cache_fresh(cached):
            return self._parse_mane_file(cached), self._version_from_name(cached.name)
        downloaded = self._download_mane_summary()
        return self._parse_mane_file(downloaded), self._version_from_name(downloaded.name)

    def _latest_cached_file(self) -> Path | None:
        candidates = sorted(self.cache_dir.glob("MANE.GRCh38.v*.summary.txt.gz"))
        return candidates[-1] if candidates else None

    def _is_cache_fresh(self, path: Path) -> bool:
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        return datetime.now(UTC) - modified < timedelta(days=self.ttl_days)

    def _download_mane_summary(self) -> Path:
        """Download current MANE GRCh38 summary file matching v*.summary.txt.gz."""
        with httpx.Client(timeout=30.0) as client:
            listing = client.get(MANE_BASE_URL).text
            match = MANE_PATTERN.search(listing)
            if match is None:
                raise RuntimeError(
                    "Unable to locate MANE summary file from NCBI listing "
                    f"using pattern {MANE_GLOB_REFERENCE}."
                )
            filename = match.group(0)
            content = client.get(f"{MANE_BASE_URL}{filename}").content
        path = self.cache_dir / filename
        path.write_bytes(content)
        return path

    def _parse_mane_file(self, path: Path) -> set[str]:
        transcripts: set[str] = set()
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            reader = handle.read().splitlines()
        for line in reader[1:]:
            cols = line.split("\t")
            if len(cols) < 6:
                continue
            for candidate in cols:
                if candidate.startswith("NM_") or candidate.startswith("ENST"):
                    transcripts.add(candidate.split(".")[0])
        return transcripts

    def _version_from_name(self, filename: str) -> str:
        match = re.search(r"(v[0-9.]+)", filename)
        return match.group(1) if match else "unknown"


ManeTranscriptCheck = MANETranscriptCheck

