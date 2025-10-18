$ErrorActionPreference = "Stop"

$venvPy = Join-Path (Join-Path $PSScriptRoot "..\..") ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
  & $venvPy "app.py"
} else {
  python "app.py"
}
