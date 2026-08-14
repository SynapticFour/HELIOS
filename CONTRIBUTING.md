# Contributing to HELIOS

Thank you for helping improve HELIOS.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quality Gates

Same as CI. Prefer:

```bash
make test    # ruff + mypy + pytest --cov=helios --cov-fail-under=80
```

Equivalent:

```bash
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/helios/
pytest tests/ -v --tb=short --cov=helios --cov-report=term-missing --cov-fail-under=80
```

`make lint` is ruff + mypy only. `make fmt` applies ruff `--fix` and format.

## Pull Requests

- Keep changes focused and include tests.
- Update docs when behavior changes. Operator-facing config/CLI belongs in [`docs/operator.md`](docs/operator.md); design choices in [`docs/decisions/`](docs/decisions/).
- Checks must stay fail-closed: unmeasurable inputs fail or skip, they never pass. See [ADR 0001](docs/decisions/0001-fail-closed-evidence.md).
- Signature verify must use the trust store, never an embedded PEM. See [ADR 0002](docs/decisions/0002-trust-store.md).
- Add changelog entries for user-visible changes.

## Code of Conduct

Contributors are expected to follow the [Contributor Covenant](https://www.contributor-covenant.org/).
