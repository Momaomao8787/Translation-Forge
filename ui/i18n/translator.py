from __future__ import annotations

import json
from pathlib import Path

from core.ui_locales import SUPPORTED_UI_LOCALES, ui_locale_setting_key

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"


class Translator:
    def __init__(self, locale: str = "zh-Hant") -> None:
        self._locale = locale if locale in SUPPORTED_UI_LOCALES else "en"
        self._tables: dict[str, dict[str, str]] = {}
        self._load_all()

    def _load_all(self) -> None:
        for loc in SUPPORTED_UI_LOCALES:
            path = _LOCALES_DIR / f"{loc}.json"
            if path.is_file():
                self._tables[loc] = json.loads(path.read_text(encoding="utf-8"))

    @property
    def locale(self) -> str:
        return self._locale

    def set_locale(self, locale: str) -> None:
        if locale in SUPPORTED_UI_LOCALES:
            self._locale = locale

    def t(self, key: str, **params: object) -> str:
        text = self._tables.get(self._locale, {}).get(key)
        if text is None:
            text = self._tables.get("en", {}).get(key, key)
        if params:
            try:
                return text.format(**params)
            except KeyError:
                return text
        return text

    def locale_options(self) -> list[tuple[str, str]]:
        return [(loc, self.t(ui_locale_setting_key(loc))) for loc in SUPPORTED_UI_LOCALES]
