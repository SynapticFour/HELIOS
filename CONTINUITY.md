# CONTINUITY — HELIOS (`helios-audit`)

Survivability notes. **True on `origin/main` today.** Not legal advice. Not certification.

Checked on 2026-10-14. Release tags: `git tag` (do not copy a tag or commit SHA into this file). This repository has no `VERSIONS.lock`. Package version: `pyproject.toml`. PyPI `helios-audit` **0.1.2** is the version recorded by the 2026-10 registry query and matches git tag `v0.1.2`. `main` can be ahead of that tag.

## What this project is

Genomics pipeline **audit evidence** framework: signed audit trails, checks, exports (JSON / PDF / RO-Crate per product docs). Reads export JSON from disk; does **not** call Ferrum/Helix APIs or orchestrate them. License: **Apache-2.0**. Maturity on this branch: **Early use** (registry HELIOS-MATURITY-001). The claim's plain text still says early access. Until this branch is merged, `origin/main` still says Early access / Alpha. Console script: `helios`. Import package: `helios`.

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
git tag -l 'v*'
git checkout <tag>     # tag v0.1.2 matches the recorded PyPI 0.1.2; main may be ahead
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

HELIOS is maintained by a single steward (Synaptic Four). To reduce dependence on any one person, the build is documented from a clean machine in this file, the release steps are written down, and the source can be inspected and built without access to Synaptic Four systems (clean-room check dated 2026-10; Python ≥ 3.11 and network access to PyPI for a first install). Operational details such as accounts, publication rights and escrow arrangements are being documented in a non-public continuity plan.

## Minimal operator runbook

| Action | Command |
|--------|---------|
| Install (PyPI pin recorded 2026-10) | `pip install helios-audit==0.1.2` **or** clone the `v0.1.2` tag → venv → `make install` |
| Install (from main) | Clone → Python 3.11 venv → `make install` (version is `pyproject.toml`; it can be ahead of the tag) |
| Prove | `make prove` |
| Start dashboard | set `HELIOS_DASHBOARD_API_KEY` → `make up` |
| Stop | `make down` |
| Wipe | `make destroy` |
| Back up | Export evidence outputs / DB volume used by Compose; keep signing keys offline |
| Restore | Restore volumes + keys → `make up` |
| Upgrade | Newer tag or PyPI version; re-run `make test` / `make prove` |
