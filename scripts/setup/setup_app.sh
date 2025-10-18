#!/usr/bin/env bash
set -euo pipefail

# Install external tools
"$(dirname "$0")"/../tools/install_tools.sh

# Create venv and install Python deps
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e .

echo "Setup complete. To start the server, run one of:\n  python scripts/start/start_app.py\n  scripts/start/start_app.sh"
