"""Container pinning check for Nextflow and Snakemake workflows."""

from __future__ import annotations

import re
from pathlib import Path

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext

CONTAINER_REGEX = re.compile(r"container\s*[:=]\s*['\"]([^'\"]+)['\"]")


class ContainerPinningCheck(BaseCheck):
    """Ensure workflow container references are fully pinned."""

    check_id = "SEC-CONTAINER-001"
    name = "Container Pinning"
    description = "Container references must avoid floating tags."
    severity = "warning"
    standards = ["ISO15189:2022-5.6", "GA4GH-TRS-2.0"]

    def run(self, context: RunContext) -> CheckResult:
        """Scan workflow definitions for unsafe container references."""
        root = context.project_dir or context.work_dir
        candidates = self._discover_candidate_files(root)
        found: list[str] = []
        failures: list[str] = []
        warnings: list[str] = []
        digest_required = bool(self.settings and self.settings.checks.container_digest_required)

        for path in candidates:
            content = path.read_text(encoding="utf-8")
            for ref in CONTAINER_REGEX.findall(content):
                found.append(ref)
                if ref.endswith(":latest") or (":" not in ref and "@sha256:" not in ref):
                    failures.append(ref)
                elif ":" in ref and "@sha256:" not in ref:
                    warnings.append(ref)

        if digest_required and warnings:
            failures.extend(warnings)
            warnings = []

        if failures:
            failure_list = ", ".join(sorted(set(failures)))
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message=f"Found floating or unpinned containers: {failure_list}",
                evidence={"containers_scanned": str(len(found))},
            )
        if warnings:
            warning_list = ", ".join(sorted(set(warnings)))
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message=f"Containers have tags but no digest pinning: {warning_list}",
                evidence={"containers_scanned": str(len(found))},
            )
        return CheckResult(
            check_id=self.check_id,
            status="pass",
            message="All container definitions are pinned.",
            evidence={"containers_scanned": str(len(found))},
        )

    def _discover_candidate_files(self, root: Path) -> list[Path]:
        """Scan pipeline source files, not Nextflow task scratch trees."""
        if not root.exists():
            return []
        names = {"Snakefile", "nextflow.config"}
        patterns = ("*.nf", "*.smk", "*.config", "modules/**/*.nf", "workflows/**/*.nf")
        files: list[Path] = []
        seen: set[Path] = set()
        for path in root.iterdir() if root.is_dir() else []:
            if path.is_file() and (path.suffix in {".nf", ".smk", ".config"} or path.name in names):
                files.append(path)
                seen.add(path)
        for pattern in patterns:
            for path in root.glob(pattern):
                if path.is_file() and path not in seen:
                    files.append(path)
                    seen.add(path)
        return files
