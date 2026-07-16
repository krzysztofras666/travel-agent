#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3 || command -v python)"
fi

mkdir -p logs
LOG="logs/travel_run.log"

{
  echo "=== $(date -Iseconds) travel_agent daily run ==="
  "$PYTHON" -m travel_agent send "$@"
} >>"$LOG" 2>&1

echo "Run complete. See $LOG"
