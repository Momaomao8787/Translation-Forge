from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.def_inherit import build_def_index
from core.fix_src import run_fix_src
from core.models import ProjectConfig
from core.paths import discover_defs_roots, load_folders, resolve_game_version
from core.scan import run_check, scan_pending
from core.stale_keys import find_stale_keys


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _about(mod: Path, *versions: str) -> None:
    items = "".join(f"<li>{v}</li>" for v in versions)
    _write(mod / "About" / "About.xml", f"<ModMetaData><supportedVersions>{items}</supportedVersions></ModMetaData>")


def _rel(mod: Path, paths: list[Path]) -> list[str]:
    return [p.relative_to(mod).as_posix() or "." for p in paths]


def test_load_folders_without_xml_prefers_exact_version(tmp_path: Path):
    for name in ("1.5", "1.6", "Common"):
        (tmp_path / name).mkdir()
    _about(tmp_path, "1.5", "1.6")
    assert _rel(tmp_path, load_folders(tmp_path, (1, 6))) == ["1.6", "Common", "."]
    assert _rel(tmp_path, load_folders(tmp_path, (1, 5))) == ["1.5", "Common", "."]


def test_load_folders_without_xml_falls_back_to_highest_older_version(tmp_path: Path):
    for name in ("1.4", "1.5"):
        (tmp_path / name).mkdir()
    assert _rel(tmp_path, load_folders(tmp_path, (1, 6))) == ["1.5", "."]
    assert _rel(tmp_path, load_folders(tmp_path, (1, 3))) == ["1.4", "."]


def test_load_folders_xml_exact_older_and_default(tmp_path: Path):
    _write(
        tmp_path / "LoadFolders.xml",
        """<loadFolders>
  <v1.5><li>/</li><li>1.5</li></v1.5>
  <v1.6><li>/</li><li>1.6</li><li IfModActive="Ludeon.RimWorld.Royalty">Mods/Royalty</li></v1.6>
  <default><li>Legacy</li></default>
</loadFolders>""",
    )
    assert _rel(tmp_path, load_folders(tmp_path, (1, 6))) == [".", "1.6", "Mods/Royalty"]
    assert _rel(tmp_path, load_folders(tmp_path, (1, 7))) == [".", "1.6", "Mods/Royalty"]
    assert _rel(tmp_path, load_folders(tmp_path, (1, 4))) == ["Legacy"]


def test_discover_defs_roots_uses_version_for_mod_root(tmp_path: Path):
    _about(tmp_path, "1.6")
    for name in ("1.5", "1.6"):
        _write(tmp_path / name / "Defs" / "a.xml", "<Defs/>")
    assert _rel(tmp_path, discover_defs_roots(tmp_path, (1, 6))) == ["1.6/Defs"]


def test_discover_defs_roots_scans_everything_for_plain_folder(tmp_path: Path):
    for name in ("1.5", "1.6"):
        _write(tmp_path / name / "Defs" / "a.xml", "<Defs/>")
    assert _rel(tmp_path, discover_defs_roots(tmp_path, (1, 6))) == ["1.5/Defs", "1.6/Defs"]


def test_resolve_game_version_prefers_explicit_then_target(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _about(source, "1.5", "1.6")
    _about(target, "1.5")
    assert resolve_game_version("1.6", target, source) == (1, 6)
    assert resolve_game_version("", target, source) == (1, 5)
    assert resolve_game_version("", tmp_path / "missing", source) == (1, 6)


INHERIT_DEFS = """<Defs>
  <ThingDef Name="BaseBlade" Abstract="True">
    <description>base</description>
    <tools>
      <li><label>point</label></li>
    </tools>
    <comps>
      <li Class="CompProperties_Refuelable"><fuelLabel>Qi</fuelLabel></li>
    </comps>
  </ThingDef>
  <ThingDef ParentName="BaseBlade">
    <defName>Blade</defName>
    <tools>
      <li><label>edge</label></li>
    </tools>
  </ThingDef>
  <ThingDef ParentName="BaseBlade">
    <defName>Club</defName>
    <tools Inherit="False">
      <li><label>head</label></li>
    </tools>
  </ThingDef>
  <ThingDef ParentName="CoreBaseWeapon">
    <defName>Gun</defName>
    <tools>
      <li><label>stock</label></li>
    </tools>
  </ThingDef>
  <WorkGiverDef>
    <defName>FillStove</defName>
    <label>fill stove</label>
  </WorkGiverDef>
</Defs>"""


def _stale(tmp_path: Path, entries: dict[str, str], patch_text: str = "") -> list[str]:
    defs = tmp_path / "Defs"
    _write(defs / "Things.xml", INHERIT_DEFS)
    di = tmp_path / "DefInjected"
    for folder, body in entries.items():
        _write(di / folder / "Things.xml", f"<LanguageData>{body}</LanguageData>")
    return find_stale_keys(di, build_def_index([defs]), patch_text)


def test_inherited_list_items_are_appended_after_parent(tmp_path: Path):
    defs = tmp_path / "Defs"
    _write(defs / "Things.xml", INHERIT_DEFS)
    index = build_def_index([defs])
    (_, blade), = index.candidates("Blade")
    resolved, complete = index.resolved(blade)
    assert complete
    assert [li.findtext("label") for li in resolved.find("tools")] == ["point", "edge"]
    assert resolved.findtext("description") == "base"
    (_, club), = index.candidates("Club")
    club_tools = index.resolved(club)[0].find("tools")
    assert [li.findtext("label") for li in club_tools] == ["head"]
    assert "Inherit" not in club_tools.attrib


def test_inherit_false_keeps_parent_attributes(tmp_path: Path):
    defs = tmp_path / "Defs"
    _write(defs / "a.xml", """<Defs>
  <ThingDef Name="Base" Abstract="True"><graphicData Class="GraphicData_Base"><texPath>a</texPath></graphicData></ThingDef>
  <ThingDef ParentName="Base"><defName>Kid</defName><graphicData Inherit="False"><texPath>b</texPath></graphicData></ThingDef>
</Defs>""")
    index = build_def_index([defs])
    (_, kid), = index.candidates("Kid")
    graphic = index.resolved(kid)[0].find("graphicData")
    assert graphic.attrib == {"Class": "GraphicData_Base"}
    assert graphic.findtext("texPath") == "b"


def test_stale_keys_accept_inherited_fields(tmp_path: Path):
    stale = _stale(tmp_path, {
        "ThingDef": "<Blade.tools.1.label>刃</Blade.tools.1.label>"
                    "<Blade.tools.point.label>尖</Blade.tools.point.label>"
                    "<Blade.comps.CompRefuelable.fuelLabel>氣</Blade.comps.CompRefuelable.fuelLabel>",
    })
    assert stale == []


def test_stale_keys_flag_removed_defs_and_fields(tmp_path: Path):
    stale = _stale(tmp_path, {
        "ThingDef": "<OldBlade.label>舊</OldBlade.label>"
                    "<Blade.tools.2.label>多</Blade.tools.2.label>"
                    "<Club.tools.point.label>尖</Club.tools.point.label>",
    })
    assert stale == [
        "ThingDef/Things.xml: OldBlade.label",
        "ThingDef/Things.xml: Blade.tools.2.label",
        "ThingDef/Things.xml: Club.tools.point.label",
    ]


def test_stale_keys_flag_type_mismatch(tmp_path: Path):
    stale = _stale(tmp_path, {
        "JobDef": "<FillStove.reportString>填充</FillStove.reportString>",
        "WorkGiverDef": "<FillStove.label>填充</FillStove.label>",
    })
    assert stale == ["JobDef/Things.xml: FillStove.reportString"]


def test_stale_keys_skip_unverifiable_cases(tmp_path: Path):
    stale = _stale(
        tmp_path,
        {"ThingDef": "<Gun.tools.3.label>托</Gun.tools.3.label><PatchedThing.label>補</PatchedThing.label>"},
        patch_text="<xpath>Defs/ThingDef[defName=\"PatchedThing\"]</xpath>",
    )
    assert stale == []


def test_stale_keys_accept_har_subclass_folders(tmp_path: Path):
    defs = tmp_path / "Defs"
    _write(defs / "Race.xml", """<Defs>
  <AlienRace.ThingDef_AlienRace><defName>Alien</defName><label>alien</label></AlienRace.ThingDef_AlienRace>
  <AlienRace.AlienBackstoryDef><defName>Kid</defName><title>kid</title></AlienRace.AlienBackstoryDef>
</Defs>""")
    di = tmp_path / "DefInjected"
    _write(di / "ThingDef" / "a.xml", "<LanguageData><Alien.label>異</Alien.label></LanguageData>")
    _write(di / "BackstoryDef" / "b.xml", "<LanguageData><Kid.title>童</Kid.title></LanguageData>")
    assert find_stale_keys(di, build_def_index([defs])) == []


def _inherit_project(tmp_path: Path, translations: str) -> tuple[Path, Path]:
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write(source / "Defs" / "Things.xml", INHERIT_DEFS)
    _write(
        target / "Languages" / "ChineseTraditional" / "DefInjected" / "ThingDef" / "Things.xml",
        f"<LanguageData>{translations}</LanguageData>",
    )
    return source, target


def test_scan_pending_includes_inherited_fields(tmp_path: Path):
    source, target = _inherit_project(tmp_path, "<Blade.tools.1.label>刃</Blade.tools.1.label>")
    pending, def_map, *_ = scan_pending(ProjectConfig(source, target, "ChineseTraditional"))
    blade = {(p.field, p.source_text) for p in pending if p.def_name == "Blade"}
    assert blade == {
        ("description", "base"),
        ("tools.point.label", "point"),
        ("comps.0.fuelLabel", "Qi"),
    }
    club = {p.field for p in pending if p.def_name == "Club"}
    assert club == {"description", "tools.head.label", "comps.0.fuelLabel"}
    assert ("ThingDef", "BaseBlade") not in {(r.def_type, r.def_name) for r in def_map.values()}


def test_inherited_def_keeps_child_type(tmp_path: Path):
    defs = tmp_path / "Defs"
    _write(defs / "Race.xml", """<Defs>
  <ThingDef Name="BasePawnLike" Abstract="True"><description>pawn</description></ThingDef>
  <AlienRace.ThingDef_AlienRace ParentName="BasePawnLike"><defName>Alien</defName><label>alien</label></AlienRace.ThingDef_AlienRace>
</Defs>""")
    index = build_def_index([defs])
    (def_type, node), = index.candidates("Alien")
    assert def_type == "AlienRace.ThingDef_AlienRace"
    assert index.resolved(node)[0].tag == "AlienRace.ThingDef_AlienRace"


ABSTRACT_WITH_DEFNAME = """<Defs>
  <PawnKindDef Name="BaseCourier" Abstract="True">
    <defName>Courier</defName>
    <label>courier</label>
  </PawnKindDef>
  <PawnKindDef ParentName="BaseCourier"><defName>Courier_Colonist</defName></PawnKindDef>
</Defs>"""


def test_abstract_def_with_def_name_is_not_a_def(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write(source / "Defs" / "Kinds.xml", ABSTRACT_WITH_DEFNAME)
    _write(
        target / "Languages" / "ChineseTraditional" / "DefInjected" / "PawnKindDef" / "Kinds.xml",
        "<LanguageData><Courier.label>信使</Courier.label></LanguageData>",
    )
    index = build_def_index([source / "Defs"])
    assert index.candidates("Courier") == []
    assert [name for _, name, _ in index.def_nodes()] == ["Courier_Colonist"]
    pending, *_ = scan_pending(ProjectConfig(source, target, "ChineseTraditional"))
    assert [(p.def_name, p.field, p.source_text) for p in pending] == [("Courier_Colonist", "label", "courier")]
    result = run_check(ProjectConfig(source, target, "ChineseTraditional"))
    assert result.stale_keys == ["PawnKindDef/Kinds.xml: Courier.label"]


def test_fix_src_resolves_inherited_text(tmp_path: Path):
    source, target = _inherit_project(
        tmp_path,
        "\n  <!-- SRC description: (unknown) -->\n  <Blade.description>基底</Blade.description>\n",
    )
    result = run_fix_src(ProjectConfig(source, target, "ChineseTraditional"))
    assert result.fixed_count == 1
    text = (target / "Languages" / "ChineseTraditional" / "DefInjected" / "ThingDef" / "Things.xml").read_text(encoding="utf-8")
    assert "<!-- SRC description: base -->" in text


def test_run_check_reports_stale_keys_for_target_version(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _about(source, "1.5", "1.6")
    _about(target, "1.6")
    _write(source / "1.5" / "Defs" / "a.xml", "<Defs><ThingDef><defName>Old</defName><label>old</label></ThingDef></Defs>")
    _write(source / "1.6" / "Defs" / "a.xml", "<Defs><ThingDef><defName>New</defName><label>new</label></ThingDef></Defs>")
    _write(
        target / "Languages" / "ChineseTraditional" / "DefInjected" / "ThingDef" / "a.xml",
        "<LanguageData><Old.label>舊</Old.label><New.label>新</New.label></LanguageData>",
    )
    config = ProjectConfig(source, target, "ChineseTraditional")
    result = run_check(config)
    assert result.ok
    assert result.pending_count == 0
    assert result.stale_keys == ["ThingDef/a.xml: Old.label"]
    assert any(key == "msg.check.stale_keys" for key, _ in result.warning_keys)
    legacy = run_check(ProjectConfig(source, target, "ChineseTraditional", game_version="1.5"))
    assert legacy.stale_keys == ["ThingDef/a.xml: New.label"]
    _write(source / "1.5" / "Defs" / "b.xml", "<Defs><ThingDef><defName>Extra</defName><label>x</label></ThingDef></Defs>")
    pending, *_ = scan_pending(ProjectConfig(source, target, "ChineseTraditional", game_version="1.5"))
    assert [(p.def_name, p.field) for p in pending] == [("Extra", "label")]
