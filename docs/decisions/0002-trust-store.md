# ADR 0002 — Trust-store signatures

- Status: Accepted
- Date: 2026-08-15

## Context

`AuditRecord.signature.public_key_pem` let importers treat any self-signed Ed25519 envelope as valid. That is attestation by the record author, not by the lab.

## Decision

Verification loads `*.pub` from `trusted_keys_dir` (default `~/.helios/keys`). Embedded PEMs are informational. Import of a signed record whose fingerprint is not in the trust store is rejected. Missing signing keys are errors, not silent unsigned stores. `helios key generate` requires `HELIOS_KEY_PASSPHRASE` unless `--allow-unencrypted` is passed.

## Consequences

Third-party verify needs the lab's public key, not just the JSON file. Dashboard import of foreign signed records requires installing that lab's `.pub` first.
