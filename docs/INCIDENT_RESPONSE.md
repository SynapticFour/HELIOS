# HELIOS — Incident Response Runbook

**Status:** Living · 2026-08-12 · Alpha
**Audience:** Operators using HELIOS for evidence
**Company plan:** Synaptic Four business IR (private)
**Threat model:** [THREAT_MODEL.md](THREAT_MODEL.md)

---

## 1. What counts as an incident

- HELIOS signing private key exposure or loss
- Evidence report forged / altered after signing
- HELIOS host compromise while processing Solum audit exports or pipeline metadata
- Accidental inclusion of unexpected personal data in published reports

---

## 2. Severity

| Level | Examples |
|-------|----------|
| Critical | Signing key theft with reports already distributed as authoritative |
| High | Tampered unsigned reports relied upon in a pilot pack |
| Medium | Dependency vuln in HELIOS install; contained |
| Low | Doc/process gap |

---

## 3. Immediate actions

1. Stop using the compromised signing key; take key material offline.
2. Inventory reports signed with that key (Showcase packs, shared PDFs).
3. Notify relying parties that prior signatures may be untrusted.
4. Preserve HELIOS logs and input digests for investigation.
5. Contact `contact@synapticfour.com` if under support.

---

## 4. Recovery

- Generate new signing keys (`HELIOS_KEY_PASSPHRASE` required unless `--allow-unencrypted`); store the private key in the operator secret manager
- Install the new `helios.pub` into `trusted_keys_dir` on every host that verifies reports; remove the compromised `.pub`
- Re-run checks on retained inputs; re-sign with new keys (`helios run` / `helios solum-audit`)
- Tell relying parties which fingerprints are retired and which `.pub` to install
- Update pin in Showcase / pilot docs
- Do **not** claim certificates — re-issue engineering evidence only

---

## 5. Post-incident

Document which external parties received tainted reports. Update threat model residual risks. Consider moving up SBOM/attestation work (org level-up C6).
