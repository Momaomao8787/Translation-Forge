# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

locale_datas = [
    (str(root / "ui" / "i18n" / "locales"), "ui/i18n/locales"),
]

a = Analysis(
    ["ui/main.py"],
    pathex=[str(root)],
    binaries=[],
    datas=locale_datas,
    hiddenimports=[
        "core",
        "core.about_template",
        "core.check_quality",
        "core.definjected_write",
        "core.errors",
        "core.export",
        "core.export_merge",
        "core.field_collect",
        "core.field_path",
        "core.field_resolve",
        "core.fix_src",
        "core.import_merge",
        "core.meta",
        "core.models",
        "core.path_suggest",
        "core.paths",
        "core.prefix",
        "core.scan",
        "core.scaffold",
        "core.settings",
        "core.src_comment",
        "core.target_assess",
        "ui.i18n",
        "ui.i18n.detect",
        "ui.i18n.formatters",
        "ui.i18n.settings",
        "ui.i18n.translator",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="TranslationForge-UI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
