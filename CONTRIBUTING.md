# Contributing to HELIOS

Thank you for helping improve HELIOS.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quality Gates

```bash
ruff check .
mypy src
pytest
```

## Pull Requests

- Keep changes focused and include tests.
- Update docs when behavior changes.
- Add changelog entries for user-visible changes.

## Code of Conduct

Contributors are expected to follow the [Contributor Covenant](https://www.contributor-covenant.org/).

