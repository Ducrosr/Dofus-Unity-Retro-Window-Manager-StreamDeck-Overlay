"""Download official release assets without ever executing them."""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .update_checker import OFFICIAL_REPOSITORY, parse_release_version

MAX_ASSET_BYTES = 512 * 1024 * 1024
ASSET_NAMES = ("DofusWindowManager-Setup.exe", "DofusWindowManager.exe")


@dataclass(frozen=True)
class DownloadAsset:
    name: str
    url: str
    size: int
    sha256: str


def release_assets(tag: str, raw_assets: object) -> tuple[DownloadAsset, ...]:
    if parse_release_version(tag) is None or not isinstance(raw_assets, list):
        return ()
    result = []
    for name in ASSET_NAMES:
        matches = [a for a in raw_assets if isinstance(a, dict) and a.get("name") == name]
        if len(matches) != 1:
            continue
        raw = matches[0]
        url = f"https://github.com/{OFFICIAL_REPOSITORY}/releases/download/{quote(tag, safe='')}/{name}"
        digest = raw.get("digest", "")
        size = raw.get("size")
        if (raw.get("browser_download_url") != url
                or not isinstance(digest, str)
                or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest)
                or type(size) is not int or not 0 < size <= MAX_ASSET_BYTES):
            continue
        result.append(DownloadAsset(name, url, size, digest[7:].lower()))
    return tuple(result)


def _allowed_url(url: str) -> bool:
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.hostname in
            {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}
            and parsed.port in (None, 443) and not parsed.username and not parsed.password)


class OfficialRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _allowed_url(newurl):
            raise ValueError("Redirection de téléchargement non autorisée.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_asset(asset: DownloadAsset, directory: Path, cancel: Event, progress,
                   *, opener=None) -> Path:
    # Revalidate even when invoked outside the UI.
    prefix = f"https://github.com/{OFFICIAL_REPOSITORY}/releases/download/"
    if (asset.name not in ASSET_NAMES or not asset.url.startswith(prefix)
            or not _allowed_url(asset.url)
            or not re.fullmatch(r"[0-9a-f]{64}", asset.sha256)
            or not 0 < asset.size <= MAX_ASSET_BYTES):
        raise ValueError("Fichier de mise à jour non valide.")
    relative = asset.url[len(prefix):].split("/")
    if len(relative) != 2 or parse_release_version(relative[0]) is None or relative[1] != asset.name:
        raise ValueError("Fichier de mise à jour non valide.")
    if cancel.is_set():
        raise InterruptedError()
    # A unique directory prevents replacing any existing executable.
    folder = Path(tempfile.mkdtemp(prefix="DWM-update-", dir=directory))
    partial = folder / (asset.name + ".part")
    destination = folder / asset.name
    open_url = opener or build_opener(OfficialRedirectHandler()).open
    try:
        digest = hashlib.sha256()
        count = 0
        with open_url(Request(asset.url, headers={"User-Agent": "DofusWindowManager"}), timeout=15) as response:
            with partial.open("xb") as output:
                while True:
                    if cancel.is_set():
                        raise InterruptedError()
                    block = response.read(256 * 1024)
                    if not block:
                        break
                    count += len(block)
                    if count > asset.size:
                        raise ValueError("Taille du téléchargement incorrecte.")
                    output.write(block)
                    digest.update(block)
                    progress(count, asset.size)
                output.flush()
                os.fsync(output.fileno())
        if cancel.is_set():
            raise InterruptedError()
        if count != asset.size or digest.hexdigest() != asset.sha256:
            raise ValueError("La vérification SHA-256 a échoué.")
        partial.rename(destination)
        return destination
    except BaseException:
        partial.unlink(missing_ok=True)
        folder.rmdir()
        raise
