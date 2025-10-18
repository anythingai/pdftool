# Full setup: install Poppler/Tesseract (via Scoop), ensure eng data, create venv, install project
$ErrorActionPreference = "Stop"

# Install external tools
& "$PSScriptRoot\..\tools\install_tools.ps1"

# Create venv and install Python deps
Write-Host "Creating virtual environment..."
python -m venv .venv
Write-Host "Upgrading pip/setuptools/wheel..."
.venv\Scripts\python -m pip install --upgrade pip setuptools wheel
Write-Host "Installing project (editable)..."
.venv\Scripts\pip install -e .

Write-Host "Setup complete. To start the server, run one of:\n  python scripts/start/start_app.py\n  scripts\start\start_app.ps1"
