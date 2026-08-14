# EU AI Act (Articles 10 & 11) Mapping

HELIOS is **not** an AI system under the AI Act. The optional `ai_act_art11_fragment` is a provenance stub for labs that already run high-risk genomics models **beside** HELIOS.

## What is emitted

- `risk_classification` is always `"unspecified"` unless you change the exporter. HELIOS will not label a pipeline high-risk.
- `data_governance.training_data_sources` / `validation_data_sources` / `data_quality_measures` are empty unless the operator puts values in pipeline parameters. HELIOS does not invent training-data lineage.
- `audit_trail_reference` points at the signed `AuditRecord` (run id, payload hash, signer fingerprint).

Do not attach this fragment to an AI Act dossier as if it were Article 10/11 documentation. It is a pointer to pipeline evidence, nothing more.
