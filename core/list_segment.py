from __future__ import annotations

import xml.etree.ElementTree as ET

from core.field_path import slug_segment


def _local_tag(elem: ET.Element) -> str:
    tag = elem.tag
    if isinstance(tag, str) and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return str(tag)


def _named_segment(li: ET.Element) -> str | None:
    vc = li.find("verbClass")
    if vc is not None and (vc.text or "").strip():
        return vc.text.strip()
    cc = li.find("compClass")
    if cc is not None and (cc.text or "").strip():
        return cc.text.strip()
    custom_label = li.find("customLabel")
    if custom_label is not None and (custom_label.text or "").strip():
        return slug_segment(custom_label.text)
    def_el = li.find("def")
    if def_el is not None and (def_el.text or "").strip():
        return def_el.text.strip()
    return None


def label_to_handle_base(label: str) -> str:
    return (label or "").strip().replace(" ", "_")


def thought_stage_handle(li: ET.Element, siblings: list[ET.Element]) -> str | None:
    label = (li.findtext("label") or "").strip()
    if not label:
        return None
    same_label_count = sum(
        1 for s in siblings if (s.findtext("label") or "").strip() == label
    )
    if same_label_count <= 1:
        return None
    idx_among = 0
    for sibling in siblings:
        if sibling is li:
            break
        if (sibling.findtext("label") or "").strip() == label:
            idx_among += 1
    return f"{label_to_handle_base(label)}-{idx_among}"


def for_list_item(
    li: ET.Element,
    path_parts: list[str],
    def_type: str,
    siblings: list[ET.Element],
) -> str | None:
    named = _named_segment(li)
    if named is not None:
        return named

    parent = path_parts[-1] if path_parts else ""
    if parent == "tools":
        label = li.find("label")
        if label is not None and (label.text or "").strip():
            return slug_segment(label.text)

    if parent == "stages" and def_type == "ThoughtDef":
        return thought_stage_handle(li, siblings)

    return None


def matches_thought_stage_handle(
    li: ET.Element,
    siblings: list[ET.Element],
    segment: str,
) -> bool:
    expected = thought_stage_handle(li, siblings)
    return expected is not None and expected == segment
