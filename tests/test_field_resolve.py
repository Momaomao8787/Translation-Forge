from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.field_path import parse_field_path, slug_segment
from core.field_resolve import resolve_field_text

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "source_mod" / "Defs"


def _load_def(defs_file: str, def_name: str) -> ET.Element:
    tree = ET.parse(FIXTURES / defs_file)
    for node in tree.getroot():
        dn = node.find("defName")
        if dn is not None and dn.text == def_name:
            return node
    raise AssertionError(f"{def_name} not in {defs_file}")


def test_slug_segment():
    assert slug_segment("Soaking Wet") == "soaking_wet"
    assert slug_segment("Verb_Shoot") == "verb_shoot"


def test_parse_field_path():
    assert parse_field_path("tools.stock.label") == ["tools", "stock", "label"]


def test_resolve_tools_label():
    node = _load_def("NestedWeapon.xml", "NestedGun")
    assert resolve_field_text(node, "tools.stock.label") == "stock"
    assert resolve_field_text(node, "tools.barrel.label") == "barrel"


def test_resolve_verb_label_fallback():
    node = _load_def("NestedWeapon.xml", "NestedGun")
    assert resolve_field_text(node, "verbs.Verb_Shoot.label") == "Nested Gun"


def test_resolve_comp_fields():
    node = _load_def("NestedComp.xml", "NestedBeacon")
    assert resolve_field_text(node, "comps.CompRefuelable.fuelGizmoLabel") == "Wood left"
    assert resolve_field_text(node, "comps.CompRefuelable.outOfFuelMessage") == "Needs wood"


def test_resolve_thought_stages():
    node = _load_def("NestedThought.xml", "NestedThought")
    assert resolve_field_text(node, "stages.0.label") == "soaking wet"
    assert resolve_field_text(node, "stages.1.description") == "spoils of war."
