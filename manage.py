#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import subprocess
import sys
import venv
from pathlib import Path


def devsetup(rebuild=False):
    """Set up an environment for local development."""
    this = Path(__file__).resolve(strict=True)
    venvdir = this.parent / ".venv"
    project_dir = this.parent

    def _run(*args):
        subprocess.check_call(args, cwd=str(project_dir))

    if rebuild:
        # Nuke the venv and recreate
        print("Rebuilding virtualenv")
        venv.create(str(venvdir), clear=True, with_pip=True, prompt="commoncontent")
    elif not venvdir.exists():
        print("Creating virtualenv")
        venv.create(str(venvdir), with_pip=True, prompt="commoncontent")

    python = venvdir / "bin" / "python"
    activate = f"source {venvdir}/bin/activate"
    if sys.platform == "win32":
        python = venvdir / "Scripts" / "python.exe"
        activate = (
            f"{venvdir}\\Scripts\\Activate.ps1 or {venvdir}\\Scripts\\activate.bat"
        )

    # Upgrade pip in virtualenv. Need pip >= 22.1 for -e with pyproject.toml
    # 3.8's pip won't cut it.
    print("Upgrading virtualenv to latest pip")
    _run(python, "-m", "pip", "install", "-q", "--upgrade", "pip", "wheel")

    # Run pip install -e .[dev]
    #   - Installs requirements from pyproject.toml, not requirements.txt
    print("Installing requirements. May take a bit. Grab a coffee.")
    _run(python, "-m", "pip", "install", "-e", ".[dev]")

    # If no .env, copy example.env to .env
    # dotenv = project_dir / ".env"
    # if not dotenv.exists():
    #     shutil.copy(project_dir.joinpath("example.env"), dotenv)

    # Create the dev database
    print("Applying database migrations")
    _run(python, "manage.py", "migrate")

    print(f"Now activate your virtualenv using: {activate}")


def django_command(args=None):
    """Run administrative tasks."""
    if args is None:
        args = sys.argv
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?\n\n"
            "To bootstrap a virtualenv, run: python manage.py devsetup"
        ) from exc
    execute_from_command_line(args)


if __name__ == "__main__":
    if sys.argv[1] == "devsetup":
        rebuild = False
        if len(sys.argv) > 2 and sys.argv[2] in ["--rebuild", "-r"]:
            rebuild = True
        devsetup(rebuild=rebuild)
    else:
        django_command()
