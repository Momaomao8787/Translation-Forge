from __future__ import annotations

import json
import os
from pathlib import Path

from core.models import (
    COMMON_LANGUAGES,
    EXPORT_LAYOUT_BY_SOURCE,
    EXPORT_LAYOUT_SINGLE,
    EXPORT_PLACEHOLDER_EMPTY,
    EXPORT_PLACEHOLDER_SOURCE,
    EXPORT_PLACEHOLDER_TODO,
    RIMWORLD_LANGUAGES,
    WORK_MODE_MAINTAIN,
    WORK_MODE_SCAFFOLD,
    WRITE_MODE_MERGE_EXISTING,
    WRITE_MODE_NEW_FILE,
)

SETTINGS_DIR = Path(os.environ.get("APPDATA", Path.home())) / "RimworldDefInjectTranslator"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

VALID_EXPORT_FORMATS = frozenset({"xml", "csv"})
_COMMON_LANGS = frozenset(COMMON_LANGUAGES)
_RIMWORLD_LANGS = frozenset(RIMWORLD_LANGUAGES)
_VALID_WORK_MODES = frozenset({WORK_MODE_MAINTAIN, WORK_MODE_SCAFFOLD})
_VALID_LAYOUTS = frozenset({EXPORT_LAYOUT_SINGLE, EXPORT_LAYOUT_BY_SOURCE})
_VALID_PLACEHOLDERS = frozenset(
    {EXPORT_PLACEHOLDER_EMPTY, EXPORT_PLACEHOLDER_TODO, EXPORT_PLACEHOLDER_SOURCE}
)
_VALID_WRITE_MODES = frozenset({WRITE_MODE_MERGE_EXISTING, WRITE_MODE_NEW_FILE})


def load_settings() -> dict:
    if not SETTINGS_FILE.is_file():
        return {}
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(patch: dict) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    data = load_settings()
    data.update(patch)
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_ui_locale() -> str | None:
    value = load_settings().get("uiLocale")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def set_ui_locale(locale: str) -> None:
    save_settings({"uiLocale": locale})


def project_settings_for_save(
    source_mod: str,
    target_mod: str,
    mod_language: str,
    export_format: str,
    *,
    work_mode: str | None = None,
    create_about: bool | None = None,
    export_layout: str | None = None,
    export_placeholder: str | None = None,
    export_write_mode: str | None = None,
    export_prefix: str | None = None,
    import_write_mode: str | None = None,
    import_prefix: str | None = None,
    about_name: str | None = None,
    package_id: str | None = None,
) -> dict:
    patch: dict = {}
    sm = (source_mod or "").strip()
    tm = (target_mod or "").strip()
    if sm:
        patch["sourceMod"] = sm
    if tm:
        patch["targetMod"] = tm
    if mod_language in _RIMWORLD_LANGS:
        patch["modLanguage"] = mod_language
    fmt = (export_format or "").strip().lower()
    if fmt in VALID_EXPORT_FORMATS:
        patch["exportFormat"] = fmt
    if work_mode in _VALID_WORK_MODES:
        patch["workMode"] = work_mode
    if create_about is not None:
        patch["createAbout"] = bool(create_about)
    if export_layout in _VALID_LAYOUTS:
        patch["exportLayout"] = export_layout
    if export_placeholder in _VALID_PLACEHOLDERS:
        patch["exportPlaceholder"] = export_placeholder
    if export_write_mode in _VALID_WRITE_MODES:
        patch["exportWriteMode"] = export_write_mode
    if export_prefix is not None and export_prefix.strip():
        patch["exportPrefix"] = export_prefix.strip()
    if import_write_mode in _VALID_WRITE_MODES:
        patch["importWriteMode"] = import_write_mode
    if import_prefix is not None and import_prefix.strip():
        patch["importPrefix"] = import_prefix.strip()
    if about_name is not None and about_name.strip():
        patch["aboutName"] = about_name.strip()
    if package_id is not None and package_id.strip():
        patch["packageId"] = package_id.strip()
    return patch


def parse_saved_project_settings(data: dict | None = None) -> dict:
    raw = data if data is not None else load_settings()
    out: dict = {}
    for key in ("sourceMod", "targetMod", "aboutName", "packageId"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            out[key] = value.strip()
    lang = raw.get("modLanguage")
    if isinstance(lang, str) and lang in _RIMWORLD_LANGS:
        out["modLanguage"] = lang
    elif isinstance(lang, str) and lang in _COMMON_LANGS:
        out["modLanguage"] = lang
    fmt = raw.get("exportFormat")
    if isinstance(fmt, str) and fmt.lower() in VALID_EXPORT_FORMATS:
        out["exportFormat"] = fmt.lower()
    mode = raw.get("workMode")
    if isinstance(mode, str) and mode in _VALID_WORK_MODES:
        out["workMode"] = mode
    if isinstance(raw.get("createAbout"), bool):
        out["createAbout"] = raw["createAbout"]
    layout = raw.get("exportLayout")
    if isinstance(layout, str) and layout in _VALID_LAYOUTS:
        out["exportLayout"] = layout
    ph = raw.get("exportPlaceholder")
    if isinstance(ph, str) and ph in _VALID_PLACEHOLDERS:
        out["exportPlaceholder"] = ph
    wm = raw.get("exportWriteMode")
    if isinstance(wm, str) and wm in _VALID_WRITE_MODES:
        out["exportWriteMode"] = wm
    if isinstance(raw.get("exportPrefix"), str) and raw["exportPrefix"].strip():
        out["exportPrefix"] = raw["exportPrefix"].strip()
    iwm = raw.get("importWriteMode")
    if isinstance(iwm, str) and iwm in _VALID_WRITE_MODES:
        out["importWriteMode"] = iwm
    if isinstance(raw.get("importPrefix"), str) and raw["importPrefix"].strip():
        out["importPrefix"] = raw["importPrefix"].strip()
    return out
