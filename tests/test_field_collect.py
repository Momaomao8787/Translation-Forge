from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.field_collect import collect_fields

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "source_mod" / "Defs"


def _load_def(defs_file: str, def_name: str) -> ET.Element:
    tree = ET.parse(FIXTURES / defs_file)
    for node in tree.getroot():
        dn = node.find("defName")
        if dn is not None and dn.text == def_name:
            return node
    raise AssertionError(f"{def_name} not in {defs_file}")


def test_collect_nested_weapon():
    fields = collect_fields(_load_def("NestedWeapon.xml", "NestedGun"))
    assert fields["label"] == "Nested Gun"
    assert fields["tools.stock.label"] == "stock"
    assert fields["verbs.Verb_Shoot.label"] == "Nested Gun"


def test_collect_nested_comp():
    fields = collect_fields(_load_def("NestedComp.xml", "NestedBeacon"))
    assert fields["comps.CompRefuelable.fuelLabel"] == "Wood left"


def test_collect_thought_stages():
    fields = collect_fields(_load_def("NestedThought.xml", "NestedThought"))
    assert fields["stages.soaking_wet.label"] == "soaking wet"
    assert fields["stages.booty.description"] == "spoils of war."
