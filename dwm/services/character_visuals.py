from __future__ import annotations

import base64
import binascii
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Mapping

from PIL import Image, ImageDraw, ImageFont, ImageOps

from ..utils.paths import resource_path


MAX_PORTRAIT_SOURCE_BYTES = 20 * 1024 * 1024
MAX_PORTRAIT_DATA_LENGTH = 500_000
MAX_PORTRAIT_SOURCE_PIXELS = 40_000_000
PORTRAIT_SIZE = 96

BADGE_CATALOG: dict[str, tuple[str, str, str]] = {
    "none": ("Aucune icône", "", "#64748b"),
}

ANKAMA_ICON_FILENAMES = (
    "Agilite.png", "Chance.png", "Critique.png", "Dommage_Arme.png",
    "Dommage_Critique.png", "Dommage_Distance.png", "Dommage_Melee.png",
    "Dommage_Neutre.png", "Dommage_Poussee.png", "Dommage_Sort.png",
    "Esquive_PA.png", "Esquive_PM.png", "Force.png", "Fuite.png",
    "Initiative.png", "Intelligence.png", "Invocation.png", "PA.png", "PM.png",
    "PO.png", "Pods.png", "Prospection.png", "Puissance.png",
    "Resistance_Air.png", "Resistance_Arme.png", "Resistance_Critique.png",
    "Resistance_Distance.png", "Resistance_Eau.png", "Resistance_Feu.png",
    "Resistance_Melee.png", "Resistance_Neutre.png", "Resistance_Poussee.png",
    "Resistance_Terre.png", "Retrait_PA.png", "Retrait_PM.png", "Sagesse.png",
    "Soin.png", "Tacle.png", "Vitalite.png",
)

ANKAMA_METIER_FILENAMES = (
    "alchimiste.png", "bijoutier.png", "bricoleur.png", "bucheron.png",
    "chasseur.png", "cordomage.png", "cordonnier.png", "costumage.png",
    "eleveur.png", "facomage.png", "faconneur.png", "forgemage.png",
    "forgeron.png", "joaillomage.png", "mineur.png", "paysan.png",
    "pecheur.png", "sculptemage.png", "sculpteur.png", "tailleur.png",
)

_ANKAMA_ICON_LABELS = {
    "Agilite": "Agilité",
    "Dommage_Arme": "Dommages d’arme",
    "Dommage_Critique": "Dommages critiques",
    "Dommage_Distance": "Dommages à distance",
    "Dommage_Melee": "Dommages en mêlée",
    "Dommage_Neutre": "Dommages neutres",
    "Dommage_Poussee": "Dommages de poussée",
    "Dommage_Sort": "Dommages aux sorts",
    "Esquive_PA": "Esquive PA",
    "Esquive_PM": "Esquive PM",
    "Resistance_Air": "Résistance Air",
    "Resistance_Arme": "Résistance aux armes",
    "Resistance_Critique": "Résistance critique",
    "Resistance_Distance": "Résistance à distance",
    "Resistance_Eau": "Résistance Eau",
    "Resistance_Feu": "Résistance Feu",
    "Resistance_Melee": "Résistance en mêlée",
    "Resistance_Neutre": "Résistance Neutre",
    "Resistance_Poussee": "Résistance aux poussées",
    "Resistance_Terre": "Résistance Terre",
    "Retrait_PA": "Retrait PA",
    "Retrait_PM": "Retrait PM",
    "Soin": "Soins",
    "Vitalite": "Vitalité",
}

_ANKAMA_METIER_LABELS = {
    "alchimiste": "Alchimiste",
    "bijoutier": "Bijoutier",
    "bricoleur": "Bricoleur",
    "bucheron": "Bûcheron",
    "chasseur": "Chasseur",
    "cordomage": "Cordomage",
    "cordonnier": "Cordonnier",
    "costumage": "Costumage",
    "eleveur": "Éleveur",
    "facomage": "Façomage",
    "faconneur": "Façonneur",
    "forgemage": "Forgemage",
    "forgeron": "Forgeron",
    "joaillomage": "Joaillomage",
    "mineur": "Mineur",
    "paysan": "Paysan",
    "pecheur": "Pêcheur",
    "sculptemage": "Sculptemage",
    "sculpteur": "Sculpteur",
    "tailleur": "Tailleur",
}

ANKAMA_ICON_FILES: dict[str, str] = {}
for _filename in ANKAMA_ICON_FILENAMES:
    _stem = Path(_filename).stem
    _key = "ankama_" + _stem.lower()
    ANKAMA_ICON_FILES[_key] = f"icons/{_filename}"
    _label = _ANKAMA_ICON_LABELS.get(_stem, _stem.replace("_", " "))
    BADGE_CATALOG[_key] = (f"Jeu — {_label}", "", "#d7b384")

for _filename in ANKAMA_METIER_FILENAMES:
    _stem = Path(_filename).stem
    _key = "ankama_metier_" + _stem.lower()
    ANKAMA_ICON_FILES[_key] = f"metiers/{_filename}"
    _label = _ANKAMA_METIER_LABELS.get(_stem, _stem.replace("_", " ").title())
    BADGE_CATALOG[_key] = (f"Métier — {_label}", "", "#d7b384")

_CLASS_LABELS = {
    "Cra": "Crâ",
    "Feca": "Féca",
    "Xelor": "Xélor",
}


def normalize_badge(value: object) -> str:
    badge = str(value or "none").strip().lower()
    return badge if badge in BADGE_CATALOG else "none"


def badge_label(badge: object) -> str:
    return BADGE_CATALOG[normalize_badge(badge)][0]


def badge_from_label(label: str) -> str:
    requested = str(label or "").strip()
    for badge, (candidate, _glyph, _color) in BADGE_CATALOG.items():
        if candidate == requested:
            return badge
    return "none"


def validate_portrait_data(value: object) -> str:
    data = str(value or "").strip()
    prefix = "data:image/png;base64,"
    if not data.startswith(prefix) or len(data) > MAX_PORTRAIT_DATA_LENGTH:
        return ""
    try:
        raw = base64.b64decode(data[len(prefix) :], validate=True)
    except (binascii.Error, ValueError):
        return ""
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return ""
    try:
        with Image.open(BytesIO(raw)) as opened:
            if opened.format != "PNG" or opened.width > 512 or opened.height > 512:
                return ""
            opened.verify()
    except Exception:
        return ""
    return data


def sanitize_character_visuals(value: object) -> dict[str, dict[str, str]]:
    if not isinstance(value, Mapping):
        return {}
    visuals: dict[str, dict[str, str]] = {}
    for raw_pseudo, raw_appearance in value.items():
        pseudo = str(raw_pseudo or "").strip()[:80]
        if not pseudo or not isinstance(raw_appearance, Mapping):
            continue
        portrait = validate_portrait_data(raw_appearance.get("portrait"))
        badge = normalize_badge(raw_appearance.get("badge"))
        if portrait or badge != "none":
            visuals[pseudo] = {"portrait": portrait, "badge": badge}
    return visuals


def encode_portrait_file(path: str | Path, *, size: int = PORTRAIT_SIZE) -> str:
    source = Path(path)
    if not source.is_file():
        raise ValueError("Le portrait sélectionné n’existe pas.")
    if source.stat().st_size > MAX_PORTRAIT_SOURCE_BYTES:
        raise ValueError("Le portrait dépasse la taille maximale de 20 Mo.")

    try:
        with Image.open(source) as opened:
            if opened.width * opened.height > MAX_PORTRAIT_SOURCE_PIXELS:
                raise ValueError("Le portrait dépasse 40 millions de pixels.")
            image = ImageOps.exif_transpose(opened).convert("RGBA")
            image = ImageOps.fit(
                image,
                (int(size), int(size)),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.42),
            )
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Le fichier sélectionné n’est pas une image compatible.") from exc

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    data = "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")
    if len(data) > MAX_PORTRAIT_DATA_LENGTH:
        raise ValueError("Le portrait converti est trop volumineux.")
    return data


def decode_portrait_data(data: object) -> Image.Image | None:
    validated = validate_portrait_data(data)
    if not validated:
        return None
    try:
        raw = base64.b64decode(validated.split(",", 1)[1], validate=True)
        with Image.open(BytesIO(raw)) as opened:
            return opened.convert("RGBA")
    except Exception:
        return None


def build_avatar_image(
    pseudo: str,
    *,
    portrait_data: str = "",
    badge: str = "none",
    size: int = 64,
    background: str = "#223047",
    foreground: str = "#ffffff",
    show_badge: bool = True,
) -> Image.Image:
    size = max(24, min(256, int(size)))
    portrait = decode_portrait_data(portrait_data)
    if portrait is not None:
        avatar = ImageOps.fit(portrait, (size, size), method=Image.Resampling.LANCZOS)
    else:
        avatar = Image.new("RGBA", (size, size), background)
        draw = ImageDraw.Draw(avatar)
        initial = (str(pseudo or "?").strip()[:1] or "?").upper()
        font = _load_font(max(13, int(size * 0.46)), bold=True)
        draw.text((size / 2, size / 2), initial, fill=foreground, font=font, anchor="mm")

    badge = normalize_badge(badge)
    if show_badge and badge != "none":
        _draw_badge(avatar, badge, size)
    return avatar


def build_badge_tile_image(
    badge: str,
    *,
    size: int = 64,
    background: str = "#223047",
) -> Image.Image:
    """Render a standalone badge without creating a fallback character portrait."""
    size = max(24, min(256, int(size)))
    image = Image.new("RGBA", (size, size), background)
    badge = normalize_badge(badge)
    if badge == "none":
        return image

    _label, glyph, color = BADGE_CATALOG[badge]
    icon = _load_ankama_icon(badge)
    if icon is not None:
        icon_size = max(16, int(size * 0.76))
        fitted = ImageOps.contain(icon, (icon_size, icon_size), method=Image.Resampling.LANCZOS)
        image.alpha_composite(fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2))
        return image

    draw = ImageDraw.Draw(image)
    diameter = max(18, int(size * 0.72))
    offset = (size - diameter) // 2
    draw.ellipse(
        (offset, offset, offset + diameter, offset + diameter),
        fill=color,
        outline="#111827",
        width=max(1, int(size * 0.035)),
    )
    font = _load_font(max(11, int(diameter * 0.48)), bold=True)
    text_color = "#111827" if badge in {"neutral", "wisdom", "farmer"} else "#ffffff"
    draw.text((size / 2, size / 2), glyph, fill=text_color, font=font, anchor="mm")
    return image


def _draw_badge(image: Image.Image, badge: str, size: int) -> None:
    _label, glyph, color = BADGE_CATALOG[badge]
    diameter = max(16, int(size * 0.38))
    margin = max(1, int(size * 0.03))
    left = size - diameter - margin
    top = size - diameter - margin
    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (left, top, left + diameter, top + diameter),
        fill=color,
        outline="#111827",
        width=max(1, int(size * 0.025)),
    )
    ankama_icon = _load_ankama_icon(badge)
    if ankama_icon is not None:
        icon_size = max(12, int(diameter * 0.82))
        fitted = ImageOps.contain(ankama_icon, (icon_size, icon_size), method=Image.Resampling.LANCZOS)
        x = int(left + (diameter - fitted.width) / 2)
        y = int(top + (diameter - fitted.height) / 2)
        image.alpha_composite(fitted, (x, y))
        return
    font = _load_font(max(10, int(diameter * 0.53)), bold=True)
    text_color = "#111827" if badge in {"neutral", "wisdom", "farmer"} else "#ffffff"
    draw.text(
        (left + diameter / 2, top + diameter / 2),
        glyph,
        fill=text_color,
        font=font,
        anchor="mm",
    )


@lru_cache(maxsize=64)
def _load_ankama_icon(badge: str) -> Image.Image | None:
    relative_path = ANKAMA_ICON_FILES.get(normalize_badge(badge))
    if not relative_path:
        return None
    try:
        with Image.open(resource_path("assets", "ankama", *Path(relative_path).parts)) as opened:
            return opened.convert("RGBA")
    except Exception:
        return None


@lru_cache(maxsize=64)
def bundled_icon_data_uri(badge: str) -> str:
    relative_path = ANKAMA_ICON_FILES.get(normalize_badge(badge))
    if not relative_path:
        return ""
    try:
        raw = Path(resource_path("assets", "ankama", *Path(relative_path).parts)).read_bytes()
    except OSError:
        return ""
    if not raw.startswith(b"\x89PNG\r\n\x1a\n") or len(raw) > 100_000:
        return ""
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


@lru_cache(maxsize=1)
def bundled_portrait_choices() -> dict[str, str]:
    folder = Path(resource_path("assets", "ankama", "portraits"))
    choices: dict[str, str] = {}
    if not folder.is_dir():
        return choices
    for path in sorted(folder.glob("*.png"), key=lambda item: item.name.casefold()):
        try:
            class_name, gender = path.stem.rsplit("_", 1)
        except ValueError:
            continue
        class_label = _CLASS_LABELS.get(class_name, class_name)
        gender_label = "Féminin" if gender.upper() == "F" else "Masculin"
        choices[f"{class_label} — {gender_label}"] = str(path)
    return choices


def _load_font(size: int, *, bold: bool) -> ImageFont.ImageFont:
    candidates = (
        "seguisb.ttf" if bold else "segoeui.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()
