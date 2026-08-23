from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


OFFICIAL_REPOSITORY = "Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay"
RELEASES_API_URL = f"https://api.github.com/repos/{OFFICIAL_REPOSITORY}/releases?per_page=20"
OFFICIAL_RELEASE_URL = f"https://github.com/{OFFICIAL_REPOSITORY}/releases/tag"
AUTOMATIC_CHECK_INTERVAL = timedelta(hours=24)
MAX_RESPONSE_BYTES = 1024 * 1024

_VERSION_PATTERN = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-(?P<stage>alpha|beta|rc)(?:[.-]?(?P<number>\d+))?)?$",
    re.IGNORECASE,
)
_STAGE_RANK = {"alpha": 0, "beta": 1, "rc": 2, "stable": 3}


class UpdateCheckError(RuntimeError):
    """Raised when the official releases feed cannot be checked safely."""


@dataclass(frozen=True, order=True)
class ReleaseVersion:
    major: int
    minor: int
    patch: int
    stage_rank: int
    stage_number: int

    @property
    def is_prerelease(self) -> bool:
        return self.stage_rank < _STAGE_RANK["stable"]


@dataclass(frozen=True)
class ReleaseInfo:
    tag: str
    name: str
    url: str
    published_at: str
    prerelease: bool


@dataclass(frozen=True)
class UpdateCheckResult:
    current_tag: str
    latest_release: ReleaseInfo | None
    update_available: bool


def parse_release_version(tag: str) -> ReleaseVersion | None:
    match = _VERSION_PATTERN.fullmatch((tag or "").strip())
    if match is None:
        return None

    stage = (match.group("stage") or "stable").lower()
    return ReleaseVersion(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        stage_rank=_STAGE_RANK[stage],
        stage_number=int(match.group("number") or 0),
    )


def select_latest_release(
    releases: Iterable[object],
    *,
    include_prereleases: bool,
) -> tuple[ReleaseInfo, ReleaseVersion] | None:
    candidates: list[tuple[ReleaseVersion, ReleaseInfo]] = []
    for raw_release in releases:
        if not isinstance(raw_release, dict) or bool(raw_release.get("draft")):
            continue

        tag = str(raw_release.get("tag_name") or "").strip()
        version = parse_release_version(tag)
        if version is None:
            continue

        prerelease = bool(raw_release.get("prerelease")) or version.is_prerelease
        if prerelease and not include_prereleases:
            continue

        name = str(raw_release.get("name") or tag).strip() or tag
        published_at = str(raw_release.get("published_at") or "").strip()
        release_url = f"{OFFICIAL_RELEASE_URL}/{quote(tag, safe='')}"
        info = ReleaseInfo(
            tag=tag,
            name=name[:160],
            url=release_url,
            published_at=published_at,
            prerelease=prerelease,
        )
        candidates.append((version, info))

    if not candidates:
        return None
    version, info = max(candidates, key=lambda candidate: candidate[0])
    return info, version


def check_for_update(
    current_tag: str,
    *,
    include_prereleases: bool,
    timeout: float = 5.0,
    opener: Callable[..., object] = urlopen,
) -> UpdateCheckResult:
    current_version = parse_release_version(current_tag)
    if current_version is None:
        raise UpdateCheckError(f"Version installée non reconnue : {current_tag}")

    request = Request(
        RELEASES_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": f"DofusWindowManager/{current_tag.lstrip('v')}",
        },
        method="GET",
    )

    try:
        response = opener(request, timeout=timeout)
        try:
            payload_bytes = response.read(MAX_RESPONSE_BYTES + 1)
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()
    except HTTPError as exc:
        if exc.code in (403, 429):
            raise UpdateCheckError("La limite temporaire de GitHub a été atteinte.") from exc
        raise UpdateCheckError(f"GitHub a répondu avec l’erreur HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise UpdateCheckError("Impossible de joindre le dépôt GitHub officiel.") from exc

    if len(payload_bytes) > MAX_RESPONSE_BYTES:
        raise UpdateCheckError("La réponse de GitHub est anormalement volumineuse.")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateCheckError("La réponse de GitHub n’est pas exploitable.") from exc
    if not isinstance(payload, list):
        raise UpdateCheckError("La réponse de GitHub ne contient pas de liste de versions.")

    selected = select_latest_release(payload, include_prereleases=include_prereleases)
    if selected is None:
        return UpdateCheckResult(current_tag=current_tag, latest_release=None, update_available=False)

    latest_release, latest_version = selected
    return UpdateCheckResult(
        current_tag=current_tag,
        latest_release=latest_release,
        update_available=latest_version > current_version,
    )


def utc_now_iso(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_automatic_check_due(
    last_check_at: str,
    *,
    now: datetime | None = None,
    interval: timedelta = AUTOMATIC_CHECK_INTERVAL,
) -> bool:
    raw_value = (last_check_at or "").strip()
    if not raw_value:
        return True

    try:
        checked_at = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return True
    if checked_at.tzinfo is None:
        checked_at = checked_at.replace(tzinfo=timezone.utc)

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc) - checked_at.astimezone(timezone.utc) >= interval
