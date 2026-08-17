# HELIOS

**Apache-2.0 ambassador** — not a Synaptic Four product SKU. HELIOS produces technical audit evidence for genomics pipelines. It **reads export JSON from disk**; it does **not** call Ferrum or Solum APIs and does **not** orchestrate those products. It is **not** a certification, accreditation, legal determination, or regulatory approval.

**Maturity: Early access.** Alpha→Beta: [`docs/ALPHA-TO-BETA.md`](docs/ALPHA-TO-BETA.md).

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Status](https://img.shields.io/badge/status-alpha-orange.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![CI](https://img.shields.io/github/actions/workflow/status/SynapticFour/HELIOS/ci.yml?branch=main)

## Ferrum / GA4GH suite

These ten public repositories are from the same organisation and can be composed. They are not a fifth product and not a bundle SKU. Each repository keeps its own version and license. Roles, maturity, and who consumes whom: [SUITE-OVERVIEW](https://github.com/SynapticFour/Ferrum/blob/main/docs/SUITE-OVERVIEW.md).

## Quick start

The package name is `helios-audit`. **PyPI has `0.1.0`.** HEAD on this repo is **ahead of PyPI** (WES DRS-id check, honesty mapping). For the code on `main`, install from git — do not assume `pip install helios-audit` equals this tree.

```bash
pip install -e ".[dev]"
make prove
```

`make prove` signs a fixture chain and rejects tamper. No Nextflow, no Ferrum, no network. Details: [`docs/PROVE.md`](docs/PROVE.md). Evaluator snapshot: [`docs/FOR-EVALUATORS.md`](docs/FOR-EVALUATORS.md).

Optional dashboard: `make up` (requires `HELIOS_DASHBOARD_API_KEY`) → http://127.0.0.1:8765/static/index.html.

Solum writes a HELIOS-oriented export; HELIOS **ingests the file** (`helios solum-audit --export …`). Operator notes: [`docs/operator.md`](docs/operator.md). Index: [`docs/index.md`](docs/index.md).

## License

Apache License 2.0 — see [LICENSE](LICENSE).
