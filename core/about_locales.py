from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from core.ui_locales import ui_locale_for_rimworld_lang

ABOUT_DESCRIPTION_KEY = "about.description.template"
_LOCALES_DIR = Path(__file__).resolve().parents[1] / "ui" / "i18n" / "locales"
_OVERLAYS_DIR = Path(__file__).resolve().parents[1] / "scripts" / "locale_overlays"
_FALLBACK_EN = "This mod was created with Momaomao's Translation Forge"


@lru_cache(maxsize=32)
def _load_table(ui_locale: str) -> dict[str, str]:
    path = _LOCALES_DIR / f"{ui_locale}.json"
    if not path.is_file():
        return {}
    table = json.loads(path.read_text(encoding="utf-8"))
    overlay = _OVERLAYS_DIR / f"{ui_locale}.json"
    if overlay.is_file():
        table.update(json.loads(overlay.read_text(encoding="utf-8")))
    return table


def default_about_description(rimworld_lang: str) -> str:
    ui_locale = ui_locale_for_rimworld_lang(rimworld_lang) or "en"
    text = _load_table(ui_locale).get(ABOUT_DESCRIPTION_KEY)
    if text:
        return text
    return _load_table("en").get(ABOUT_DESCRIPTION_KEY, _FALLBACK_EN)
