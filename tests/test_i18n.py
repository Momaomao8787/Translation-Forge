from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from core.models import ProjectConfig
from core.scan import run_check
from ui.i18n.detect import detect_system_ui_locale, resolve_ui_locale
from ui.i18n.translator import Translator


def test_translator_interpolation():
    tr = Translator("en")
    assert tr.t("msg.check.pending", count=5) == "5 entries pending translation"


def test_translator_fallback_to_en():
    tr = Translator("en")
    assert tr.t("nonexistent.key") == "nonexistent.key"


def test_resolve_ui_locale_prefers_saved():
    assert resolve_ui_locale("zh-Hans") == "zh-Hans"


def test_resolve_ui_locale_detect_when_empty():
    with patch("ui.i18n.detect.detect_system_ui_locale", return_value="en"):
        assert resolve_ui_locale(None) == "en"


def test_detect_system_ui_locale_windows_traditional():
    with patch("sys.platform", "win32"):
        with patch("ctypes.windll.kernel32.GetUserDefaultUILanguage", return_value=1028):
            assert detect_system_ui_locale() == "zh-Hant"


def test_detect_system_ui_locale_windows_simplified():
    with patch("sys.platform", "win32"):
        with patch("ctypes.windll.kernel32.GetUserDefaultUILanguage", return_value=2052):
            assert detect_system_ui_locale() == "zh-Hans"


def test_check_empty_path_error_key():
    config = ProjectConfig(Path(""), Path(""), "ChineseTraditional")
    result = run_check(config)
    assert result.error_key == "err.specify_source_mod"


def test_check_success_has_message_keys(tmp_path):
    from tests.test_workflow import _copy_fixtures

    source, target = _copy_fixtures(tmp_path)
    result = run_check(ProjectConfig(source, target, "ChineseTraditional"))
    assert result.ok
    assert len(result.message_keys) >= 2
    tr = Translator("en")
    text = "\n".join(tr.t(k, **p) for k, p in result.message_keys)
    assert "pending translation" in text
