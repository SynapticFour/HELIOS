# For evaluators

Factual snapshot of this repository. Not a sales brief. Not legal advice. Not a certification.

## Maturity

**Early access.** Apache-2.0 ambassador — not a Synaptic Four product SKU. Alpha→Beta notes: [ALPHA-TO-BETA.md](ALPHA-TO-BETA.md).

HELIOS **reads export JSON from disk**. It does **not** call Ferrum or Solum APIs and does **not** orchestrate those products.

## License

Apache License 2.0 — see [LICENSE](../LICENSE).

## Tested in this tree

| Claim | Evidence |
|-------|----------|
| Fixture sign / tamper reject | `make prove` (no Nextflow, no Ferrum, no network) |
| Coverage gate | `make test` (`pytest --cov-fail-under=80`) — not the same as `make prove` |

## Not tested / not claimed

| Topic | Status |
|-------|--------|
| PyPI equals git HEAD | **No.** PyPI has `helios-audit` **0.1.0**. HEAD on this repo is ahead. For current ambassador code, install from git. |
| Live Ferrum / Solum HTTP | Not implemented. Solum writes an export file; HELIOS ingests the file. |
| Laboratory accreditation / ISO 15189 certificate | Orientation only. Evidence you still interpret in your QMS. |
| Combo SKU with Ferrum or Solum | Does not exist. |

## Contact

Questions can be sent to [contact@synapticfour.com](mailto:contact@synapticfour.com).
