#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3 || command -v python)"
fi

mkdir -p logs
LOG="logs/wizzair_afternoon.log"

{
  echo "=== $(date -Iseconds) wizzair afternoon delta run ==="
  "$PYTHON" -m wizzair send-delta "$@"
} >>"$LOG" 2>&1

echo "Afternoon run complete. See $LOG"
