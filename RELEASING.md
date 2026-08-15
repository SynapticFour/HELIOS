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
6. Release workflow runs tests, then emits CycloneDX SBOM + `requirements.lock` checksums. The JSON sidecar is unsigned provenance, not an in-toto attestation.

`v0.1.0` is tagged and published: https://pypi.org/project/helios-audit/0.1.0/ — `pip install helios-audit`.

## `v0.1.0` on PyPI

The GitHub Release **publish** job for the tag failed with `invalid-publisher` (no Trusted Publisher). The wheel and sdist were uploaded with a one-time API token. Do **not** retag `v0.1.0`.

For later tags, add a **Trusted Publisher** on the live project (not a pending publisher):

- Owner: `SynapticFour`
- Repository: `HELIOS`
- Workflow: `release.yml`
- Environment: **leave empty** (the workflow does not set `environment:`)

Then `git push origin vX.Y.Z` is enough. Do not put PyPI API tokens in the repo or in chat.

## Cut a later tag (operator steps)

Do **not** push a new `v*` tag until Trusted Publisher is confirmed (or you are prepared to upload with a short-lived token and revoke it).

```bash
# On a clean main that matches the intended release commit:
git checkout main
git pull
git status   # clean

# Annotated tag (triggers release.yml on push):
git tag -a vX.Y.Z -m "vX.Y.Z"

# Publish the tag (this starts PyPI publish — irreversible for that version):
git push origin vX.Y.Z
```

Then confirm the Release workflow, the PyPI project page, and `pip install helios-audit==X.Y.Z`.

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
