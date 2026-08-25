from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


PLUGIN_UUID = "com.remyducros.dofuswindowmanager"
ROOT_NAMESPACE = uuid.UUID("a8a95676-2dc6-48dc-84ed-32c252307853")
PLUGIN_ROOT = Path(__file__).resolve().parents[1] / f"{PLUGIN_UUID}.sdPlugin"
PROFILE_DIRECTORY = PLUGIN_ROOT / "profiles"


@dataclass(frozen=True)
class ProfileSpec:
    key: str
    filename: str
    name: str
    device_type: int
    model: str
    columns: int
    rows: int
    layout: tuple[tuple[str | int | None, ...], ...]


PROFILE_SPECS = (
    ProfileSpec(
        key="standard",
        filename="DofusWindowManager.streamDeckProfile",
        name="Dofus Window Manager — 15 touches",
        device_type=0,
        model="20GAA9901",
        columns=5,
        rows=3,
        layout=(
            ("move-up", 1, 2, 3, 4),
            ("move-down", 5, 6, 7, 8),
            ("show", "toggle-ignore", "refresh", "previous", "next"),
        ),
    ),
    ProfileSpec(
        key="mini",
        filename="DofusWindowManagerMini.streamDeckProfile",
        name="Dofus Window Manager — Mini",
        device_type=1,
        model="20GAI9901",
        columns=3,
        rows=2,
        layout=((1, 2, 3), (4, "previous", "next")),
    ),
    ProfileSpec(
        key="xl",
        filename="DofusWindowManagerXL.streamDeckProfile",
        name="Dofus Window Manager — XL",
        device_type=2,
        model="20GAT9901",
        columns=8,
        rows=4,
        layout=(
            (1, 2, 3, 4, 5, 6, 7, 8),
            (
                "move-up",
                "move-down",
                "show",
                "toggle-ignore",
                "refresh",
                "previous",
                "next",
                "next-attention",
            ),
            (None, None, None, None, None, None, None, None),
            (None, None, None, None, None, None, None, None),
        ),
    ),
    ProfileSpec(
        key="plus",
        filename="DofusWindowManagerPlus.streamDeckProfile",
        name="Dofus Window Manager — Plus",
        device_type=7,
        model="20GBD9901",
        columns=4,
        rows=2,
        layout=((1, 2, 3, 4), (5, 6, "previous", "next")),
    ),
    ProfileSpec(
        key="neo",
        filename="DofusWindowManagerNeo.streamDeckProfile",
        name="Dofus Window Manager — Neo",
        device_type=9,
        model="20GBJ9901",
        columns=4,
        rows=2,
        layout=((1, 2, 3, 4), (5, 6, "previous", "next")),
    ),
)


ACTION_NAMES = {
    "move-up": "Monter le personnage",
    "move-down": "Descendre le personnage",
    "show": "Lancer / afficher",
    "toggle-ignore": "Ignorer / réintégrer",
    "refresh": "Actualiser",
    "previous": "Précédent",
    "next": "Suivant",
    "next-attention": "Prochaine alerte",
}


def encoded_page_directory(page_id: uuid.UUID) -> str:
    encoded = base64.b32hexencode(page_id.bytes).decode("ascii").rstrip("=")
    return encoded.translate(str.maketrans({"U": "V", "V": "W"})) + "Z"


def action_state() -> dict[str, object]:
    return {
        "FontFamily": "",
        "FontSize": 9,
        "FontStyle": "",
        "FontUnderline": False,
        "OutlineThickness": 2,
        "ShowTitle": True,
        "TitleAlignment": "middle",
        "TitleColor": "#ffffff",
    }


def profile_action(spec: ProfileSpec, coordinate: str, key: str | int) -> dict[str, object]:
    action_id = str(uuid.uuid5(ROOT_NAMESPACE, f"{spec.key}:{coordinate}:{key}"))
    if isinstance(key, int):
        return {
            "ActionID": action_id,
            "LinkedTitle": True,
            "Name": "Personnage",
            "Settings": {
                "accentColor": "auto",
                "aliasLine": "4",
                "classLine": "3",
                "display": "name",
                "nameLine": "2",
                "positionLine": "1",
                "slot": str(key),
            },
            "State": 0,
            "States": [action_state(), action_state()],
            "UUID": f"{PLUGIN_UUID}.character",
        }
    return {
        "ActionID": action_id,
        "LinkedTitle": True,
        "Name": ACTION_NAMES[key],
        "Settings": {},
        "State": 0,
        "States": [action_state()],
        "UUID": f"{PLUGIN_UUID}.{key if key != 'show' else 'launch'}",
    }


def actions_for_spec(spec: ProfileSpec) -> dict[str, dict[str, object]]:
    actions: dict[str, dict[str, object]] = {}
    for row, keys in enumerate(spec.layout):
        if len(keys) != spec.columns:
            raise ValueError(f"{spec.key}: invalid column count on row {row}")
        for column, key in enumerate(keys):
            if key is None:
                continue
            coordinate = f"{column},{row}"
            actions[coordinate] = profile_action(spec, coordinate, key)
    if len(spec.layout) != spec.rows:
        raise ValueError(f"{spec.key}: invalid row count")
    return actions


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=4, ensure_ascii=False) + "\n").encode("utf-8")


def write_entry(archive: ZipFile, name: str, data: bytes) -> None:
    info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def build_profile(spec: ProfileSpec) -> Path:
    profile_root_id = uuid.uuid5(ROOT_NAMESPACE, f"{spec.key}:root")
    current_page_id = uuid.uuid5(ROOT_NAMESPACE, f"{spec.key}:current")
    default_page_id = uuid.uuid5(ROOT_NAMESPACE, f"{spec.key}:default")
    root = f"{str(profile_root_id).upper()}.sdProfile"
    current_directory = encoded_page_directory(current_page_id)
    default_directory = encoded_page_directory(default_page_id)
    root_manifest = {
        "Device": {"Model": spec.model, "UUID": ""},
        "Name": spec.name,
        "Pages": {
            "Current": str(current_page_id),
            "Default": str(default_page_id),
            "Pages": [str(current_page_id)],
        },
        "Version": "2.0",
    }
    current_manifest = {
        "Controllers": [{"Actions": actions_for_spec(spec), "Type": "Keypad"}],
        "Icon": "",
        "Name": "",
    }
    default_manifest = {
        "Controllers": [{"Actions": {}, "Type": "Keypad"}],
        "Icon": "",
        "Name": "",
    }
    PROFILE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    target = PROFILE_DIRECTORY / spec.filename
    with ZipFile(target, "w") as archive:
        write_entry(archive, f"{root}/manifest.json", json_bytes(root_manifest))
        write_entry(
            archive,
            f"{root}/Profiles/{current_directory}/manifest.json",
            json_bytes(current_manifest),
        )
        write_entry(
            archive,
            f"{root}/Profiles/{default_directory}/manifest.json",
            json_bytes(default_manifest),
        )
    return target


def main() -> None:
    for spec in PROFILE_SPECS:
        print(build_profile(spec).relative_to(PLUGIN_ROOT.parent))


if __name__ == "__main__":
    main()
