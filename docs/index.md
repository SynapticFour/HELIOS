# HELIOS Documentation

**Status: Alpha.** HELIOS is a Genomics Pipeline Audit & Validation Framework that wraps Nextflow and Snakemake runs to generate signed, reproducible compliance evidence. Install from source until `v0.1.0` is tagged and published (see [quickstart](quickstart.md) and [RELEASING.md](../RELEASING.md)). HELIOS is **not** a certification or regulatory approval.

- Start with the [quickstart](quickstart.md)
- **Solum clinical ingest:** [solum-ingest.md](solum-ingest.md) (`helios solum-audit`, CLIN-ACCESS-001)
- Review [architecture decisions](architecture.md)
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
- Dashboard API requires `HELIOS_DASHBOARD_API_KEY` (see README / `.env.example`)
- Security policy: [SECURITY.md](../SECURITY.md)
- Contribution policy: [CONTRIBUTING.md](../CONTRIBUTING.md)
- Code of Conduct: [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)

## Notice

HELIOS is alpha software. Documentation describes technical controls and generated evidence. It does not constitute legal advice or a formal certification by itself.
