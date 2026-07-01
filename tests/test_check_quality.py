from __future__ import annotations

from pathlib import Path

from core.check_quality import (
    find_duplicate_tags,
    find_manifest_strategy_hint,
    find_pending_format_mix,
    find_write_strategy_mix,
    has_collision_suffix,
)
from core.models import WRITE_MODE_MERGE_EXISTING, WRITE_MODE_NEW_FILE


def test_find_duplicate_tags(tmp_path: Path):
    di = tmp_path / "DefInjected" / "ThingDef"
    di.mkdir(parents=True)
    (di / "Items.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
  <Foo.label>a</Foo.label>
  <Foo.label>b</Foo.label>
</LanguageData>
""",
        encoding="utf-8",
    )
    found = find_duplicate_tags(tmp_path / "DefInjected")
    assert any("Foo.label" in item for item in found)


def test_find_write_strategy_mix(tmp_path: Path):
    di = tmp_path / "DefInjected" / "ThingDef"
    di.mkdir(parents=True)
    (di / "Items.xml").write_text(
        "<LanguageData>\n  <Foo.label>a</Foo.label>\n</LanguageData>\n",
        encoding="utf-8",
    )
    (di / "Demo_Items.xml").write_text(
        "<LanguageData>\n  <Foo.label>b</Foo.label>\n</LanguageData>\n",
        encoding="utf-8",
    )
    found = find_write_strategy_mix(tmp_path / "DefInjected", "Demo")
    assert any("Foo.label" in item for item in found)


def test_find_manifest_strategy_hint():
    meta = {"importWriteMode": WRITE_MODE_NEW_FILE}
    hint = find_manifest_strategy_hint(meta, WRITE_MODE_MERGE_EXISTING)
    assert hint is not None
    assert "new_file" in hint


def test_find_pending_format_mix(tmp_path: Path):
    (tmp_path / "DefInjected-missing.csv").write_text("a", encoding="utf-8")
    (tmp_path / "DefInjected-missing.xml").write_text("<LanguageData/>", encoding="utf-8")
    assert find_pending_format_mix(tmp_path)


def test_has_collision_suffix():
    assert has_collision_suffix("Demo-TC-2")
    assert not has_collision_suffix("Demo-TC")
