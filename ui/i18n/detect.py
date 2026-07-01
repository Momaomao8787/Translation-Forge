from __future__ import annotations

import locale
import sys

SUPPORTED_UI_LOCALES = ("zh-Hant", "zh-Hans", "en")

_ZH_HANT_LCID = frozenset({1028, 3076, 5124})
_ZH_HANS_LCID = frozenset({2052, 4100})


def _locale_tag_from_string(tag: str | None) -> str | None:
    if not tag:
        return None
    normalized = tag.replace("_", "-").lower()
    if normalized.startswith("zh-tw") or normalized.startswith("zh-hk") or normalized.startswith("zh-mo"):
        return "zh-Hant"
    if normalized.startswith("zh-cn") or normalized.startswith("zh-sg") or normalized == "zh":
        return "zh-Hans"
    if normalized.startswith("zh"):
        return "zh-Hant"
    if normalized.startswith("en"):
        return "en"
    return None


def detect_system_ui_locale() -> str:
    if sys.platform == "win32":
        try:
            import ctypes

            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lang_id in _ZH_HANT_LCID:
                return "zh-Hant"
            if lang_id in _ZH_HANS_LCID:
                return "zh-Hans"
        except OSError:
            pass

    for getter in (locale.getlocale, locale.getdefaultlocale):
        try:
            tag = getter()[0]
        except (AttributeError, ValueError, TypeError):
            tag = None
        resolved = _locale_tag_from_string(tag)
        if resolved:
            return resolved

    return "en"


def resolve_ui_locale(saved: str | None) -> str:
    if saved in SUPPORTED_UI_LOCALES:
        return saved
    return detect_system_ui_locale()
