# Who HELIOS is for

HELIOS (`helios-audit` on PyPI) is a **free Apache-2.0 ambassador**: signed, reproducible evidence for genomics pipeline runs (Nextflow/Snakemake artefacts). It is **not** a Synaptic Four product SKU.

It does **not** orchestrate Ferrum or Solum. Solum is **file ingest** (`helios solum-audit`). Ferrum WES artefacts: set metadata `ferrum_wes_outputs` / `wes_output_drs_ids` to `drs://…` ids so check **GA4GH-WES-DRS-001** can pass. Local file hashes alone are not a Ferrum join.

## Audience

Labs that want machine-verifiable pipeline evidence. Anyone — including non-customers.

**Not for:** running DRS/WES (Ferrum), issuing Passports (ga4gh-infra), clinical consent (Solum), a researcher UI (BRA).

## Standalone

```bash
pip install helios-audit
make prove   # from a clone: no Nextflow, no Ferrum
```

See [PROVE.md](PROVE.md) and [solum-ingest.md](solum-ingest.md).
