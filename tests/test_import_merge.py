from __future__ import annotations

from pathlib import Path

from core.export import run_export
from core.meta import write_meta
from core.models import (
    EXPORT_LAYOUT_BY_SOURCE,
    ExportOptions,
    ProjectConfig,
    WRITE_MODE_MERGE_EXISTING,
)
from tests.test_workflow import _copy_fixtures


def test_import_rejects_by_source_manifest(tmp_path: Path):
    from core.import_merge import run_import

    source, target = _copy_fixtures(tmp_path)
    config = ProjectConfig(source, target, "ChineseTraditional")
    out = target / "DefInjected-missing.csv"
    out.write_text("defName,defType,field,sourceText,translation,sourceDefFile\n", encoding="utf-8-sig")
    write_meta(
        out.with_suffix(out.suffix + ".meta.json"),
        config,
        [],
        "csv",
        layout=EXPORT_LAYOUT_BY_SOURCE,
        import_write_mode=WRITE_MODE_MERGE_EXISTING,
    )
    result = run_import(config=config)
    assert not result.ok
    assert result.error_key == "err.import_by_source_not_supported"


def test_export_skips_translated_in_definjected(tmp_path: Path):
    source, target = _copy_fixtures(tmp_path)
    di = target / "Languages" / "ChineseTraditional" / "DefInjected" / "ResearchProjectDef"
    di.mkdir(parents=True, exist_ok=True)
    (di / "Sample.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
  <SampleResearch.label>已譯</SampleResearch.label>
</LanguageData>
""",
        encoding="utf-8",
    )
    config = ProjectConfig(source, target, "ChineseTraditional")
    result = run_export(config, ExportOptions(fmt="csv"))
    assert result.ok
    text = Path(result.output_path).read_text(encoding="utf-8-sig")
    assert "SampleResearch,ResearchProjectDef,label" not in text
