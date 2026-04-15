# Architecture

HELIOS follows a modular architecture:

1. **CLI layer** (`helios.cli`) orchestrates user workflows.
2. **Core domain layer** (`helios.core`) defines immutable audit records, signing, hashing, and persistence.
3. **Integration layer** (`helios.integrations`) extracts context from Nextflow and Snakemake.
4. **Check layer** (`helios.checks`) runs compliance assertions against run artifacts.
5. **Export layer** (`helios.export`) renders JSON, PDF, and RO-Crate outputs.
6. **Dashboard layer** (`helios.dashboard`) serves run/report APIs.

## Design choices

- Immutable Pydantic models for tamper-resistant audit evidence.
- Ed25519 signatures for compact, strong cryptographic integrity.
- SQLite + SQLModel for low-ops local persistence and queryability.
- Streaming hashing for large genomic assets.

