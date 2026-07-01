from ui.i18n.detect import detect_system_ui_locale, resolve_ui_locale, SUPPORTED_UI_LOCALES
from ui.i18n.settings import load_ui_locale, save_ui_locale
from ui.i18n.translator import Translator

__all__ = [
    "Translator",
    "SUPPORTED_UI_LOCALES",
    "detect_system_ui_locale",
    "resolve_ui_locale",
    "load_ui_locale",
    "save_ui_locale",
]
