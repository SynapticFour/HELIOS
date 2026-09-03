# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- README / IDENTITY: Helix/HelixTest are the VERIFY/conformance tools. HELIOS stays evidence/reproducibility. Pointer: https://github.com/SynapticFour/Helix/blob/main/docs/HELIX_VS_HELIOS.md

## [0.1.1] - 2026-08-17

PyPI catch-up: `helios-audit==0.1.1` matches git tag `v0.1.1`. Later `main` may be ahead.

### Changed

- **GA4GH-WES-DRS-001** (`ferrum_wes_outputs`) — when a Ferrum WES run is in context, outputs must be DRS ids (`drs://…` or `drs.`). Local BAM/VCF hashes alone fail. No WES context → skip. Default `helios.toml.example` enables it. HELIOS still does not call Ferrum.
- CI and Release test jobs run `make prove` (sign/tamper; no coverage gate on the subset).
- `docs/PROVE.md`: the 80 % coverage gate is `make test`, not `make prove`.

## [0.1.0] - 2026-08-15

First tagged release of `helios-audit`. Technical audit evidence only — not certification.

### Breaking
- Checks are fail-closed: empty container scans, unproven references, suffix-only Crypt4GH, and empty VUS sets no longer pass
- Skip-only suites grade `N/A` (score `null`), never 100
- `helios run` and `helios validate` exit 1 on failed checks or untrusted signatures
- Signing is required unless `--no-sign`; missing keys error instead of silent unsigned store
- Signature verify uses `trusted_keys_dir` only; embedded PEM is not a trust root
- `helios key generate` requires `HELIOS_KEY_PASSPHRASE` or `--allow-unencrypted`
- Empty `checks.enabled` is an error
- `container_digest_required` defaults to true
- Dashboard bind in Compose is `127.0.0.1:8765`; UI no longer loads CDN scripts or stores the API key in sessionStorage
- CLIN-ACCESS-001 verifies the Solum hash chain and fails when there are zero clinical events

### Added
- `make prove` — unit tests plus a sign/tamper round-trip on a fixture chain (`--no-cov` so the coverage gate does not apply to the subset)
- Trust-store verification (`trusted_keys_dir`)
- Import size limit (`dashboard.max_import_bytes`)
- Command timeout (`command_timeout_seconds`)
- `requirements.lock` and ADRs under `docs/decisions/`
- Operator reference (`docs/operator.md`)
- `make test` / `make lint`
- Core audit record model with Ed25519 signing
- Nextflow trace parser and plugin interface
- Snakemake integration
- Compliance checks: reference_genome, container_pinning, mane_transcripts, vus_rate, crypt4gh_output
- RO-Crate 1.1 export format
- PDF compliance report generation
- Optional EU AI Act Article 11 provenance stub
- Web dashboard with FastAPI backend and vanilla JS frontend
- Docker support

### Security
- `helios config print` redacts API keys
- SQLite DB/dir modes 0600/0700 when the process can chmod
- Gitleaks scans git history; CodeQL runs on PRs; dependency-review is blocking; release runs tests before PyPI
