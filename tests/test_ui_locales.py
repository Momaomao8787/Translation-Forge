from __future__ import annotations

import json
from pathlib import Path

from core.models import RIMWORLD_LANGUAGES
from core.ui_locales import (
    RIMWORLD_TO_UI_LOCALE,
    SUPPORTED_UI_LOCALES,
    UI_LOCALE_LABELS,
    ui_locale_for_rimworld_lang,
    ui_locale_setting_key,
)

LOCALES_DIR = Path(__file__).resolve().parents[1] / "ui" / "i18n" / "locales"


def _load_locale(name: str) -> dict[str, str]:
    path = LOCALES_DIR / f"{name}.json"
    assert path.is_file(), f"missing locale file: {name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_supported_ui_locales_align_with_rimworld_languages() -> None:
    assert len(SUPPORTED_UI_LOCALES) == len(RIMWORLD_LANGUAGES)
    for lang in RIMWORLD_LANGUAGES:
        assert ui_locale_for_rimworld_lang(lang) in SUPPORTED_UI_LOCALES
    assert set(RIMWORLD_TO_UI_LOCALE) == set(RIMWORLD_LANGUAGES)
    assert len(UI_LOCALE_LABELS) == len(SUPPORTED_UI_LOCALES)


def test_locale_files_have_identical_keys() -> None:
    master = _load_locale("en")
    master_keys = set(master)
    for loc in SUPPORTED_UI_LOCALES:
        keys = set(_load_locale(loc))
        assert keys == master_keys, f"{loc}.json key mismatch"


def test_ui_locale_labels_present_and_nonempty() -> None:
    master = _load_locale("en")
    for loc in SUPPORTED_UI_LOCALES:
        table = _load_locale(loc)
        for target_loc in SUPPORTED_UI_LOCALES:
            key = ui_locale_setting_key(target_loc)
            assert key in table
            assert table[key].strip()
            assert table[key] == UI_LOCALE_LABELS[target_loc]


def test_native_locales_differ_from_english() -> None:
    en = _load_locale("en")
    probes = (
        "ui.work_mode.maintain",
        "action.check",
        "err.source_mod_missing",
        "notify.restart_body",
    )
    for loc in ("ja", "ko", "ru", "fr", "de", "es"):
        table = _load_locale(loc)
        assert any(table[key] != en[key] for key in probes), loc


def test_placeholder_locales_use_english_copy() -> None:
    en = _load_locale("en")
    for loc in ("it", "pt-BR", "pl", "cs", "tr", "uk"):
        table = _load_locale(loc)
        assert table["app.title"] == en["app.title"]
        assert table["err.source_mod_missing"] == en["err.source_mod_missing"]
