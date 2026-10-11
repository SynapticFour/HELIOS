# CONTINUITY — HELIOS (`helios-audit`)

Survivability notes. **True on `origin/main` today.** Not legal advice. Not certification.

**Audited revision:** `origin/main` @ `4932aaf367691ca589348c63beb6008f18d97ca0`. Latest tag on origin: `v0.1.2` (commit `eda6417555052598650e0bafd3c230cd7b69f198`, differs from this main tip). Package version on main (`pyproject.toml`): `0.1.2`.

## What this project is

Genomics pipeline **audit evidence** framework: signed audit trails, checks, exports (JSON / PDF / RO-Crate per product docs). Reads export JSON from disk; does **not** call Ferrum/Helix APIs or orchestrate them. License: **Apache-2.0**. Maturity: Early access / Alpha. Console script: `helios`. Import package: `helios`.

## Build from a clean machine (from a given tag)

### Prerequisites

- Git, `make` (install `make` on bare Python container images)
- **Python ≥ 3.11** (3.9 is insufficient — `make install` / package metadata require 3.11+)
- `pip` / venv
- Network to PyPI for dependencies (or use `requirements.lock` as the project documents)
- For wheels: `pip install build` (or `python -m build` after installing the `build` package) — not pulled in by `make install` alone
- Optional dashboard: Docker Compose; env name **`HELIOS_DASHBOARD_API_KEY`** (value operator-chosen; see `.env.example` — do not commit values)

### Source

```bash
git clone https://github.com/SynapticFour/HELIOS.git
cd HELIOS
git checkout v0.1.1    # matches published PyPI 0.1.1
# Or for current main (may be 0.1.2 unpublished):
# git checkout main
python3.11 -m venv .venv
. .venv/bin/activate
pip install -U pip
make install           # pip install -e ".[dev]"
make prove             # integrity proof subset (no Nextflow)
# Fuller CI-parity:
make test              # ruff + mypy + pytest with coverage gate
```

Wheel/sdist smoke: `python -m build` (see `RELEASING.md`).

### Dashboard (optional)

```bash
# set HELIOS_DASHBOARD_API_KEY in environment or .env (never commit secrets)
make up                # docker compose up -d --build
make down
make destroy
```

UI: `http://127.0.0.1:8765/static/index.html` per README.

## How to run tests

| Command | Meaning |
|---------|---------|
| `make prove` | Sign/tamper integrity subset (no pipeline) |
| `make test` | lint + pytest + coverage ≥ 80% |
| `make verify-release` | `./scripts/verify-release.sh` before a `v*` tag |

## How to cut a release

Per `RELEASING.md`:

1. Align `pyproject.toml` version and `src/helios/__init__.py` `__version__`.
2. Update `CHANGELOG.md`.
3. `make verify-release`.
4. Confirm **PyPI Trusted Publisher** for owner `SynapticFour`, repo `HELIOS`, workflow `release.yml` (environment empty) — or be prepared for a one-time token upload (as happened for `v0.1.0` when Trusted Publisher was missing).
5. Annotated tag `vX.Y.Z` → `git push origin vX.Y.Z`.
6. Confirm Release workflow, PyPI page, and `pip install helios-audit==X.Y.Z`.
7. GHCR image: `docker-release.yml` → `ghcr.io/<owner>/helios:<version>`.

## Continuity

HELIOS is maintained by a single steward (Synaptic Four). To reduce dependence on any one person, the build is documented from a clean machine in this file, the release steps are written down, and the source can be inspected and built without access to Synaptic Four systems (clean-room check dated 2026-10; Python ≥ 3.11 and network access to PyPI for a first install). Operational details such as accounts, publication rights and escrow arrangements are kept in a non-public continuity plan. If you depend on HELIOS in production, ask for it.

## Minimal operator runbook

| Action | Command |
|--------|---------|
| Install (from tag matching PyPI) | `pip install helios-audit==0.1.1` **or** clone `v0.1.1` → venv → `make install` |
| Install (from main) | Clone → Python 3.11 venv → `make install` (expect 0.1.2 on audited HEAD) |
| Prove | `make prove` |
| Start dashboard | set `HELIOS_DASHBOARD_API_KEY` → `make up` |
| Stop | `make down` |
| Wipe | `make destroy` |
| Back up | Export evidence outputs / DB volume used by Compose; keep signing keys offline |
| Restore | Restore volumes + keys → `make up` |
| Upgrade | Newer tag or PyPI version; re-run `make test` / `make prove` |
