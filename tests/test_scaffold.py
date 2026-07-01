from __future__ import annotations

from pathlib import Path

import pytest

from core.about_template import default_package_id, read_source_about
from core.models import ProjectConfig, ScaffoldOptions
from core.path_suggest import (
    default_rimworld_mods_dir,
    lang_package_suffix,
    suggest_folder_name,
    suggest_target_mod_path,
    validate_scaffold_target,
)
from core.scaffold import run_scaffold
from tests.test_workflow import FIXTURES


def test_lang_package_suffix():
    assert lang_package_suffix("ChineseTraditional") == "TC"
    assert lang_package_suffix("ChineseSimplified") == "ZH"
    assert lang_package_suffix("Japanese") == "JP"


def test_suggest_folder_name_strips_suffix(tmp_path: Path):
    source = tmp_path / "Monolyn Race-TC"
    source.mkdir()
    (source / "About").mkdir()
    (source / "About" / "About.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<ModMetaData><name>Monolyn Race</name><packageId>ASEL.MonolynRace</packageId></ModMetaData>""",
        encoding="utf-8",
    )
    assert suggest_folder_name(source, "ChineseTraditional") == "Monolyn Race-TC"


def test_suggest_target_collision(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "core.path_suggest.default_rimworld_mods_dir",
        lambda: None,
    )
    mods = tmp_path / "Mods"
    mods.mkdir()
    source = mods / "source"
    source.mkdir()
    (source / "About").mkdir()
    (source / "About" / "About.xml").write_text(
        "<ModMetaData><name>Demo</name><packageId>Demo.Mod</packageId></ModMetaData>",
        encoding="utf-8",
    )
    (mods / "Demo-TC").mkdir()
    path, name = suggest_target_mod_path(source, "ChineseTraditional")
    assert path.parent == mods
    assert name == "Demo-TC-2"


def test_validate_scaffold_target_blocks_same_path(tmp_path: Path):
    source = tmp_path / "mod"
    source.mkdir()
    assert validate_scaffold_target(source, source) == "err.scaffold_target_same_as_source"


def test_default_package_id(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "About").mkdir()
    (source / "About" / "About.xml").write_text(
        "<ModMetaData><packageId>ASEL.MonolynRace</packageId></ModMetaData>",
        encoding="utf-8",
    )
    assert default_package_id(source, "ChineseTraditional") == "ASEL.MonolynRace.TC"


def test_scaffold_run_creates_about_and_dirs(tmp_path: Path):
    source = tmp_path / "source_mod"
    target = tmp_path / "target_mod"
    import shutil

    shutil.copytree(FIXTURES / "source_mod", source)
    config = ProjectConfig(source, target, "ChineseTraditional")
    options = ScaffoldOptions(create_about=True)
    result = run_scaffold(config, options, app_title="Momaomao's Translation Forge")
    assert result.ok
    assert (target / "About" / "About.xml").is_file()
    assert (target / "Languages" / "ChineseTraditional" / "DefInjected").is_dir()
    assert result.entries_written == 0


def test_scaffold_warns_existing_lang(tmp_path: Path):
    source = tmp_path / "source_mod"
    target = tmp_path / "target_mod"
    import shutil

    shutil.copytree(FIXTURES / "source_mod", source)
    lang = target / "Languages" / "ChineseTraditional"
    lang.mkdir(parents=True)
    config = ProjectConfig(source, target, "ChineseTraditional")
    result = run_scaffold(config, ScaffoldOptions(create_about=False))
    assert result.ok
    assert any("existing_lang" in key for key, _ in result.warning_keys)


def test_default_rimworld_mods_dir_prefers_steam_path(monkeypatch, tmp_path: Path):
    fake = tmp_path / "Steam" / "steamapps" / "common" / "RimWorld" / "Mods"
    fake.mkdir(parents=True)
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path))
    assert default_rimworld_mods_dir() == fake
