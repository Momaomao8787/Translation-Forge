from __future__ import annotations

import xml.etree.ElementTree as ET

from core.field_collect import collect_fields
from core.field_resolve import resolve_field_text
from core.list_segment import matches_thought_stage_handle


def test_koelime_relation_stages_use_numeric_index():
    xml = """
<AlienRace.ThingDef_AlienRace>
  <defName>Alien_Koelime</defName>
  <modExtensions>
    <li>
      <stages>
        <li><label>favor stage 1</label><description>a</description></li>
        <li><label>favor stage 2</label><description>b</description></li>
      </stages>
    </li>
  </modExtensions>
</AlienRace.ThingDef_AlienRace>"""
    fields = collect_fields(ET.fromstring(xml))
    assert "modExtensions.0.stages.0.label" in fields
    assert "modExtensions.0.stages.1.description" in fields
    assert "modExtensions.0.stages.favor_stage_1.label" not in fields


def test_koelime_joyfuzz_uses_thought_stage_duplicate_handle():
    xml = """
<ThoughtDef>
  <defName>Koelime_Joyfuzz</defName>
  <stages>
    <li><label>Draconic Blessing</label><description>a</description></li>
    <li><label>Draconic Blessing</label><description>b</description></li>
    <li><label>Draconic Blessing</label><description>c</description></li>
  </stages>
</ThoughtDef>"""
    fields = collect_fields(ET.fromstring(xml))
    assert "stages.Draconic_Blessing-0.label" in fields
    assert "stages.Draconic_Blessing-2.description" in fields
    assert "stages.draconic_blessing.label" not in fields


def test_koelime_shield_mod_extension_use_numeric_index():
    xml = """
<HediffDef>
  <defName>KoelimeShield</defName>
  <modExtensions>
    <li>
      <label>dismantle rune matrix</label>
      <description>Disrupt the rune matrix structure, rendering it ineffective.</description>
    </li>
  </modExtensions>
</HediffDef>"""
    fields = collect_fields(ET.fromstring(xml))
    assert "modExtensions.0.label" in fields
    assert "modExtensions.0.description" in fields
    assert "modExtensions.dismantle_rune_matrix.label" not in fields


def test_tools_keep_label_slug_segment():
    xml = """
<ThingDef>
  <defName>Sample</defName>
  <tools>
    <li><label>left fist</label></li>
  </tools>
</ThingDef>"""
    fields = collect_fields(ET.fromstring(xml))
    assert "tools.left_fist.label" in fields


def test_field_resolve_finds_thought_stage_handle():
    stages = ET.fromstring(
        """
<stages>
  <li><label>Draconic Blessing</label><description>a</description></li>
  <li><label>Draconic Blessing</label><description>b</description></li>
</stages>"""
    )
    items = list(stages.findall("li"))
    assert matches_thought_stage_handle(items[1], items, "Draconic_Blessing-1")

    thought = ET.fromstring(
        """
<ThoughtDef>
  <defName>Koelime_Joyfuzz</defName>
  <stages>
    <li><label>Draconic Blessing</label><description>a</description></li>
    <li><label>Draconic Blessing</label><description>b</description></li>
  </stages>
</ThoughtDef>"""
    )
    assert resolve_field_text(thought, "stages.Draconic_Blessing-1.description") == "b"
