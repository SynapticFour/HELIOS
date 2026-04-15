# HELIOS

```text
 _   _ _____ _     ___ ___  ____
| | | | ____| |   |_ _/ _ \/ ___|
| |_| |  _| | |    | | | | \___ \
|  _  | |___| |___ | | |_| |___) |
|_| |_|_____|_____|___\___/|____/
```

Genomics Pipeline Audit & Validation Framework for signed, reproducible compliance evidence.

![PyPI](https://img.shields.io/pypi/v/helios-audit)
![Python](https://img.shields.io/pypi/pyversions/helios-audit)
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![CI](https://img.shields.io/github/actions/workflow/status/example/helios/ci.yml?branch=main)

## Why HELIOS?

Clinical genomics labs need reproducible, machine-verifiable audit trails:

- **ISO 15189:2022**: evidence for software validation, traceability, and reporting.
- **GA4GH standards**: operational alignment with interoperable genomics ecosystems.
- **EU AI Act**: technical documentation and data governance artifacts (Articles 10/11).

HELIOS wraps pipeline execution, captures immutable run context, performs compliance checks, and exports signed reports.

## Install

```bash
pip install helios-audit
```

## 5-minute Quickstart (Nextflow)

```bash
helios init
helios key generate
helios run --pipeline nextflow --work-dir ./work --output-dir ./results
helios status
helios report --run-id <run-id> --format json
```

## Documentation

See [`docs/index.md`](docs/index.md).

## Compliance Coverage

| Standard | Coverage |
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

