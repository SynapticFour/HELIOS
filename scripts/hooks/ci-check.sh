#!/usr/bin/env bash
# Mirror .github/workflows/ci.yml
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/ruff || ! -x .venv/bin/mypy || ! -x .venv/bin/pytest ]]; then
  echo "HELIOS ci-check: create .venv first:" >&2
  echo "  python3 -m venv .venv && .venv/bin/pip install -e \".[dev]\"" >&2
  exit 1
fi

echo "ci-check: ruff"
.venv/bin/ruff check src/ tests/
.venv/bin/ruff format --check src/ tests/

echo "ci-check: mypy"
.venv/bin/mypy src/helios/

echo "ci-check: pytest"
.venv/bin/pytest tests/ -q

echo "ci-check: OK"
