from __future__ import annotations

import json
from pathlib import Path

from core.cli import main as cli_main
from tests.test_workflow import _copy_fixtures


def _scaffold_argv(source: Path, target: Path, **extra: str) -> list[str]:
    argv = [
        "scaffold",
        "--source-mod",
        str(source),
        "--target-mod",
        str(target),
        "--lang",
        "ChineseTraditional",
    ]
    for key, value in extra.items():
        if value is True:
            argv.append(f"--{key.replace('_', '-')}")
        elif value is False:
            argv.append(f"--no-{key.replace('_', '-')}")
        elif value:
            argv.extend([f"--{key.replace('_', '-')}", str(value)])
    return argv


def test_cli_scaffold_run_creates_files(tmp_path: Path, capsys):
    source, _target = _copy_fixtures(tmp_path)
    target = tmp_path / "scaffold_target"
    code = cli_main(_scaffold_argv(source, target))
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert (target / "About" / "About.xml").is_file()
    assert (target / "Languages" / "ChineseTraditional" / "DefInjected").is_dir()
    assert data["entries_written"] == 0


def test_cli_scaffold_same_source_target_fails(tmp_path: Path, capsys):
    source, _target = _copy_fixtures(tmp_path)
    code = cli_main(_scaffold_argv(source, source))
    assert code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert data["error_key"] == "err.scaffold_target_same_as_source"


def test_cli_scaffold_no_create_about(tmp_path: Path, capsys):
    source, _target = _copy_fixtures(tmp_path)
    target = tmp_path / "scaffold_target"
    code = cli_main(_scaffold_argv(source, target, create_about=False))
    assert code == 0
    json.loads(capsys.readouterr().out)
    assert not (target / "About" / "About.xml").is_file()
    assert (target / "Languages" / "ChineseTraditional" / "DefInjected").is_dir()
