# Releasing `helios-audit`

**Status: Alpha.** HELIOS produces technical audit evidence. A PyPI release is not a certification, accreditation, or regulatory approval.

Package metadata (must stay aligned):

| Field | Value |
|---|---|
| PyPI / project name | `helios-audit` (`pyproject.toml` `[project].name`) |
| Import package | `helios` |
| Console script | `helios` |
| Current version | `0.1.0` (`pyproject.toml` and `helios.__version__`) |
| Python | `>=3.11` |
| Build backend | `hatchling` |
| Publish workflow | [`.github/workflows/release.yml`](.github/workflows/release.yml) on tag `v*` |

## Preconditions before cutting `v0.1.0`

1. CI green on `main` ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
2. `CHANGELOG.md` has a closed `[0.1.0]` section that matches the tag.
3. Version strings match: `pyproject.toml` `version = "0.1.0"` and `src/helios/__init__.py` `__version__ = "0.1.0"`.
4. **PyPI Trusted Publisher** is configured for this GitHub repository and the `helios-audit` project (OIDC via `pypa/gh-action-pypi-publish` with `id-token: write`). Do **not** push a release tag until that is verified in the PyPI project settings — otherwise the workflow will build but fail to publish.
5. Optional smoke: locally `python -m build` and confirm `dist/helios_audit-0.1.0-*.whl` / `.tar.gz`.

Until `v0.1.0` is tagged **and** published, operators install from source (see [README.md](README.md)).

## Cut `v0.1.0` (operator steps)

Do **not** run these until Trusted Publisher is confirmed.

```bash
# On a clean main that matches the intended release commit:
git checkout main
git pull
git status   # clean

# Annotated tag (triggers release.yml on push):
git tag -a v0.1.0 -m "v0.1.0"

# Publish the tag (this starts PyPI publish — irreversible for that version):
git push origin v0.1.0
```

Then:

1. Confirm the **Release** workflow succeeded on GitHub Actions.
2. Confirm `https://pypi.org/project/helios-audit/0.1.0/` is live.
3. Smoke-test: `pip install helios-audit==0.1.0 && helios --help`.
4. Update README install section if it still says “install from source only”.

## Subsequent releases

1. Bump `version` in `pyproject.toml` and `__version__` in `src/helios/__init__.py`.
2. Update `CHANGELOG.md`.
3. Tag `vX.Y.Z` and `git push origin vX.Y.Z`.

## Versioning rules

- `MAJOR`: breaking API/behavior changes
- `MINOR`: backward-compatible features
- `PATCH`: backward-compatible fixes and maintenance

## Dashboard auth reminder

Released dashboard builds still require `HELIOS_DASHBOARD_API_KEY` for `/api/v1/*`. See README and `.env.example`.
