from __future__ import annotations

import re
from pathlib import Path

from core.cli import _localize_result
from core.models import CheckResult, ProjectConfig
from core.scan import run_check, stale_key_item
from ui.i18n.formatters import format_check_messages
from ui.i18n.translator import Translator

CJK = re.compile(r"[\u4e00-\u9fff]")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _collision_project(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    target = tmp_path / "target"
    for folder, name in (("A", "Alpha"), ("B", "Beta")):
        _write(
            source / "Defs" / folder / "Things.xml",
            f"<Defs><ThingDef><defName>{name}</defName><label>{name.lower()}</label></ThingDef></Defs>",
        )
    _write(
        target / "Languages" / "ChineseTraditional" / "DefInjected" / "ThingDef" / "Gone.xml",
        "<LanguageData><Missing.label>消失</Missing.label></LanguageData>",
    )
    return source, target


def test_check_messages_are_grouped_into_bullets():
    result = CheckResult(ok=True)
    result.message_keys = [
        ("msg.check.pending", {"count": 3}),
        ("msg.check.def_records", {"count": 10, "roots": 2}),
    ]
    result.warning_keys = [
        ("msg.check.stale_keys", {"count": 4, "items": ["Alpha.label", "Beta.label"], "more": 2}),
        ("msg.check.pending_format_mix", {}),
    ]
    assert format_check_messages(result, Translator("zh-Hant")).splitlines() == [
        "檢查結果",
        "• 尚待翻譯 3 條",
        "• 掃描 10 個 Def，來自 2 個 Defs 資料夾",
        "",
        "警告",
        "• 4 條譯文在原模組找不到對應，可能已過時",
        "  - Alpha.label",
        "  - Beta.label",
        "  - 另 2 條",
        "• 同時存在 CSV 與 XML 待譯檔，請勿混用格式",
    ]


def test_check_messages_without_warnings_have_no_warning_section():
    result = CheckResult(ok=True)
    result.message_keys = [("msg.check.pending", {"count": 0})]
    assert format_check_messages(result, Translator("en")).splitlines() == [
        "Check results",
        "• 0 entries pending translation",
    ]


def test_check_warnings_are_localized_with_details(tmp_path: Path):
    source, target = _collision_project(tmp_path)
    result = run_check(ProjectConfig(source, target, "ChineseTraditional"))
    text = format_check_messages(result, Translator("en"))
    assert not CJK.search(text)
    assert "• 1 target file(s) shared by multiple sources\n  - ThingDef/Things.xml: 2 sources" in text
    assert "• 1 translation key(s) no longer match the source mod and may be stale\n  - Missing.label" in text
    assert "Scanned 2 Defs in 1 Defs folder(s)" in text


def test_stale_key_details_are_shortened():
    assert stale_key_item("ThingDef/Gone.xml: Missing.label") == "Missing.label"
    assert (
        stale_key_item(
            "QuestScriptDef/Quest.xml: Raven_Quest.root.nodes.ShuttleDelay.node.nodes.Letter.label.slateRef"
        )
        == "Raven_Quest … Letter.label"
    )


def test_cli_localizes_check_warnings(tmp_path: Path):
    source, target = _collision_project(tmp_path)
    localized = _localize_result(run_check(ProjectConfig(source, target, "ChineseTraditional")), "en")
    assert localized.warnings[0].startswith("1 target file(s) shared by multiple sources\n  - ThingDef/Things.xml")
