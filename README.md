# HELIOS

```text
 _   _ _____ _     ___ ___  ____
| | | | ____| |   |_ _/ _ \/ ___|
| |_| |  _| | |    | | | | \___ \
|  _  | |___| |___ | | |_| |___) |
|_| |_|_____|_____|___\___/|____/
```

**Status: Alpha** — early development. HELIOS produces technical audit evidence for genomics pipelines. It is **not** a certification, accreditation, legal determination, or regulatory approval.

Genomics Pipeline Audit & Validation Framework for signed, reproducible compliance evidence.

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Status](https://img.shields.io/badge/status-alpha-orange.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![CI](https://img.shields.io/github/actions/workflow/status/SynapticFour/HELIOS/ci.yml?branch=main)

## Why HELIOS?

Clinical genomics labs need reproducible, machine-verifiable audit trails:

- **ISO 15189:2022**: evidence for software validation, traceability, and reporting.
- **GA4GH standards**: operational alignment with interoperable genomics ecosystems.
- **EU AI Act**: technical documentation and data governance artifacts (Articles 10/11).

HELIOS wraps pipeline execution, captures immutable run context, performs compliance checks, and exports signed reports. Mappings to standards are engineering orientation, not a certificate that your lab is compliant.

## Install

The package name is `helios-audit`. **Until `v0.1.0` is tagged and published to PyPI, install from source.** After that release, `pip install helios-audit` works. See [`RELEASING.md`](RELEASING.md) for the operator tag steps (Trusted Publisher must be configured first).

```bash
# editable install from a clone (current recommended path)
git clone https://github.com/SynapticFour/HELIOS.git
cd HELIOS
pip install -e .

# or one-shot from GitHub
pip install "git+https://github.com/SynapticFour/HELIOS.git"

# after v0.1.0 is on PyPI:
# pip install helios-audit
```

Development extras: `pip install -e ".[dev]"` (see [`CONTRIBUTING.md`](CONTRIBUTING.md)).

## 5-minute Quickstart (Nextflow)

```bash
helios init
helios key generate
helios run --pipeline nextflow --work-dir ./work --output-dir ./results
helios status
helios report --run-id <run-id> --format json
```

### Optional dashboard (Docker)

The dashboard requires an API key (`HELIOS_DASHBOARD_API_KEY`). Unauthenticated `/api/v1/*` requests are rejected.

```bash
export HELIOS_DASHBOARD_API_KEY=$(openssl rand -hex 32)   # or copy .env.example → .env
make up        # http://localhost:8765/static/index.html
make down
make destroy
```

CLI equivalent: `HELIOS_DASHBOARD_API_KEY=... helios serve`. Pass the key as `X-API-Key`, `Authorization: Bearer`, HTTP Basic password, or `?api_key=` (browser UI prompts and stores it in `sessionStorage`).

## Documentation

See [`docs/index.md`](docs/index.md). Release process: [`RELEASING.md`](RELEASING.md).

## CI, Security, and Governance

- Primary quality pipeline: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- PyPI publish on tag `v*`: [.github/workflows/release.yml](.github/workflows/release.yml) (see [`RELEASING.md`](RELEASING.md))
- Security/compliance automation:
  - [.github/workflows/codeql.yml](.github/workflows/codeql.yml)
  - [.github/workflows/secret-scan.yml](.github/workflows/secret-scan.yml)
  - [.github/workflows/dependency-review.yml](.github/workflows/dependency-review.yml)
- **Dependency Review** requires the GitHub **Dependency graph** for this repository (repository owner: **Settings → Security → Code security and analysis → Dependency graph**).
- Repo governance:
  - [`SECURITY.md`](SECURITY.md)
  - [`CONTRIBUTING.md`](CONTRIBUTING.md)
  - [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
  - [`.github/pull_request_template.md`](.github/pull_request_template.md)

## Compliance Coverage (engineering orientation)

| Standard | Coverage (technical controls / evidence — not certification) |
|---|---|
| ISO 15189:2022 | Validation traceability, software controls, reportability |
| GA4GH | Reference integrity, transcript evidence, crypt4gh outputs |
| EU AI Act Art. 10/11 | Data lineage, technical documentation exports |

## Architecture

```text
CLI (Typer)
   |
   +-- Integrations (Nextflow / Snakemake)
   |
   +-- Checks (reference, container pinning, MANE, VUS, crypt4gh)
   |
   +-- Core (audit model, signer, hasher, storage)
   |
   +-- Export (JSON / PDF / RO-Crate)
   |
   +-- Dashboard API (FastAPI)
```

## Contributing

Contributions are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Apache 2.0. See [`LICENSE`](LICENSE).

## Important Notice

HELIOS is alpha software. It provides technical quality and compliance evidence support. It is not, by itself, a certification decision, legal determination, or regulatory approval.
