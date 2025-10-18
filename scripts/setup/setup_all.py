"""Cross-platform unified setup script.

Installs required system tools, creates/uses a local virtual environment,
and installs project dependencies via editable install.
"""

import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

WORKDIR = Path(__file__).resolve().parent.parent.parent


def run(
    cmd: list[str],
    check: bool = True,
    shell: bool = False,
) -> subprocess.CompletedProcess[Any]:
    """Run a command and return the CompletedProcess.

    Args:
        cmd: Command as a list of arguments.
        check: If True, raise on non-zero exit code.
        shell: If True, run via shell.
    """
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=check, shell=shell)


def install_tools() -> None:
    """Install platform-specific system tools if needed.

    Delegates to PowerShell on Windows and bash script on macOS/Linux.
    """
    system = platform.system()
    tools_dir = WORKDIR / "scripts" / "tools"
    if system == "Windows":
        ps_script = tools_dir / "install_tools.ps1"
        run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)])
    elif system in ("Darwin", "Linux"):
        sh_script = tools_dir / "install_tools.sh"
        run(["bash", str(sh_script)])
    else:
        print(f"Unsupported OS: {system}")
        sys.exit(1)


def create_venv() -> None:
    """Create or reuse the local virtual environment and install project deps."""
    venv_dir = WORKDIR / ".venv"
    exists = venv_dir.exists()
    if exists:
        print("Using existing virtual environment at", venv_dir)
    else:
        run([sys.executable, "-m", "venv", str(venv_dir)])

    if platform.system() == "Windows":
        py = venv_dir / "Scripts" / "python.exe"
    else:
        py = venv_dir / "bin" / "python"

    # Upgrade pip/setuptools/wheel and install project (editable)
    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    run([str(py), "-m", "pip", "install", "-e", str(WORKDIR)])


def main() -> None:
    """Run full setup sequence: tools, venv, dependencies."""
    install_tools()
    create_venv()
    print("Setup complete. To start the server, run:\n  python scripts/start/start_app.py")


if __name__ == "__main__":
    main()
