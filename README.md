# HELIOS

**Apache-2.0 ambassador** — not a Synaptic Four product SKU. HELIOS produces technical audit evidence for genomics pipelines. It **reads export JSON from disk**; it does **not** call other product APIs and does **not** orchestrate them. It is **not** a certification, accreditation, legal determination, or regulatory approval.

**Maturity: Early access.** Alpha→Beta: [`docs/ALPHA-TO-BETA.md`](docs/ALPHA-TO-BETA.md).

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Status](https://img.shields.io/badge/status-alpha-orange.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![CI](https://img.shields.io/github/actions/workflow/status/SynapticFour/HELIOS/ci.yml?branch=main)

These public repositories are maintained by the same organisation and are designed to work together. Each repository keeps its own version and license. For details on roles, maturity, and how the components relate to one another, see [SUITE-OVERVIEW](https://github.com/SynapticFour/.github/blob/main/profile/SUITE-OVERVIEW.md).

## Quick start

The package name is `helios-audit`. **PyPI has `0.1.1`** (git tag `v0.1.1`). Later commits on `main` may be ahead of that tag. `pip install helios-audit==0.1.1` matches the tag, not necessarily HEAD.

```bash
pip install -e ".[dev]"
make prove
```

`make prove` signs a fixture chain and rejects tamper. No Nextflow, no network. Details: [`docs/PROVE.md`](docs/PROVE.md). Evaluator snapshot: [`docs/FOR-EVALUATORS.md`](docs/FOR-EVALUATORS.md).

Optional dashboard: `make up` (requires `HELIOS_DASHBOARD_API_KEY`) → http://127.0.0.1:8765/static/index.html.

Solum writes a HELIOS-oriented export; HELIOS **ingests the file** (`helios solum-audit --export …`). Operator notes: [`docs/operator.md`](docs/operator.md). Index: [`docs/index.md`](docs/index.md).

## License

Apache License 2.0 — see [LICENSE](LICENSE).
