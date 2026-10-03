# CI triggers

Push to `main` and pull requests run only the secret scan and dependency review. Product CI is manual. A `v*` tag publishes `helios-audit` to PyPI and the GHCR image.

Run `make verify-release` before tagging. That command is `make test` (ruff, format, mypy, pytest with the 80% coverage floor), `make prove` (the sign/tamper subset), and `pip-audit` against `requirements.lock` when `pip-audit` is installed.

Minutes below are rough runner time, not a measured bill.

| Workflow | Trigger | Rough minutes | When to run manually |
|---|---|---|---|
| `ci.yml` | `workflow_dispatch` | 8–15 | Before a tag, after `make verify-release`, when you want the same jobs on a GitHub runner (Python 3.11 and 3.12). |
| `codeql.yml` | `workflow_dispatch` | 8–15 | Before a release when you want a CodeQL pass. No weekly schedule. |
| `release.yml` | tag `v*` | 10–20 | The tag runs tests, then publishes the wheel and sdist to PyPI and attaches the SBOM files to the GitHub Release. |
| `docker-release.yml` | tag `v*`; `workflow_dispatch` | 8–15 | The tag publishes `ghcr.io/synapticfour/helios:<tag>` (linux/amd64). Dispatch to rebuild without a new tag. |
| `secret-scan.yml` | pull request; push to `main` or `master` | 1–2 | Leave it. It stays on those events. |
| `dependency-review.yml` | pull request | 1–2 | Leave it. It stays on pull requests. |
