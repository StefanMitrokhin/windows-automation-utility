# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.building.build_main import COLLECT, EXE, PYZ, Analysis
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

SPECPATH = Path(SPECPATH)
ROOT = SPECPATH.parent

a = Analysis(
    [str(ROOT / "deskkit" / "entry_gui.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=collect_data_files("customtkinter")
    + [
        (str(ROOT / "deskkit" / "assets" / "icon.png"), "deskkit/assets"),
        (str(ROOT / "deskkit" / "assets" / "icon.ico"), "deskkit/assets"),
    ],
    hiddenimports=collect_submodules("customtkinter") + ["openpyxl", "psutil"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff", "PIL"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DeskKit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "deskkit" / "assets" / "icon.ico"),
    version=str(SPECPATH / "version_info.txt"),
    uac_admin=False,
    uac_uiaccess=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DeskKit",
)