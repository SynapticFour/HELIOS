# HELIOS — Threat Model

**Status:** Living · Alpha product
**Version:** 1.0 · 2026-08-12
**Audience:** Security reviewers, lab quality / IT
**Related:** [README.md](../README.md) · [architecture.md](architecture.md) · [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) (when present)

HELIOS produces **technical audit evidence** for genomics pipelines. It is **not** certification, accreditation, legal determination, or regulatory approval.

---

## 1. Assets

| Asset | Sensitivity | Notes |
|-------|-------------|-------|
| Pipeline run context (inputs, digests, versions) | Medium–High | May include paths or sample IDs |
| Check results / evidence reports | High | Integrity is the product value |
| Signing keys for reports | Critical | Compromise → forged “evidence” |
| Ingested Solum audit exports | High | Clinical access trails |
| Operator config / CI secrets | High | |

---

## 2. Trust boundaries

```text
  Pipeline / lab systems          Solum audit export (optional)
           │                                │
           └────────────┬───────────────────┘
                        ▼
                 HELIOS checks + report
                        │
                        ▼
              Signed evidence artefact
                        │
                        ▼
         Auditor / partner / Showcase pack
```

HELIOS typically runs **inside the operator’s trust domain**. Synaptic Four does not sign customer production reports by default.

---

## 3. Adversaries (in scope)

| Adversary | Goal | Posture |
|-----------|------|---------|
| Report forger | Fake pass evidence | Signing keys; document verification steps |
| Tamper with inputs after the fact | Change what was checked | Capture immutable run context at check time |
| Malicious dependency in HELIOS install | RCE on operator host | Pin releases; SBOM/attestation (level-up C6) |
| Confused deputy (CI) | Leak secrets into reports | Redact; avoid dumping env |

### Out of scope

| Non-goal | Meaning |
|----------|---------|
| Proving a lab is ISO 15189 / IVDR / AI Act compliant | Orientation docs only |
| Protecting data inside Ferrum/Solum runtimes | Those products’ threat models |
| Guaranteeing third parties accept HELIOS packs | Buyer/auditor decision |
| Live signing as a Solum product feature | Export shapes exist; productized bridge is level-up F5 |

---

## 4. STRIDE summary

| STRIDE | Mitigations | Residual |
|--------|-------------|----------|
| Spoofing | Signed reports when keys configured | Unsigned Alpha demos |
| Tampering | Digests of inputs; signed output | Weak if signing skipped |
| Repudiation | Report metadata + timestamps | Operator clock trust |
| Info disclosure | Minimize PII in reports | Sample IDs in paths |
| DoS | Local tool | N/A |
| Elevation | Normal user-level install | Host compromise |

---

## 5. Pilot guidance

1. Treat Alpha reports as **engineering evidence**, not certificates.
2. Protect signing keys like production secrets.
3. Prefer pinned HELIOS version in Showcase `PINNED_VERSIONS.txt`.
4. When ingesting Solum chains, verify export schema version.

---

## 6. Maintenance

Update when signing, Solum ingest, or clinical check sets change.
