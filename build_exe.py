from __future__ import annotations

import argparse
import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(command: list[str]) -> None:
    print(">", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def build_python(build_venv: Path) -> Path:
    return build_venv / "Scripts" / "python.exe"


def main() -> None:
    parser = argparse.ArgumentParser(description="Construit Dofus Window Manager avec PyInstaller.")
    parser.add_argument(
        "--with-popup",
        action="store_true",
        help="inclut la détection visuelle des invitations Dofus Retro",
    )
    args = parser.parse_args()

    if sys.platform != "win32":
        raise SystemExit("Le binaire Windows doit être construit depuis Windows.")

    variant = "popup" if args.with_popup else "core"
    build_venv = ROOT / f".venv-build-{variant}"
    python_path = build_python(build_venv)
    if not python_path.exists():
        print(f"Création de l'environnement de build : {build_venv}")
        venv.EnvBuilder(with_pip=True, clear=False).create(build_venv)

    python = str(python_path)
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    run([python, "-m", "pip", "install", "-r", "requirements.txt"])
    if args.with_popup:
        run([python, "-m", "pip", "install", "-r", "requirements-popup.txt"])
    run([python, "-m", "pip", "install", "-r", "requirements-dev.txt"])
    run([python, "-m", "PyInstaller", "--noconfirm", "--clean", "main.spec"])

    print("Build terminé : dist\\DofusWindowManager.exe")


if __name__ == "__main__":
    main()
