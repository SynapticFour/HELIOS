# HELIOS maturity — Alpha → Beta exit (K1)

**Status:** Alpha (do not market as release-frozen)
**Org plan:** Workstream K1 · Strategic roadmap Phase 1
**Related:** [RELEASING.md](../RELEASING.md) · [solum-ingest.md](solum-ingest.md) · Showcase Evidence Pack

HELIOS is the **shared signed evidence surface** for the commercial spine. It is not a certification product.

---

## Remain Alpha until all of the following are true

| # | Exit item | Status |
|---|-----------|--------|
| 1 | Solum audit ingest → signed report documented + CI/fixture covered | **Done** (F5/F6) |
| 2 | Evidence Pack field → auditor/ethics question map published (non-cert) | See Showcase `docs/for-customers/evidence-pack-auditor-map.md` |
| 3 | Threat model + IR runbook current | **Done** |
| 4 | SBOM / lockfile on release path | **Partial** — CycloneDX SBOM + `requirements.lock` checksums. The JSON “attestation” is unsigned provenance, not in-toto. |
| 5 | `v0.1.0` tagged **and** published to PyPI | **Done** — 0.1.0 and **0.1.1**. https://pypi.org/project/helios-audit/ |
| 6 | README Status badge flipped Alpha → Beta only after 1–5 | **Blocked on 5** |

## Explicitly not required for Beta

- Formal ISO/EHDS certification language
- Managed SaaS dashboard as default
- Replacing customer QMS sign-off

## When Beta is declared

Update README badge, website HELIOS copy if needed, and [`RELEASE-FROZEN-SCORECARD.md`](https://github.com/SynapticFour/synapticfour-business/blob/main/strategy/org-level-up/RELEASE-FROZEN-SCORECARD.md).
