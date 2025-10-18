#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
VENVPY="$ROOT_DIR/.venv/bin/python"

if [ -x "$VENVPY" ]; then
  "$VENVPY" "$ROOT_DIR/app.py"
else
  python3 "$ROOT_DIR/app.py"
fi
