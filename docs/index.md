# HELIOS Documentation

**Status: Alpha.** HELIOS is a Genomics Pipeline Audit & Validation Framework that wraps Nextflow and Snakemake runs to generate signed, reproducible compliance evidence. Install from source (see [quickstart](quickstart.md)); the `helios-audit` name is reserved for a future PyPI release and is not published yet.

- Start with the [quickstart](quickstart.md)
- Review [architecture decisions](architecture.md)
- Explore compliance mappings (engineering orientation, not certification):
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

## Notice

HELIOS is alpha software. Documentation describes technical controls and generated evidence. It does not constitute legal advice or a formal certification by itself.
