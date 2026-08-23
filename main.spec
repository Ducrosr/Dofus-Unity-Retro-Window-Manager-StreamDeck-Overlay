# -*- mode: python ; coding: utf-8 -*-
from importlib.util import find_spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_dir = Path(SPECPATH or ".").resolve()
icon_path = str(project_dir / "icons" / "dofus.ico")
streamdeck_plugin_path = str(
    project_dir / "streamdeck-plugin" / "com.remyducros.dofuswindowmanager.streamDeckPlugin"
)

popup_enabled = all(find_spec(module) is not None for module in ("cv2", "numpy", "windows_capture"))
popup_hidden = collect_submodules("windows_capture") if popup_enabled else []
excludes = ["pandas"]
if not popup_enabled:
    excludes.extend(["cv2", "numpy", "windows_capture"])

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (icon_path, "icons"),
        (str(project_dir / "assets" / "ankama"), "assets/ankama"),
        (streamdeck_plugin_path, "streamdeck-plugin"),
    ],
    hiddenimports=popup_hidden + ["pystray._win32"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="DofusWindowManager",
    icon=icon_path,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
