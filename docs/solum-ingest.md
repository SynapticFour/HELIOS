# Solum audit ingest → signed HELIOS report

**Status:** Productized recipe · 2026-08-12 · org plan **F5**
**Audience:** operators / Showcase pilots
**Honesty:** Solum does **not** embed HELIOS keys or call HELIOS internally. Export from Solum, ingest with HELIOS CLI.

---

## Prerequisites

- Solum audit store with events (sidecar `GET /v1/audit/export` or `solum-core audit export`)
- HELIOS installed (`pip install -e .` from this repo) with a signing key (`helios key generate` or path in `helios.toml`)

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

Report lands under `helios-reports/` (or `export.output_dir` in config). Check `CLIN-ACCESS-001` must be `pass` (not skipped) when the export is valid.

---

## What CLIN-ACCESS-001 does

- Validates `format == solum-audit-helios-chain-v1`
- Counts clinical-plane events (`consent.*`, `authorization.*`, `data.encrypt` / `data.decrypt`, `access.*`)
- Does **not** certify EHDS/GDPR compliance

---

## Showcase pilot path

When `SHOWCASE_ENABLE_SOLUM=1`, Showcase saves the pre-tamper audit export and runs this recipe after the Solum stage (see Showcase `run-golden-path.sh`). Fixtures mode packs a sample chain + HELIOS report including `CLIN-ACCESS-001`.

---

## Related

- Solum [helios.md](https://github.com/SynapticFour/Solum/blob/main/docs/helios.md)
- Check implementation: `src/helios/checks/clinical_access.py`
