"""Render the static website with the application release metadata."""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from dwm import __release_tag__

REPOSITORY = "Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay"
VERSION = r"\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?"


def render_site(source: Path, destination: Path, tag: str) -> None:
    if re.fullmatch("v" + VERSION, tag) is None:
        raise ValueError("Invalid release tag")
    if destination.resolve() == source.resolve() or source.resolve() in destination.resolve().parents:
        raise ValueError("Build output must be outside the website sources")
    html = (source / "index.html").read_text(encoding="utf-8")
    release_prefix = f"https://github.com/{REPOSITORY}/releases/tag/"
    html, links = re.subn(re.escape(release_prefix) + "v" + VERSION, release_prefix + tag, html)
    html, metadata = re.subn(r'("softwareVersion"\s*:\s*")' + VERSION + '"',
                             lambda match: match[1] + tag[1:] + '"', html)
    html, labels = re.subn(r"(?<=Bêta publique )v" + VERSION, tag, html)
    if links < 2 or metadata != 1 or labels != 1:
        raise ValueError("Website release markers are missing or ambiguous")
    shutil.copytree(source, destination, dirs_exist_ok=True)
    (destination / "index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).parent / "website")
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    render_site(args.source, args.destination, __release_tag__)
