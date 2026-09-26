from __future__ import annotations

from pathlib import Path

import pytest

from core.about_template import (
    build_about_fields,
    default_description,
    default_package_id,
    read_published_file_id,
    read_source_about,
    workshop_url_from_file_id,
)
from core.models import ProjectConfig, ScaffoldOptions
from core.path_suggest import (
    default_rimworld_mods_dir,
    default_user_mods_dir,
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
    assert suggest_folder_name(source, "ChineseTraditional") == "Monolyn Race TC"


def test_suggest_target_collision(tmp_path: Path, monkeypatch):
    user_mods = tmp_path / "Rimworld Mod"
    user_mods.mkdir()
    monkeypatch.setattr(
        "core.path_suggest.default_user_mods_dir",
        lambda *, create=True: user_mods,
    )
    source = tmp_path / "source"
    source.mkdir()
    (source / "About").mkdir()
    (source / "About" / "About.xml").write_text(
        "<ModMetaData><name>Demo</name><packageId>Demo.Mod</packageId></ModMetaData>",
        encoding="utf-8",
    )
    (user_mods / "Demo TC").mkdir()
    path, name = suggest_target_mod_path(source, "ChineseTraditional")
    assert path.parent == user_mods
    assert name == "Demo TC-2"


def test_validate_scaffold_target_blocks_same_path(tmp_path: Path):
    source = tmp_path / "mod"
    source.mkdir()
    assert validate_scaffold_target(source, source) == "err.scaffold_target_same_as_source"


def test_default_package_id(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "About").mkdir()
    (source / "About" / "About.xml").write_text(
        "<ModMetaData><name>Monolyn Race</name><packageId>ASEL.MonolynRace</packageId></ModMetaData>",
        encoding="utf-8",
    )
    assert default_package_id(source, "ChineseTraditional") == "MonolynRace.TC"


def test_default_package_id_from_long_title(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "About").mkdir()
    (source / "About" / "About.xml").write_text(
        """<ModMetaData>
<name>Kurin, The Three Tailed Fox [Deluxe Edition]</name>
<packageId>Inoshishi3.KTTFDE</packageId>
</ModMetaData>""",
        encoding="utf-8",
    )
    assert default_package_id(source, "ChineseTraditional") == "KurinTheThreeTailedFoxDeluxeEdition.TC"
    assert default_package_id(source, "ChineseSimplified") == "KurinTheThreeTailedFoxDeluxeEdition.ZH"


def test_default_package_id_ignores_source_pid(tmp_path: Path):
    source = tmp_path / "Ratkin Underground+"
    source.mkdir()
    (source / "About").mkdir()
    (source / "About" / "About.xml").write_text(
        """<ModMetaData>
<name>Ratkin Underground+</name>
<packageId>RKU.RatkinUnderground</packageId>
</ModMetaData>""",
        encoding="utf-8",
    )
    assert default_package_id(source, "ChineseTraditional") == "RatkinUnderground.TC"


def test_default_package_id_invalid_suffix_override_falls_back_to_lang(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "About").mkdir()
    (source / "About" / "About.xml").write_text(
        "<ModMetaData><name>Kurin Fox</name></ModMetaData>",
        encoding="utf-8",
    )
    assert default_package_id(source, "ChineseTraditional", ".") == "KurinFox.TC"


def test_build_about_fields_depends_only_on_source_with_workshop_url(tmp_path: Path):
    source = tmp_path / "source_mod"
    target = tmp_path / "target_mod"
    about = source / "About"
    about.mkdir(parents=True)
    (about / "About.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <name>Demo Mod</name>
  <packageId>Demo.Mod</packageId>
  <supportedVersions><li>1.6</li></supportedVersions>
  <modDependencies>
    <li>
      <packageId>brrainz.harmony</packageId>
      <displayName>Harmony</displayName>
      <steamWorkshopUrl>steam://url/CommunityFilePage/2009463077</steamWorkshopUrl>
    </li>
  </modDependencies>
</ModMetaData>""",
        encoding="utf-8",
    )
    (about / "PublishedFileId.txt").write_text("1234567890\n", encoding="utf-8")
    target.mkdir()
    fields = build_about_fields(source, target, "ChineseTraditional")
    deps = fields["modDependencies"]
    assert len(deps) == 1
    assert deps[0]["packageId"] == "Demo.Mod"
    assert deps[0]["displayName"] == "Demo Mod"
    assert deps[0]["steamWorkshopUrl"] == "steam://url/CommunityFilePage/1234567890"
    assert fields["loadAfter"] == ["Demo.Mod"]


def test_read_published_file_id_falls_back_to_workshop_folder(tmp_path: Path):
    root = tmp_path / "steamapps" / "workshop" / "content" / "294100" / "99887766"
    about = root / "About"
    about.mkdir(parents=True)
    (about / "About.xml").write_text(
        "<ModMetaData><name>X</name><packageId>X.Mod</packageId></ModMetaData>",
        encoding="utf-8",
    )
    assert read_published_file_id(root) == "99887766"
    assert workshop_url_from_file_id("99887766") == "steam://url/CommunityFilePage/99887766"


def test_default_description():
    assert default_description("ChineseTraditional") == "本模組使用「魔貓貓的翻譯鍛造台」協助完成"
    assert default_description("ChineseSimplified") == "本模组使用「魔猫猫的翻译锻造台」协助完成"
    assert default_description("English") == "This mod was created with Momaomao's Translation Forge"
    assert "この Mod は" in default_description("Japanese")


def test_scaffold_about_description_localized(tmp_path: Path):
    source = tmp_path / "source_mod"
    target = tmp_path / "target_mod"
    import shutil

    shutil.copytree(FIXTURES / "source_mod", source)
    config = ProjectConfig(source, target, "Japanese")
    result = run_scaffold(config, ScaffoldOptions(create_about=True))
    assert result.ok
    about_text = (target / "About" / "About.xml").read_text(encoding="utf-8")
    assert default_description("Japanese") in about_text


def test_scaffold_run_creates_about_and_dirs(tmp_path: Path):
    source = tmp_path / "source_mod"
    target = tmp_path / "target_mod"
    import shutil

    shutil.copytree(FIXTURES / "source_mod", source)
    config = ProjectConfig(source, target, "ChineseTraditional")
    options = ScaffoldOptions(create_about=True)
    result = run_scaffold(config, options, app_title="Momaomao's Translation Forge")
    assert result.ok
    about_path = target / "About" / "About.xml"
    assert about_path.is_file()
    assert default_description("ChineseTraditional") in about_path.read_text(encoding="utf-8")
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


def test_default_user_mods_dir_creates_folder(tmp_path: Path, monkeypatch):
    docs = tmp_path / "Documents"
    docs.mkdir()
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    root = default_user_mods_dir()
    assert root == docs / "Rimworld Mod"
    assert root.is_dir()


def test_default_rimworld_mods_dir_prefers_steam_path(monkeypatch, tmp_path: Path):
    fake = tmp_path / "Steam" / "steamapps" / "common" / "RimWorld" / "Mods"
    fake.mkdir(parents=True)
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path))
    assert default_rimworld_mods_dir() == fake
