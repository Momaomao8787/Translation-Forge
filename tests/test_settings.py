from __future__ import annotations

import json
from pathlib import Path

import pytest

from core import settings as settings_mod
from core.cli import main as cli_main
from tests.test_workflow import _copy_fixtures


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings_mod, "SETTINGS_DIR", tmp_path)
    monkeypatch.setattr(settings_mod, "SETTINGS_FILE", path)
    return path


def test_save_settings_merges_ui_locale(settings_file):
    settings_mod.set_ui_locale("zh-Hant")
    settings_mod.save_settings({"sourceMod": r"C:\Mods\Source"})
    data = json.loads(settings_file.read_text(encoding="utf-8"))
    assert data["uiLocale"] == "zh-Hant"
    assert data["sourceMod"] == r"C:\Mods\Source"


def test_project_settings_for_save_validates_export_format():
    patch = settings_mod.project_settings_for_save("", "", "ChineseTraditional", "bad")
    assert "exportFormat" not in patch
    patch = settings_mod.project_settings_for_save("", "", "ChineseTraditional", "csv")
    assert patch["exportFormat"] == "csv"


def test_parse_saved_project_settings_ignores_invalid_export_format():
    saved = settings_mod.parse_saved_project_settings(
        {
            "sourceMod": r"C:\A",
            "exportFormat": "bad",
            "modLanguage": "NotALanguage",
        }
    )
    assert saved["sourceMod"] == r"C:\A"
    assert "exportFormat" not in saved
    assert "modLanguage" not in saved


def test_cli_check_locale_en(tmp_path, capsys):
    source, target = _copy_fixtures(tmp_path)
    code = cli_main(
        [
            "--locale",
            "en",
            "check",
            "--source-mod",
            str(source),
            "--target-mod",
            str(target),
            "--lang",
            "ChineseTraditional",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "pending translation" in out
    assert "尚待翻譯" not in out


def test_cli_check_without_locale_keeps_zh_fallback(tmp_path, capsys):
    source, target = _copy_fixtures(tmp_path)
    cli_main(
        [
            "check",
            "--source-mod",
            str(source),
            "--target-mod",
            str(target),
            "--lang",
            "ChineseTraditional",
        ]
    )
    out = capsys.readouterr().out
    assert "尚待翻譯" in out
