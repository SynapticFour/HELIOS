#!/usr/bin/env bash
# Prove HELIOS integrity without a genomics pipeline:
# 1. Sign a valid Solum audit-chain fixture
# 2. Tamper the chain → solum-audit must exit non-zero
#
# Throwaway keys stay in a temp directory. Not a certification.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v helios >/dev/null 2>&1; then
  echo "helios CLI not on PATH. Run: pip install -e '.[dev]'" >&2
  exit 1
fi

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/helios-prove.XXXXXX")"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

export HELIOS_KEY_DIR="$WORKDIR/keys"
export HELIOS_KEY_PASSPHRASE="helios-prove-throwaway"
mkdir -p "$HELIOS_KEY_DIR"

helios key generate >/dev/null

python3 - "$WORKDIR/chain.json" <<'PY'
import json, sys
from pathlib import Path

from helios.checks.clinical_access import SOLUM_GENESIS_HASH, solum_record_hash

events = [
    {"event_type": "consent.granted", "actor": "practitioner/1", "outcome": "success"},
    {"event_type": "authorization.denied", "actor": "attacker", "outcome": "denied"},
    {"event_type": "data.encrypt", "actor": "practitioner/1", "outcome": "success"},
]
records = []
prev = SOLUM_GENESIS_HASH
for index, event in enumerate(events, start=1):
    digest = solum_record_hash(index, prev, event)
    records.append({"seq": index, "event": event, "prev_hash": prev, "hash": digest})
    prev = digest
Path(sys.argv[1]).write_text(
    json.dumps(
        {
            "format": "solum-audit-helios-chain-v1",
            "generator": "helios-prove",
            "record_count": len(records),
            "records": records,
        }
    ),
    encoding="utf-8",
)
PY

CFG="$WORKDIR/helios.toml"
cat > "$CFG" <<EOF
[helios]
signing_key = "$HELIOS_KEY_DIR/helios.key"
trusted_keys_dir = "$HELIOS_KEY_DIR"
audit_db = "$WORKDIR/helios.db"
cache_dir = "$WORKDIR/cache"
log_level = "WARNING"

[helios.checks]
enabled = ["CLIN-ACCESS-001"]

[helios.export]
default_format = "json"
output_dir = "$WORKDIR/reports"
EOF

echo "[prove] signing a valid Solum audit chain…"
helios solum-audit --export "$WORKDIR/chain.json" --config "$CFG"

echo "[prove] tampering the chain (must fail)…"
python3 - "$WORKDIR/chain.json" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
data = json.loads(p.read_text(encoding="utf-8"))
data["records"][0]["hash"] = "0" * 64
p.write_text(json.dumps(data), encoding="utf-8")
PY

set +e
helios solum-audit --export "$WORKDIR/chain.json" --config "$CFG"
status=$?
set -e
if [[ "$status" -eq 0 ]]; then
  echo "[prove] FAIL: tampered chain was accepted" >&2
  exit 1
fi

echo "[prove] OK — valid chain signed; tamper rejected (exit $status)."
