from __future__ import annotations

import locale
import sys

from core.ui_locales import SUPPORTED_UI_LOCALES

_ZH_HANT_LCID = frozenset({1028, 3076, 5124})
_ZH_HANS_LCID = frozenset({2052, 4100})

_TAG_PREFIX_TO_UI_LOCALE: tuple[tuple[str, str], ...] = (
    ("zh-tw", "zh-Hant"),
    ("zh-hk", "zh-Hant"),
    ("zh-mo", "zh-Hant"),
    ("zh-cn", "zh-Hans"),
    ("zh-sg", "zh-Hans"),
    ("zh", "zh-Hant"),
    ("ja", "ja"),
    ("ko", "ko"),
    ("ru", "ru"),
    ("fr", "fr"),
    ("de", "de"),
    ("es", "es"),
    ("it", "it"),
    ("pt", "pt-BR"),
    ("pl", "pl"),
    ("cs", "cs"),
    ("tr", "tr"),
    ("uk", "uk"),
    ("en", "en"),
)

_WIN_LCID_TO_UI_LOCALE: dict[int, str] = {
    1028: "zh-Hant",
    3076: "zh-Hant",
    5124: "zh-Hant",
    2052: "zh-Hans",
    4100: "zh-Hans",
    1041: "ja",
    1042: "ko",
    1049: "ru",
    1036: "fr",
    1031: "de",
    1034: "es",
    1040: "it",
    1046: "pt-BR",
    1045: "pl",
    1029: "cs",
    1055: "tr",
    1058: "uk",
    1033: "en",
    2057: "en",
    4105: "en",
}


def _locale_tag_from_string(tag: str | None) -> str | None:
    if not tag:
        return None
    normalized = tag.replace("_", "-").lower()
    for prefix, ui_locale in _TAG_PREFIX_TO_UI_LOCALE:
        if normalized == prefix or normalized.startswith(prefix + "-"):
            return ui_locale
    return None


def detect_system_ui_locale() -> str:
    if sys.platform == "win32":
        try:
            import ctypes

            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            resolved = _WIN_LCID_TO_UI_LOCALE.get(lang_id)
            if resolved:
                return resolved
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
    detected = detect_system_ui_locale()
    if detected in SUPPORTED_UI_LOCALES:
        return detected
    return "en"
