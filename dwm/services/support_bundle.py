from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

from ..storage.atomic import atomic_write_bytes


SUPPORT_FORMAT = "dofus-window-manager-support"
SUPPORT_SCHEMA_VERSION = 1
MAX_LOG_BYTES = 256_000


def redact_support_text(
    text: object,
    *,
    sensitive_values: Iterable[object] = (),
    private_paths: Iterable[object] = (),
    window_ids: Iterable[object] = (),
) -> str:
    redacted = str(text or "")

    for path in sorted(
        {str(value).strip() for value in private_paths if str(value).strip()},
        key=len,
        reverse=True,
    ):
        redacted = re.sub(re.escape(path), "<DOSSIER_PRIVE>", redacted, flags=re.IGNORECASE)

    redacted = re.sub(
        r"(?i)\b[A-Z]:\\Users\\[^\\\s]+",
        r"C:\\Users\\<UTILISATEUR>",
        redacted,
    )
    redacted = re.sub(
        r"(?i)(?<![\w])/(?:home|Users)/[^/\s]+",
        "/home/<UTILISATEUR>",
        redacted,
    )
    redacted = re.sub(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "<EMAIL>",
        redacted,
    )

    for index, value in enumerate(
        sorted(
            {str(item).strip() for item in sensitive_values if len(str(item).strip()) >= 2},
            key=len,
            reverse=True,
        ),
        start=1,
    ):
        redacted = re.sub(
            re.escape(value),
            f"<DONNEE_PRIVEE_{index}>",
            redacted,
            flags=re.IGNORECASE,
        )

    for value in {str(item).strip() for item in window_ids if str(item).strip()}:
        redacted = re.sub(
            rf"(?<!\d){re.escape(value)}(?!\d)",
            "<ID_FENETRE>",
            redacted,
        )
    return redacted


def sanitize_settings_for_support(settings: Mapping[str, object]) -> dict[str, object]:
    sanitized = json.loads(json.dumps(dict(settings), ensure_ascii=False))
    visuals = sanitized.get("character_visuals")
    sanitized["character_visuals"] = {
        "entries_removed": len(visuals) if isinstance(visuals, dict) else 0
    }
    if str(sanitized.get("last_profile") or "").strip():
        sanitized["last_profile"] = "<PROFIL_PRIVE>"
    return sanitized


def _read_log_tail(path: Path, max_bytes: int = MAX_LOG_BYTES) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if len(data) > max_bytes:
        data = data[-max_bytes:]
        prefix = "[début tronqué — seules les lignes les plus récentes sont incluses]\n"
    else:
        prefix = ""
    return prefix + data.decode("utf-8", errors="replace")


def create_support_bundle(
    destination: str | Path,
    *,
    diagnostic_report: str,
    settings: Mapping[str, object],
    log_paths: Iterable[str | Path],
    sensitive_values: Iterable[object] = (),
    private_paths: Iterable[object] = (),
    window_ids: Iterable[object] = (),
    app_version: str,
) -> Path:
    destination_path = Path(destination)
    values = tuple(sensitive_values)
    paths = tuple(private_paths)
    ids = tuple(window_ids)
    sanitized_settings = sanitize_settings_for_support(settings)
    manifest = {
        "format": SUPPORT_FORMAT,
        "schema_version": SUPPORT_SCHEMA_VERSION,
        "app_version": app_version,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "anonymized": True,
        "log_tail_limit_bytes": MAX_LOG_BYTES,
    }
    readme = (
        "Paquet de support Dofus Window Manager\n\n"
        "Ce fichier a été généré localement. Les pseudos, alias, noms de profils, "
        "identifiants de fenêtres, adresses e-mail et chemins utilisateurs connus "
        "ont été remplacés. Les portraits ne sont jamais inclus.\n\n"
        "Une anonymisation automatique ne peut pas garantir qu’un texte saisi "
        "manuellement dans un journal ne contient aucune donnée personnelle. "
        "Relisez le contenu avant de le publier.\n"
    )

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.txt", readme)
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        )
        archive.writestr(
            "diagnostic.txt",
            redact_support_text(
                diagnostic_report,
                sensitive_values=values,
                private_paths=paths,
                window_ids=ids,
            ),
        )
        archive.writestr(
            "settings-sanitized.json",
            json.dumps(sanitized_settings, indent=2, ensure_ascii=False) + "\n",
        )
        for log_path in log_paths:
            path = Path(log_path)
            content = _read_log_tail(path)
            if not content:
                continue
            archive.writestr(
                f"logs/{path.name}",
                redact_support_text(
                    content,
                    sensitive_values=values,
                    private_paths=paths,
                    window_ids=ids,
                ),
            )

    atomic_write_bytes(destination_path, archive_buffer.getvalue())
    return destination_path

