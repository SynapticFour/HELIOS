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
  --export-format json \
  --output-dir /var/lib/helios/reports

# Or:
make solum-clinical-evidence EXPORT=/tmp/pilot.solum-audit-helios-chain.json
```

Report lands under `--output-dir` when set, otherwise `export.output_dir` (default `helios-reports/`). `CLIN-ACCESS-001` is `pass` only when the hash chain verifies **and** at least one clinical-plane event is present. Format-only exports and broken chains fail; `helios solum-audit` then exits **1** and does not sign. Missing signing key is an error unless `--no-sign`.

`helios publish-report --reports-dir <reports> --dest <static-dir>` copies the newest report only when its signature verifies against the trust store and the file does not contain the dashboard API key. It does not open `/api/v1`. See [ADR 0003](decisions/0003-static-signed-report.md).

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
