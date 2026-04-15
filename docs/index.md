# HELIOS Documentation

HELIOS is a Genomics Pipeline Audit & Validation Framework that wraps Nextflow and Snakemake runs to generate signed, reproducible compliance evidence.

- Start with the [quickstart](quickstart.md)
- Review [architecture decisions](architecture.md)
- Explore compliance mappings:
  - [ISO 15189:2022](compliance/iso15189.md)
  - [GA4GH](compliance/ga4gh.md)
  - [EU AI Act](compliance/ai_act.md)

## Delivery and Assurance

- CI pipeline: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- Security workflows:
  - [CodeQL](../.github/workflows/codeql.yml)
  - [Secret Scan](../.github/workflows/secret-scan.yml)
  - [Dependency Review](../.github/workflows/dependency-review.yml)
- Security policy: [SECURITY.md](../SECURITY.md)
- Contribution policy: [CONTRIBUTING.md](../CONTRIBUTING.md)
- Code of Conduct: [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
- Parity status: [REPO-PARITY-REPORT.md](REPO-PARITY-REPORT.md)

## Notice

HELIOS documentation describes technical controls and generated evidence. It does
not constitute legal advice or a formal certification by itself.

