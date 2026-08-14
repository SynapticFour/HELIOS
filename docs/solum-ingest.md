# Solum audit ingest → signed HELIOS report

**Status:** Productized recipe · 2026-08-12 · org plan **F5**
**Audience:** operators / Showcase pilots
**Honesty:** Solum does **not** embed HELIOS keys or call HELIOS internally. Export from Solum, ingest with HELIOS CLI.

---

## Prerequisites

- Solum audit store with events (sidecar `GET /v1/audit/export` or `solum-core audit export`)
- HELIOS installed (`pip install -e .` from this repo) with a signing key (`export HELIOS_KEY_PASSPHRASE=... && helios key generate`, or `--allow-unencrypted` for throwaway keys)
- The matching `helios.pub` must sit in `trusted_keys_dir` (default `~/.helios/keys`) for later `helios validate` / dashboard import

Export format required: **`solum-audit-helios-chain-v1`**.

---

## Recipe

```bash
# 1) Export from Solum (sidecar)
curl -sS -H "Authorization: Bearer $SOLUM_TOKEN" \
  "$SOLUM/v1/audit/export" > /tmp/pilot.solum-audit-helios-chain.json

# Or CLI:
# cargo run -p solum-core -- audit export --audit "$AUDIT" --out /tmp/pilot.solum-audit-helios-chain.json

# 2) Ingest + CLIN-ACCESS-001 + sign
helios solum-audit \
  --export /tmp/pilot.solum-audit-helios-chain.json \
  --config helios.toml \
  --export-format json

# Or:
make solum-clinical-evidence EXPORT=/tmp/pilot.solum-audit-helios-chain.json
```

Report lands under `helios-reports/` (or `export.output_dir` in config). `CLIN-ACCESS-001` is `pass` only when the hash chain verifies **and** at least one clinical-plane event is present. Format-only exports and broken chains fail; `helios solum-audit` then exits **1** and does not sign. Missing signing key is an error unless `--no-sign`.

---

## What CLIN-ACCESS-001 does

- Validates `format == solum-audit-helios-chain-v1`
- Verifies `seq` / `prev_hash` / `hash` (SHA-256 over `seq BE || prev_hash || compact event JSON`)
- Counts clinical-plane events (`consent.*`, `authorization.*`, `data.encrypt` / `data.decrypt`, `access.*`)
- Does **not** certify EHDS/GDPR compliance

---

## Showcase pilot path

When `SHOWCASE_ENABLE_SOLUM=1`, Showcase saves the pre-tamper audit export and runs this recipe after the Solum stage (see Showcase `run-golden-path.sh`). Fixtures mode packs a sample chain + HELIOS report including `CLIN-ACCESS-001`.

---

## Related

- Operator reference: [operator.md](operator.md)
- Solum [helios.md](https://github.com/SynapticFour/Solum/blob/main/docs/helios.md)
- Check implementation: `src/helios/checks/clinical_access.py`
