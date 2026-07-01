from __future__ import annotations

import shutil
from pathlib import Path

from core.cli import main as cli_main
from core.fix_src import run_fix_src
from core.models import ProjectConfig

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _setup_unknown_src(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source_mod"
    target = tmp_path / "target_mod"
    shutil.copytree(FIXTURES / "source_mod", source)
    shutil.copytree(FIXTURES / "target_mod", target)
    di = target / "Languages/ChineseTraditional/DefInjected/ThingDef"
    di.mkdir(parents=True, exist_ok=True)
    (di / "NestedWeapon.xml").write_text(
        """<?xml version='1.0' encoding='UTF-8'?>
<LanguageData>

  <!-- SRC tools.stock.label: (unknown) -->
  <NestedGun.tools.stock.label>槍托</NestedGun.tools.stock.label>
  <!-- SRC verbs.Verb_Shoot.label: (unknown) -->
  <NestedGun.verbs.Verb_Shoot.label>巢狀槍</NestedGun.verbs.Verb_Shoot.label>

</LanguageData>
""",
        encoding="utf-8",
    )
    return source, target


def test_fix_src_updates_unknown(tmp_path: Path):
    source, target = _setup_unknown_src(tmp_path)
    config = ProjectConfig(source, target, "ChineseTraditional")
    result = run_fix_src(config)
    assert result.ok
    assert result.fixed_count == 2
    text = (target / "Languages/ChineseTraditional/DefInjected/ThingDef/NestedWeapon.xml").read_text(
        encoding="utf-8"
    )
    assert "<!-- SRC tools.stock.label: stock -->" in text
    assert "<!-- SRC verbs.Verb_Shoot.label: Nested Gun -->" in text


def test_cli_fix_src_dry_run(tmp_path: Path, capsys):
    source, target = _setup_unknown_src(tmp_path)
    code = cli_main(
        [
            "fix-src",
            "--dry-run",
            "--source-mod",
            str(source),
            "--target-mod",
            str(target),
            "--lang",
            "ChineseTraditional",
        ]
    )
    assert code == 0
    text = (target / "Languages/ChineseTraditional/DefInjected/ThingDef/NestedWeapon.xml").read_text(
        encoding="utf-8"
    )
    assert "(unknown)" in text
