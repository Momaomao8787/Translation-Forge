from __future__ import annotations

from pathlib import Path

from core.export import run_export
from core.export_merge import default_single_pending_path, merge_pending_entries, placeholder_text
from core.import_merge import load_entries_csv
from core.models import (
    EXPORT_LAYOUT_BY_SOURCE,
    EXPORT_LAYOUT_SINGLE,
    EXPORT_PLACEHOLDER_TODO,
    ExportOptions,
    PendingEntry,
    ProjectConfig,
    WRITE_MODE_NEW_FILE,
)
from tests.test_workflow import _copy_fixtures


def test_default_single_pending_path():
    path = default_single_pending_path(Path(r"C:\Mods\Demo-TC"), "csv")
    assert path.name == "DefInjected-missing.csv"


def test_merge_preserves_partial_translation():
    old = [
        PendingEntry("A", "ThingDef", "label", "src", "半譯", "A.xml"),
    ]
    new = [
        PendingEntry("A", "ThingDef", "label", "src2", "", "A.xml"),
    ]
    merged = merge_pending_entries(new, old, EXPORT_PLACEHOLDER_TODO)
    assert merged[0].translation == "半譯"
    assert merged[0].source_text == "src2"


def test_merge_adds_new_with_placeholder():
    merged = merge_pending_entries(
        [PendingEntry("B", "ThingDef", "label", "hello", "", "B.xml")],
        [],
        EXPORT_PLACEHOLDER_TODO,
    )
    assert merged[0].translation == "TODO"


def test_repeat_export_merge(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    config = ProjectConfig(source, target, "ChineseTraditional")
    options = ExportOptions(fmt="csv")
    first = run_export(config, options)
    assert first.ok
    out = Path(first.output_path)
    rows = out.read_text(encoding="utf-8-sig").splitlines()
    filled = [rows[0]]
    for row in rows[1:]:
        cols = row.split(",")
        if len(cols) >= 5 and cols[0] == "SampleResearch" and cols[2] == "label":
            cols[4] = "範例研究"
        filled.append(",".join(cols))
    out.write_text("\n".join(filled) + "\n", encoding="utf-8-sig")

    second = run_export(config, options)
    assert second.ok
    reloaded = load_entries_csv(out)
    sample = next(e for e in reloaded if e.def_name == "SampleResearch" and e.field == "label")
    assert sample.translation == "範例研究"


def test_by_source_export_writes_definjected(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    config = ProjectConfig(source, target, "ChineseTraditional")
    result = run_export(
        config,
        ExportOptions(layout=EXPORT_LAYOUT_BY_SOURCE, placeholder=EXPORT_PLACEHOLDER_TODO),
    )
    assert result.ok
    di = target / "Languages" / "ChineseTraditional" / "DefInjected"
    assert any(di.rglob("*.xml"))


def test_by_source_skips_bad_xml(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    bad_dir = target / "Languages" / "ChineseTraditional" / "DefInjected" / "ThingDef"
    bad_dir.mkdir(parents=True, exist_ok=True)
    (bad_dir / "Broken.xml").write_text("<LanguageData><unclosed>", encoding="utf-8")
    config = ProjectConfig(source, target, "ChineseTraditional")
    result = run_export(
        config,
        ExportOptions(layout=EXPORT_LAYOUT_BY_SOURCE, placeholder=EXPORT_PLACEHOLDER_TODO),
    )
    assert result.ok
    assert result.warning_keys
