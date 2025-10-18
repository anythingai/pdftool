"""
Bootstrap script to set up dependencies and start the server.
This script runs the unified setup and then launches the FastAPI app.
"""

import subprocess
import sys
from pathlib import Path

WORKDIR = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    """Run a shell command, echoing it first.

    Raises a CalledProcessError if the command exits with a non-zero status.
    """
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    """Execute setup and then start the application."""
    # Run unified setup (installs tools, creates venv, installs deps)
    run([sys.executable, str(WORKDIR / "scripts" / "setup" / "setup_all.py")])
    # Start the server (prefers venv python if present)
    run([sys.executable, str(WORKDIR / "scripts" / "start" / "start_app.py")])


if __name__ == "__main__":
    main()
