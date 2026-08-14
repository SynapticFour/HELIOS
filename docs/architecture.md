# Architecture

HELIOS follows a modular architecture:

1. **CLI layer** (`helios.cli`) orchestrates user workflows and fail-closed exit codes.
2. **Core domain layer** (`helios.core`) defines audit records, trust-store Ed25519 verify, hashing, SQLite persistence.
3. **Integration layer** (`helios.integrations`) extracts context from Nextflow and Snakemake.
4. **Check layer** (`helios.checks`) runs assertions. Empty or unmeasurable inputs fail or skip — they never pass.
5. **Export layer** (`helios.export`) renders JSON, PDF, and RO-Crate outputs.
6. **Dashboard layer** (`helios.dashboard`) serves run/report APIs behind API-key auth (`HELIOS_DASHBOARD_API_KEY`).

## Design choices

- Frozen Pydantic models prevent in-process mutation of a record object. They are **not** an append-only ledger; SQLite can be deleted. Signatures + trust store are the integrity control.
- Ed25519 signatures. Verification uses `trusted_keys_dir` (`*.pub`), never the PEM embedded in the record.
- SQLite + SQLModel for local persistence (mode 0600 when the process can chmod).
- Streaming SHA-256 for large genomic assets.

See [ADR 0001](decisions/0001-fail-closed-evidence.md) and [ADR 0002](decisions/0002-trust-store.md).
