# HELIOS Documentation

**Status: Alpha.** HELIOS is a Genomics Pipeline Audit & Validation Framework that wraps Nextflow and Snakemake runs to generate signed, reproducible compliance evidence. **`helios-audit` v0.1.0 is on PyPI** — `pip install helios-audit` (see [quickstart](quickstart.md) and [RELEASING.md](../RELEASING.md)). HELIOS is **not** a certification, not an orchestrator of Ferrum or Solum, and not a Synaptic Four product SKU (free Apache-2.0 ambassador).

- Start with the [quickstart](quickstart.md)
- **Operator reference** (config, env, CLI, exit codes, trust store): [operator.md](operator.md)
- **Solum clinical ingest:** [solum-ingest.md](solum-ingest.md) (`helios solum-audit`, CLIN-ACCESS-001)
- Review [architecture](architecture.md) and [ADRs](decisions/README.md) ([0001 fail-closed](decisions/0001-fail-closed-evidence.md), [0002 trust store](decisions/0002-trust-store.md))
- **Threat model:** [THREAT_MODEL.md](THREAT_MODEL.md) · **Incident response:** [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md)
- Explore compliance mappings (engineering orientation, not certification):
  - [ISO 15189:2022](compliance/iso15189.md)
  - [GA4GH](compliance/ga4gh.md)
  - [EU AI Act](compliance/ai_act.md)

## Delivery and Assurance

- CI pipeline: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- PyPI release workflow: [`.github/workflows/release.yml`](../.github/workflows/release.yml) — operator steps in [RELEASING.md](../RELEASING.md)
- Security workflows:
  - [CodeQL](../.github/workflows/codeql.yml)
  - [Secret Scan](../.github/workflows/secret-scan.yml)
  - [Dependency Review](../.github/workflows/dependency-review.yml)
- Dashboard API requires `HELIOS_DASHBOARD_API_KEY` (see README / `.env.example`); UI stores the key in memory only
- Local quality gate: `make test` (ruff + mypy + pytest `--cov-fail-under=80`)
- Security policy: [SECURITY.md](../SECURITY.md)
- Contribution policy: [CONTRIBUTING.md](../CONTRIBUTING.md)
- Code of Conduct: [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)

## Notice

HELIOS is alpha software. Documentation describes technical controls and generated evidence. It does not constitute legal advice or a formal certification by itself.
