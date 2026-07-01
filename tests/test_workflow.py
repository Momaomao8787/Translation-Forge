from __future__ import annotations

import shutil
from pathlib import Path

from core.export import run_export
from core.import_merge import load_entries_xml, run_import
from core.models import ExportOptions, ProjectConfig, WRITE_MODE_NEW_FILE
from core.prefix import default_prefix
from core.paths import discover_defs_roots
from core.scan import build_def_map, run_check

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _copy_fixtures(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source_mod"
    target = tmp_path / "target_mod"
    shutil.copytree(FIXTURES / "source_mod", source)
    shutil.copytree(FIXTURES / "target_mod", target)
    return source, target


def test_check_rejects_empty_mod_paths():
    config = ProjectConfig(Path(""), Path(""), "ChineseTraditional")
    result = run_check(config)
    assert not result.ok
    assert result.error_key == "err.specify_source_mod"


def test_default_prefix():
    assert default_prefix("Monolyn Race") == "Monolyn_Race"


def test_check_finds_defs_and_pending(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    config = ProjectConfig(source, target, "ChineseTraditional")
    result = run_check(config)
    assert result.ok
    assert result.pending_count >= 2


def test_same_def_name_different_type_not_duplicate(tmp_path: Path):
    source = tmp_path / "source_mod"
    defs_dir = source / "Defs"
    defs_dir.mkdir(parents=True)
    (defs_dir / "Mixed.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>SharedName</defName>
    <label>Thing label</label>
  </ThingDef>
  <AbilityDef>
    <defName>SharedName</defName>
    <label>Ability label</label>
  </AbilityDef>
</Defs>
""",
        encoding="utf-8",
    )
    def_map, duplicate = build_def_map(source, discover_defs_roots(source))
    assert len(def_map) == 2
    assert duplicate == []


def test_export_csv_and_import(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    out = tmp_path / "target_mod" / "DefInjected-missing.csv"
    config = ProjectConfig(source, target, "ChineseTraditional")
    export_result = run_export(config, ExportOptions(fmt="csv"))
    assert export_result.ok
    assert export_result.entry_count >= 2

    lines = out.read_text(encoding="utf-8-sig").strip().splitlines()
    updated = [lines[0]]
    for row in lines[1:]:
        parts = row.split(",")
        if len(parts) >= 5 and parts[0] == "SampleResearch":
            parts[4] = "範例研究" if parts[2] == "label" else "研究說明"
        updated.append(",".join(parts))
    out.write_text("\n".join(updated) + "\n", encoding="utf-8-sig")

    import_result = run_import(out, use_prefix=False, prefix="")
    assert import_result.ok
    assert import_result.written + import_result.updated >= 1

    merged = target / "Languages/ChineseTraditional/DefInjected/ResearchProjectDef/Sample.xml"
    assert merged.is_file()
    merged_text = merged.read_text(encoding="utf-8")
    assert "範例研究" in merged_text
    assert "<!-- SRC label:" in merged_text


def test_export_xml_has_src_comments(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    out = target / "DefInjected-missing.xml"
    config = ProjectConfig(source, target, "ChineseTraditional")
    assert run_export(config, ExportOptions(fmt="xml"), out).ok
    text = out.read_text(encoding="utf-8")
    assert "<!-- SRC label:" in text
    assert "<!-- SRC description:" in text
    assert "RDT" not in text


def test_import_xml_with_en_comments(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    config = ProjectConfig(source, target, "ChineseTraditional")
    out = target / "DefInjected-missing.xml"
    assert run_export(config, ExportOptions(fmt="xml"), out).ok

    lines = out.read_text(encoding="utf-8").splitlines()
    converted = []
    for line in lines:
        if "<!-- SRC " in line:
            converted.append(line.replace("<!-- SRC ", "<!-- EN ", 1))
        elif "<SampleResearch.label>" in line:
            converted.append("  <SampleResearch.label>範例研究</SampleResearch.label>")
        elif "<SampleResearch.description>" in line:
            converted.append("  <SampleResearch.description>研究說明</SampleResearch.description>")
        else:
            converted.append(line)
    out.write_text("\n".join(converted) + "\n", encoding="utf-8")

    entries = load_entries_xml(out)
    assert any(e.def_name == "SampleResearch" and e.source_text for e in entries)

    result = run_import(out, use_prefix=False, prefix="")
    assert result.ok
    merged = target / "Languages/ChineseTraditional/DefInjected/ResearchProjectDef/Sample.xml"
    merged_text = merged.read_text(encoding="utf-8")
    assert "<!-- SRC label:" in merged_text
    assert "範例研究" in merged_text


def test_update_empty_tag_adds_src(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    di_file = target / "Languages/ChineseTraditional/DefInjected/ResearchProjectDef/Sample.xml"
    di_file.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>

  <SampleResearch.label></SampleResearch.label>

</LanguageData>
""",
        encoding="utf-8",
    )

    out = tmp_path / "target_mod" / "DefInjected-missing.csv"
    config = ProjectConfig(source, target, "ChineseTraditional")
    assert run_export(config, ExportOptions(fmt="csv"), out).ok

    rows = out.read_text(encoding="utf-8-sig").splitlines()
    filled = [rows[0]]
    for row in rows[1:]:
        cols = row.split(",")
        if len(cols) >= 5 and cols[0] == "SampleResearch" and cols[2] == "label":
            cols[4] = "範例研究"
        filled.append(",".join(cols))
    out.write_text("\n".join(filled) + "\n", encoding="utf-8-sig")

    result = run_import(out, use_prefix=False, prefix="")
    assert result.ok
    assert result.updated >= 1
    merged_text = di_file.read_text(encoding="utf-8")
    assert "<!-- SRC label:" in merged_text
    assert "範例研究" in merged_text


def test_import_prefix_file(tmp_path: Path):
    source, _ = _copy_fixtures(tmp_path)
    work_target = tmp_path / "target_tc"
    work_target.mkdir()
    config = ProjectConfig(source, work_target, "ChineseTraditional")
    out = work_target / "DefInjected-missing.csv"
    assert run_export(config, ExportOptions(fmt="csv"), out).ok

    rows = out.read_text(encoding="utf-8-sig").splitlines()
    filled = [rows[0]]
    for row in rows[1:]:
        cols = row.split(",")
        if len(cols) >= 5:
            cols[4] = "譯文"
        filled.append(",".join(cols))
    out.write_text("\n".join(filled) + "\n", encoding="utf-8-sig")

    result = run_import(out, write_mode=WRITE_MODE_NEW_FILE, prefix="Demo")
    assert result.ok
    assert (work_target / "Languages/ChineseTraditional/DefInjected/ThingDef/Demo_Sample.xml").is_file()


def test_nested_export_and_import(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    config = ProjectConfig(source, target, "ChineseTraditional")
    result = run_check(config)
    assert result.ok
    assert result.pending_count >= 5

    out = target / "DefInjected-missing.xml"
    export_result = run_export(config, ExportOptions(fmt="xml"), out)
    assert export_result.ok
    text = out.read_text(encoding="utf-8")
    assert "<!-- SRC tools.stock.label: stock -->" in text
    assert "<!-- SRC verbs.Verb_Shoot.label: Nested Gun -->" in text
    assert "<!-- SRC comps.CompRefuelable.fuelLabel: Wood left -->" in text

    lines = text.splitlines()
    converted = []
    for line in lines:
        if "<NestedGun.tools.stock.label>" in line:
            converted.append("  <NestedGun.tools.stock.label>槍托</NestedGun.tools.stock.label>")
        elif "<NestedGun.verbs.Verb_Shoot.label>" in line:
            converted.append("  <NestedGun.verbs.Verb_Shoot.label>巢狀槍</NestedGun.verbs.Verb_Shoot.label>")
        else:
            converted.append(line)
    out.write_text("\n".join(converted) + "\n", encoding="utf-8")

    import_result = run_import(out, use_prefix=False, prefix="")
    assert import_result.ok
    merged = target / "Languages/ChineseTraditional/DefInjected/ThingDef/NestedWeapon.xml"
    assert merged.is_file()
    merged_text = merged.read_text(encoding="utf-8")
    assert "槍托" in merged_text
    assert "<!-- SRC tools.stock.label:" in merged_text
