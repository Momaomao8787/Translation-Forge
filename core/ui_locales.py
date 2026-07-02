from __future__ import annotations

from core.models import RIMWORLD_LANGUAGES

RIMWORLD_TO_UI_LOCALE: dict[str, str] = {
    "ChineseTraditional": "zh-Hant",
    "ChineseSimplified": "zh-Hans",
    "English": "en",
    "Japanese": "ja",
    "Korean": "ko",
    "Russian": "ru",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "PortugueseBrazilian": "pt-BR",
    "Polish": "pl",
    "Czech": "cs",
    "Turkish": "tr",
    "Ukrainian": "uk",
}

UI_LOCALE_TO_RIMWORLD: dict[str, str] = {v: k for k, v in RIMWORLD_TO_UI_LOCALE.items()}

SUPPORTED_UI_LOCALES: tuple[str, ...] = tuple(
    RIMWORLD_TO_UI_LOCALE[lang] for lang in RIMWORLD_LANGUAGES
)

UI_LOCALE_LABELS: dict[str, str] = {
    "zh-Hant": "繁體中文",
    "zh-Hans": "简体中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "ru": "Русский",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "it": "Italiano",
    "pt-BR": "Português (BR)",
    "pl": "Polski",
    "cs": "Čeština",
    "tr": "Türkçe",
    "uk": "Українська",
}


def ui_locale_for_rimworld_lang(rimworld_lang: str) -> str | None:
    return RIMWORLD_TO_UI_LOCALE.get(rimworld_lang)


def rimworld_lang_for_ui_locale(ui_locale: str) -> str | None:
    return UI_LOCALE_TO_RIMWORLD.get(ui_locale)


def ui_locale_setting_key(ui_locale: str) -> str:
    return f"ui.locale.{ui_locale.replace('-', '_')}"
