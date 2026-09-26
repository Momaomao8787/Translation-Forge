from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from core.field_collect import collect_fields
from core.field_path import normalized_handle
from core.field_resolve import index_path, resolve_field_text
from core.list_segment import for_list_item, list_items
from core.models import ProjectConfig
from core.scan import scan_pending

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "source_mod" / "Defs"

WEAPON = """
<ThingDef>
  <defName>Axolotl_Crossbow</defName>
  <label>MoeLotl Crossbow</label>
  <verbs>
    <li><verbClass>Axolotl.Verb_LotlQiIntensifyShoot</verbClass></li>
  </verbs>
  <comps>
    <li><compClass>Axolotl.CompAxolotlEnergy</compClass><fuelLabel>Qi</fuelLabel></li>
  </comps>
  <tools>
    <li><label>Left Fist</label></li>
    <li><label>handle</label></li>
    <li><label>handle</label></li>
    <li><label>萌螈尾巴</label></li>
  </tools>
</ThingDef>"""

THOUGHT = """
<ThoughtDef>
  <defName>Axolotl_WearSlaveApparel</defName>
  <stages>
    <li><label>Wear Slave Outfit</label><description>a</description></li>
    <li><label>Wear Slave Outfit</label><description>b</description></li>
  </stages>
</ThoughtDef>"""

BODY = """
<BodyDef>
  <defName>Axolotl</defName>
  <corePart>
    <def>Torso</def>
    <parts>
      <li><def>Axolotl_Gill</def><customLabel>left gill</customLabel></li>
      <li><def>Axolotl_Gill</def><customLabel>right gill</customLabel></li>
      <li><def>Stomach</def></li>
    </parts>
  </corePart>
</BodyDef>"""


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Left Fist", "Left_Fist"),
        ("Axolotl.Verb_LotlQiIntensifyShoot", "AxolotlVerb_LotlQiIntensifyShoot"),
        ("stab-blade", "stabblade"),
        ("  a   b  ", "a_b"),
        ("{0} fist", "fist"),
        ("123", "_123"),
        ("萌螈尾巴", ""),
    ],
)
def test_normalized_handle_matches_rimworld(raw: str, expected: str):
    assert normalized_handle(raw) == expected


def test_collect_uses_case_preserving_tool_handles():
    fields = collect_fields(ET.fromstring(WEAPON))
    assert "tools.Left_Fist.label" in fields
    assert "tools.left_fist.label" not in fields


def test_collect_indexes_duplicate_tool_handles():
    fields = collect_fields(ET.fromstring(WEAPON))
    assert fields["tools.handle-0.label"] == "handle"
    assert fields["tools.handle-1.label"] == "handle"


def test_collect_falls_back_to_index_for_non_ascii_label():
    fields = collect_fields(ET.fromstring(WEAPON))
    assert fields["tools.3.label"] == "萌螈尾巴"


def test_collect_uses_short_type_names():
    fields = collect_fields(ET.fromstring(WEAPON))
    assert fields["verbs.Verb_LotlQiIntensifyShoot.label"] == "MoeLotl Crossbow"
    assert fields["comps.CompAxolotlEnergy.fuelLabel"] == "Qi"
    assert not any(".Axolotl." in f for f in fields)


def test_body_part_segment_keeps_custom_label_case():
    body = ET.fromstring(BODY.replace("left gill", "Left Gill"))
    items = list_items(body.find("corePart/parts"))
    segments = [for_list_item(li, ["corePart", "parts"], "BodyDef", items) for li in items]
    assert segments == ["Left_Gill", "right_gill", "Stomach"]


@pytest.mark.parametrize(
    "key",
    ["tools.0.label", "tools.Left_Fist.label", "Tools.0.Label"],
)
def test_index_path_accepts_equivalent_tool_keys(key: str):
    assert index_path(ET.fromstring(WEAPON), "ThingDef", key) == "tools.0.label"


def test_index_path_is_case_sensitive_for_handles():
    assert index_path(ET.fromstring(WEAPON), "ThingDef", "tools.left_fist.label") is None


@pytest.mark.parametrize(
    "key",
    [
        "verbs.0.label",
        "verbs.Verb_LotlQiIntensifyShoot.label",
        "verbs.AxolotlVerb_LotlQiIntensifyShoot.label",
    ],
)
def test_index_path_accepts_type_handles(key: str):
    assert index_path(ET.fromstring(WEAPON), "ThingDef", key) == "verbs.0.label"


def test_index_path_rejects_namespaced_type_segment():
    assert index_path(ET.fromstring(WEAPON), "ThingDef", "verbs.Axolotl.Verb_LotlQiIntensifyShoot.label") is None


def test_index_path_thought_stage_handle_with_index():
    thought = ET.fromstring(THOUGHT)
    assert index_path(thought, "ThoughtDef", "stages.Wear_Slave_Outfit-1.description") == "stages.1.description"
    assert index_path(thought, "ThoughtDef", "stages.1.description") == "stages.1.description"
    assert index_path(thought, "ThoughtDef", "stages.Wear_Slave_Outfit-2.label") is None


def test_index_path_body_part_prefers_custom_label():
    body = ET.fromstring(BODY)
    assert index_path(body, "BodyDef", "corePart.parts.right_gill.customLabel") == "corepart.parts.1.customlabel"
    assert index_path(body, "BodyDef", "corePart.parts.Stomach.customLabel") == "corepart.parts.2.customlabel"
    assert index_path(body, "BodyDef", "corePart.parts.Axolotl_Gill-1.customLabel") == "corepart.parts.1.customlabel"


def test_index_path_no_handle_inside_mod_extension_stages():
    xml = """
<AlienRace.ThingDef_AlienRace>
  <defName>Alien_Koelime</defName>
  <modExtensions><li><stages>
    <li><label>favor stage 1</label></li>
  </stages></li></modExtensions>
</AlienRace.ThingDef_AlienRace>"""
    node = ET.fromstring(xml)
    assert index_path(node, "AlienRace.ThingDef_AlienRace", "modExtensions.0.stages.0.label") is not None
    assert index_path(node, "AlienRace.ThingDef_AlienRace", "modExtensions.0.stages.favor_stage_1.label") is None


def test_index_path_accepts_implied_comp_class_without_generating_it():
    xml = """
<ThingDef>
  <defName>Turret</defName>
  <comps>
    <li Class="CompProperties_Power"><compClass>CompPowerTrader</compClass></li>
    <li Class="CompProperties_Refuelable"><fuelLabel>Shots</fuelLabel></li>
    <li Class="HediffCompProperties_Disappears"><fuelLabel>x</fuelLabel></li>
  </comps>
</ThingDef>"""
    node = ET.fromstring(xml)
    assert index_path(node, "ThingDef", "comps.CompRefuelable.fuelLabel") == "comps.1.fuellabel"
    assert index_path(node, "ThingDef", "comps.HediffComp_Disappears.fuelLabel") == "comps.2.fuellabel"
    assert index_path(node, "ThingDef", "comps.CompPower.fuelLabel") is None
    fields = collect_fields(node)
    assert "comps.1.fuelLabel" in fields


def test_resolve_field_text_uses_rimworld_handles():
    weapon = ET.fromstring(WEAPON)
    assert resolve_field_text(weapon, "tools.handle-1.label") == "handle"
    assert resolve_field_text(weapon, "tools.Left_Fist.label") == "Left Fist"


@pytest.mark.parametrize("defs_file", sorted(p.name for p in FIXTURES.glob("*.xml")))
def test_every_collected_field_resolves(defs_file: str):
    for node in ET.parse(FIXTURES / defs_file).getroot():
        def_type = node.tag
        for field in collect_fields(node):
            assert index_path(node, def_type, field) is not None, f"{def_type} {field}"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_scan_pending_treats_equivalent_keys_as_translated(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write(source / "Defs" / "Weapons.xml", f"<Defs>{WEAPON}{THOUGHT}</Defs>")
    di = target / "Languages" / "ChineseTraditional" / "DefInjected"
    _write(
        di / "ThingDef" / "Weapons.xml",
        """<LanguageData>
  <Axolotl_Crossbow.label>萌螈連弩</Axolotl_Crossbow.label>
  <Axolotl_Crossbow.verbs.Verb_LotlQiIntensifyShoot.label>萌螈連弩</Axolotl_Crossbow.verbs.Verb_LotlQiIntensifyShoot.label>
  <Axolotl_Crossbow.comps.0.fuelLabel>螈氣</Axolotl_Crossbow.comps.0.fuelLabel>
  <Axolotl_Crossbow.tools.left_fist.label>左拳</Axolotl_Crossbow.tools.left_fist.label>
  <Axolotl_Crossbow.tools.1.label>握柄</Axolotl_Crossbow.tools.1.label>
  <Axolotl_Crossbow.tools.handle-1.label>握柄</Axolotl_Crossbow.tools.handle-1.label>
  <Axolotl_Crossbow.tools.3.label>萌螈尾巴</Axolotl_Crossbow.tools.3.label>
</LanguageData>""",
    )
    _write(
        di / "ThoughtDef" / "Thoughts.xml",
        """<LanguageData>
  <Axolotl_WearSlaveApparel.stages.0.label>穿著奴隸服裝</Axolotl_WearSlaveApparel.stages.0.label>
  <Axolotl_WearSlaveApparel.stages.0.description>甲</Axolotl_WearSlaveApparel.stages.0.description>
  <Axolotl_WearSlaveApparel.stages.1.label>穿著奴隸服裝</Axolotl_WearSlaveApparel.stages.1.label>
  <Axolotl_WearSlaveApparel.stages.1.description>乙</Axolotl_WearSlaveApparel.stages.1.description>
</LanguageData>""",
    )
    pending, *_ = scan_pending(ProjectConfig(source, target, "ChineseTraditional"))
    remaining = {(p.def_name, p.field) for p in pending}
    assert remaining == {("Axolotl_Crossbow", "tools.Left_Fist.label")}
