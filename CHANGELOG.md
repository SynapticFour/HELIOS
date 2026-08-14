# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `POST /api/v1/runs/import?allow_unsigned=true` opt-in for unsigned audit JSON (default reject)
- Dashboard API-key authentication (`HELIOS_DASHBOARD_API_KEY`); unauthenticated `/api/v1/*` rejected
- `RELEASING.md` with `v0.1.0` cut steps and Trusted Publisher precondition
- Release workflow metadata check for `helios-audit` name/version alignment
- Packaged `helios.toml.example` so `helios init` works after `pip install`
- Optional `helios-audit[pdf]` extra (WeasyPrint); CI tests Python 3.11 and 3.12

### Fixed
- Wrapped pipeline non-zero exit no longer produces a signed audit (`helios run`)
- Default `mane_transcripts` config name now enables GA4GH-MANE-001; unknown check names error
- Signing keys written mode 0600; signature envelope embeds the public key for third-party verify
- Check crashes (including bgzip VCF decode) become fail results instead of aborting the run
- Nextflow parser finds `trace.txt` / `nextflow.config` in the launch directory, parses the trace once, and no longer walks outputs per task
- `list_records` is newest-first; dashboard pagination applies offset after filters
- `skip` no longer counts as full credit; CLIN-ACCESS-001 returns `skip` when no export is supplied
- Duplicate `run_id` rejected; dashboard delete requires `dashboard.allow_delete`
- `helios status` / `helios serve` honor `[helios]` TOML the same way `helios run` does
- CLI records `pipeline_version` and hashes trace/config/parameter files as inputs
- Container pinning scans pipeline source (not Nextflow `work/`) and ignores `conda =` lines
- GRCh38 dashboard adoption uses GA4GH-REF-001 pass, not a substring search
- Dashboard UI escapes record fields; downloads use `X-API-Key` instead of `?api_key=`
- Missing `--config` path errors instead of silently loading defaults
- Query-string `?api_key=` is no longer accepted; use headers only
- Existing SQLite DBs get a unique `run_id` index (duplicates keep the newest `start_time`)
- Report downloads delete temp JSON/PDF/RO-Crate files after the response
- Passing `GA4GH-REF-001` fills `AuditRecord.reference_genome` before sign/persist
- `helios key generate` warns when `HELIOS_KEY_PASSPHRASE` is unset (keys stay mode 0600)

### Changed
- AI Act Article 11 fragment is opt-in (`export.ai_act_fragment`) and no longer auto-labels `high_risk`
- SQLite uses WAL and `check_same_thread=False`; MANE/VUS stream VCF INFO (including `.vcf.gz`)
- `AuditRecord.executor` is `nextflow` | `snakemake` | `unknown` (no unused `cwl` value)

## [0.1.0] - 2025-Q2

### Added
- Core audit record model with Ed25519 signing
- Nextflow trace parser and plugin interface
- Snakemake integration
- Five compliance checks: reference_genome, container_pinning, mane_transcripts, vus_rate, crypt4gh_output
- RO-Crate 1.1 export format
- PDF compliance report generation
- EU AI Act Article 11 documentation fragment export
- Web dashboard with FastAPI backend and vanilla JS frontend
- Docker support
- Full test suite with >80% coverage
