from __future__ import annotations

from pathlib import Path

from core.target_assess import assess_existing_target


def test_assess_empty_target(tmp_path: Path):
    target = tmp_path / "new-mod"
    result = assess_existing_target(target, "ChineseTraditional")
    assert not result.target_exists
    assert not result.needs_repeat_confirm


def test_assess_existing_about(tmp_path: Path):
    target = tmp_path / "mod"
    target.mkdir()
    (target / "About").mkdir()
    (target / "About" / "About.xml").write_text("<ModMetaData/>", encoding="utf-8")
    result = assess_existing_target(target, "ChineseTraditional")
    assert result.about_exists
    assert result.needs_repeat_confirm


def test_assess_existing_definjected(tmp_path: Path):
    target = tmp_path / "mod"
    di = target / "Languages" / "ChineseTraditional" / "DefInjected" / "ThingDef"
    di.mkdir(parents=True)
    (di / "A.xml").write_text("<LanguageData/>", encoding="utf-8")
    result = assess_existing_target(target, "ChineseTraditional")
    assert result.lang_path_exists
    assert result.definjected_xml_count == 1
    assert result.needs_repeat_confirm
