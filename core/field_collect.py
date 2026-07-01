from __future__ import annotations

import xml.etree.ElementTree as ET

from core.field_path import slug_segment
from core.models import DEFAULT_FIELDS

TRANSLATABLE_LEAF_TAGS = frozenset(
    {
        *DEFAULT_FIELDS,
        "baseDesc",
        "fuelGizmoLabel",
        "fuelLabel",
        "outOfFuelMessage",
        "labelNoLocation",
        "labelFemale",
        "labelFemalePlural",
        "labelMale",
        "labelMalePlural",
        "messageDefendersAttacking",
        "royalFavorLabel",
        "name",
    }
)


def _local_tag(elem: ET.Element) -> str:
    tag = elem.tag
    if isinstance(tag, str) and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return str(tag)


def _li_segment(li: ET.Element) -> str | None:
    vc = li.find("verbClass")
    if vc is not None and (vc.text or "").strip():
        return vc.text.strip()
    cc = li.find("compClass")
    if cc is not None and (cc.text or "").strip():
        return cc.text.strip()
    for key in ("customLabel", "def", "label"):
        el = li.find(key)
        if el is not None and (el.text or "").strip():
            return slug_segment(el.text)
    return None


def _is_leaf_element(elem: ET.Element) -> bool:
    return not any(isinstance(child.tag, str) for child in elem)


def collect_fields(def_node: ET.Element) -> dict[str, str]:
    fields: dict[str, str] = {}

    def add_path(path_parts: list[str], elem: ET.Element) -> None:
        path = ".".join(path_parts)
        if path in fields:
            return
        fields[path] = (elem.text or "").strip()

    def walk(container: ET.Element, path_parts: list[str]) -> None:
        li_index = 0
        for child in container:
            if not isinstance(child.tag, str):
                continue
            tag = _local_tag(child)
            if tag == "defName":
                continue

            if tag == "li":
                seg = _li_segment(child)
                if seg is None:
                    seg = str(li_index)
                li_index += 1
                walk(child, path_parts + [seg])
                continue

            child_elems = [c for c in child if isinstance(c.tag, str)]
            if not child_elems and tag in TRANSLATABLE_LEAF_TAGS:
                add_path(path_parts + [tag], child)
            else:
                walk(child, path_parts + [tag])

    walk(def_node, [])

    label_fallback = fields.get("label", "")
    verbs = def_node.find("verbs")
    if verbs is not None:
        for li in verbs.findall("li"):
            vc = li.find("verbClass")
            if vc is None or not (vc.text or "").strip():
                continue
            class_name = vc.text.strip()
            path = f"verbs.{class_name}.label"
            if path in fields:
                continue
            lab = li.find("label")
            if lab is not None and (lab.text or "").strip():
                fields[path] = lab.text.strip()
            elif label_fallback:
                fields[path] = label_fallback

    return fields
