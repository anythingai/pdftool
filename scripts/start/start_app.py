"""Start script for the FastAPI server.

Prefers the virtual environment's python interpreter if present, otherwise
falls back to the system python.
"""

import platform
from pathlib import Path
import subprocess
import sys

WORKDIR = Path(__file__).resolve().parent.parent.parent


def main() -> None:
    """Launch the application entrypoint using the preferred Python interpreter."""
    # Prefer venv python if available
    if platform.system() == "Windows":
        py = WORKDIR / ".venv" / "Scripts" / "python.exe"
    else:
        py = WORKDIR / ".venv" / "bin" / "python"

    python_cmd = str(py) if py.exists() else sys.executable
    subprocess.run([python_cmd, str(WORKDIR / "app.py")], check=True)


if __name__ == "__main__":
    main()
