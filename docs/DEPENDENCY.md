# Dependency care (ambassador)

Dependabot and Renovate are **off by choice**. Pin care is:

- `requirements.lock` / `pyproject.toml` bounds reviewed in PRs
- GitHub **Dependency Review** on pull requests (`.github/workflows/dependency-review.yml`)
- No automated version PRs that a visitor would mistake for a product SLA

Bump Python deps when a CVE lands or when cutting a PyPI tag. Record the bump in `CHANGELOG.md`.
