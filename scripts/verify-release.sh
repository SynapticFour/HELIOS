#!/usr/bin/env bash
# Local gate before a v* tag.
# make test is ruff, format, mypy, and pytest with the coverage floor.
# make prove is the sign/tamper subset. CodeQL stays workflow_dispatch
# (see docs/CI.md).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  export PATH="$ROOT/.venv/bin:$PATH"
fi

echo "verify-release: make test"
make test

echo "verify-release: make prove"
make prove

if command -v pip-audit >/dev/null 2>&1; then
  echo "verify-release: pip-audit"
  pip-audit -r requirements.lock
else
  echo "verify-release: pip-audit not installed; skipped (pip install pip-audit)"
fi

echo "verify-release: OK"
