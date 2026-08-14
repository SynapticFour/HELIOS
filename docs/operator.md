# Operator reference

How to run HELIOS so the output is actually evidence: fail-closed checks, a trust store, and non-zero exits on failure. Architecture: [architecture.md](architecture.md). Decisions: [0001](decisions/0001-fail-closed-evidence.md), [0002](decisions/0002-trust-store.md).

HELIOS is **not** a certification.

---

## Signing keys

```bash
export HELIOS_KEY_PASSPHRASE='use a real secret'
helios key generate
```

- Private key: `~/.helios/keys/helios.key` (mode `0600`, directory `0700`)
- Public key: `~/.helios/keys/helios.pub` — this is the trust-store entry
- Without a passphrase, generation refuses unless you pass `--allow-unencrypted` (throwaway/dev only)

Verification **never** trusts the PEM embedded in a report. It loads `*.pub` from `trusted_keys_dir` (default `~/.helios/keys`, overridable with `HELIOS_KEY_DIR`). To accept another lab’s signed JSON, install their `.pub` into that directory first.

`helios run` signs by default. Missing key → exit 1. `--no-sign` is explicit and still fails the process if checks fail.

`helios config print` redacts API keys.

---

## Environment variables

| Variable | Purpose |
|---|---|
| `HELIOS_KEY_PASSPHRASE` | Encrypts/decrypts the Ed25519 private key |
| `HELIOS_KEY_DIR` | Directory for key generate + default trust store (`*.pub`) |
| `HELIOS_DASHBOARD_API_KEY` | Required for `helios serve` / `make up` |
| `HELIOS_DASHBOARD__API_KEY` | Nested alias (prefer the name above) |
| `HELIOS_*` | Any setting in `helios.toml` (nested with `__`, e.g. `HELIOS_CHECKS__CONTAINER_DIGEST_REQUIRED=false`) |

---

## `helios.toml`

`helios init` copies [helios.toml.example](../helios.toml.example). Empty `checks.enabled` is an error — name the checks to run.

| Key | Default | Notes |
|---|---|---|
| `signing_key` | `~/.helios/keys/helios.key` | Required unless `--no-sign` |
| `trusted_keys_dir` | `~/.helios/keys` | `*.pub` trust store |
| `audit_db` | `~/.helios/helios.db` | SQLite; parent `0700`, file `0600` when chmod works |
| `command_timeout_seconds` | `86400` | Wrapped pipeline timeout (exit 124) |
| `checks.enabled` | reference, container, MANE, VUS, crypt4gh | Must be non-empty |
| `checks.container_digest_required` | `true` | Tag without `@sha256:` fails |
| `checks.vus_warn_threshold` / `vus_fail_threshold` | `0.40` / `0.70` | Fraction, not percent |
| `export.include_rocrate` | `false` | Also emit RO-Crate beside JSON/PDF |
| `export.ai_act_fragment` | `false` | Opt-in provenance stub, not Art. 10/11 docs |
| `dashboard.allow_delete` | `false` | |
| `dashboard.max_import_bytes` | `10485760` | Import body limit |

---

## Checks (fail-closed)

If a check cannot prove the named property, it **fails or skips**. Skip is excluded from the score. Nothing scored → grade `N/A`, score `null`, never 100.

| ID | Passes only when |
|---|---|
| `SEC-CONTAINER-001` | At least one container ref, all digest-pinned (default) |
| `GA4GH-CRYPT-001` | Genomic outputs start with Crypt4GH magic bytes (suffix ignored) |
| `CLIN-VUS-001` | Classified variants exist; rate below thresholds. No data → skip |
| `GA4GH-REF-001` | BAM/CRAM `@SQ` UR/M5 matches known GRCh38 MD5s. No artifact → fail |
| `GA4GH-MANE-001` | VCF transcript IDs vs cached NCBI MANE list |
| `CLIN-ACCESS-001` | Solum `solum-audit-helios-chain-v1` hash chain verifies **and** ≥1 clinical-plane event |

`helios run` and `helios validate` exit **1** if any enabled check fails. Failed wrapped Nextflow/Snakemake commands are **not** signed.

---

## CLI

| Command | Behavior |
|---|---|
| `helios run` | Wrap optional command, audit, sign, export. Exit 1 on check fail |
| `helios validate <run-id>` | Verify signature against the trust store, re-run checks on stored paths. Exit 1 on bad sig or check fail |
| `helios key generate` | Requires passphrase or `--allow-unencrypted` |
| `helios config print` | Effective config with secrets redacted |
| `helios solum-audit --export …` | CLIN-ACCESS-001 + sign; exit 1 on check fail |
| `helios snakemake-wrap -- …` | Audits **only** if Snakemake exits 0 |
| `helios serve` | Requires `HELIOS_DASHBOARD_API_KEY`. Compose publishes `127.0.0.1:8765` |

---

## Dashboard

- Auth: `X-API-Key`, `Authorization: Bearer`, or HTTP Basic password
- Browser prompts for the key and keeps it **in memory** (not `sessionStorage`)
- No CDN scripts or webfonts
- Signed import must match the trust store; unsigned import needs `allow_unsigned=true`

---

## Local quality gates

```bash
make test    # ruff + mypy + pytest --cov=helios --cov-fail-under=80
```

`requirements.lock` is the last frozen install used for release checksums. CI installs from `pyproject.toml` extras.
