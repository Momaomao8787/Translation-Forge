from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from core.field_path import normalized_handle

TEXT = "text"
TYPE = "type"


@dataclass(frozen=True)
class HandleField:
    tag: str
    kind: str
    priority: int = 0


_TOOL = (HandleField("label", TEXT),)
_VERB = (HandleField("label", TEXT, 100), HandleField("verbClass", TYPE))
_COMP = (HandleField("compClass", TYPE),)
_PART = (HandleField("customLabel", TEXT, 100), HandleField("def", TEXT))
_HEDIFF_GIVER = (HandleField("hediff", TEXT),)
_DOER = (HandleField("doerClass", TYPE),)
_LIFE_STAGE = (
    HandleField("label", TEXT, 200),
    HandleField("labelMale", TEXT, 100),
    HandleField("labelFemale", TEXT),
)
_THOUGHT_STAGE = (HandleField("label", TEXT, 100), HandleField("labelSocial", TEXT))
_LABEL = (HandleField("label", TEXT),)

_LIST_HANDLE_FIELDS: dict[str, tuple[HandleField, ...]] = {
    "tools": _TOOL,
    "verbs": _VERB,
    "comps": _COMP,
    "parts": _PART,
    "hediffGivers": _HEDIFF_GIVER,
    "doers": _DOER,
    "lifeStages": _LIFE_STAGE,
    "scoreStages": _LABEL,
    "degreeDatas": _LABEL,
}

_ROOT_STAGE_FIELDS: dict[str, tuple[HandleField, ...]] = {
    "ThoughtDef": _THOUGHT_STAGE,
    "HediffDef": _LABEL,
}

_IMPLIED_COMP_PREFIXES = (
    ("HediffCompProperties_", "HediffComp_"),
    ("CompProperties_", "Comp"),
)

_GENERATION_TAGS: dict[str, tuple[str, ...]] = {
    "tools": ("label",),
    "verbs": ("verbClass",),
    "comps": ("compClass",),
    "parts": ("customLabel", "def"),
}


def _local_tag(elem: ET.Element) -> str:
    tag = elem.tag
    if isinstance(tag, str) and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return str(tag)


def list_items(container: ET.Element) -> list[ET.Element]:
    return [child for child in container if _local_tag(child) == "li"]


def handle_fields(path_parts: list[str], def_type: str) -> tuple[HandleField, ...]:
    if not path_parts:
        return ()
    list_tag = path_parts[-1]
    if list_tag == "stages":
        if len(path_parts) == 1:
            return _ROOT_STAGE_FIELDS.get(def_type, ())
        return ()
    return _LIST_HANDLE_FIELDS.get(list_tag, ())


def _raw_value(li: ET.Element, field: HandleField) -> str:
    el = li.find(field.tag)
    if el is None:
        return ""
    return (el.text or "").strip()


def _implied_comp_class(li: ET.Element) -> str:
    props_class = (li.get("Class") or "").strip().rsplit(".", 1)[-1]
    for prefix, comp_prefix in _IMPLIED_COMP_PREFIXES:
        if props_class.startswith(prefix) and len(props_class) > len(prefix):
            return comp_prefix + props_class[len(prefix):]
    return ""


def _handle_values(li: ET.Element, field: HandleField, *, implied: bool = False) -> set[str]:
    raw = _raw_value(li, field)
    if not raw and implied and field.tag == "compClass":
        raw = _implied_comp_class(li)
    if not raw:
        return set()
    candidates = [raw]
    if field.kind == TYPE:
        candidates.append(raw.rsplit(".", 1)[-1])
    return {h for h in (normalized_handle(c) for c in candidates) if h}


def _segment_value(li: ET.Element, field: HandleField) -> str:
    raw = _raw_value(li, field)
    if field.kind == TYPE:
        raw = raw.rsplit(".", 1)[-1]
    return normalized_handle(raw)


def _matching_positions(
    items: list[ET.Element],
    field: HandleField,
    handle: str,
    *,
    implied: bool = False,
) -> list[int]:
    return [i for i, li in enumerate(items) if handle in _handle_values(li, field, implied=implied)]


def _handle_with_index(li: ET.Element, items: list[ET.Element], field: HandleField, handle: str) -> str:
    positions = _matching_positions(items, field, handle)
    if len(positions) <= 1:
        return handle
    own = next(i for i, item in enumerate(items) if item is li)
    return f"{handle}-{positions.index(own)}"


def find_list_item_index(
    items: list[ET.Element],
    segment: str,
    path_parts: list[str],
    def_type: str,
) -> int | None:
    if segment.isdigit():
        idx = int(segment)
        return idx if idx < len(items) else None
    fields = handle_fields(path_parts, def_type)
    if not fields:
        return None
    handle_index = 0
    handle = segment
    if "-" in segment:
        pieces = segment.split("-")
        if not pieces[1].isdigit():
            return None
        handle = pieces[0]
        handle_index = int(pieces[1])
    handle = normalized_handle(handle)
    if not handle:
        return None
    best: HandleField | None = None
    for field in fields:
        if best is not None and field.priority <= best.priority:
            continue
        if any(handle in _handle_values(li, field, implied=True) for li in items):
            best = field
    if best is None:
        return None
    positions = _matching_positions(items, best, handle, implied=True)
    if handle_index >= len(positions):
        return None
    return positions[handle_index]


def _thought_stage_segment(li: ET.Element, items: list[ET.Element], fields: tuple[HandleField, ...]) -> str | None:
    label_field = next((f for f in fields if f.tag == "label"), None)
    if label_field is None:
        return None
    handle = _segment_value(li, label_field)
    if not handle or len(_matching_positions(items, label_field, handle)) <= 1:
        return None
    return _handle_with_index(li, items, label_field, handle)


def for_list_item(
    li: ET.Element,
    path_parts: list[str],
    def_type: str,
    siblings: list[ET.Element],
) -> str | None:
    fields = handle_fields(path_parts, def_type)
    if not fields:
        return None
    list_tag = path_parts[-1]
    if list_tag == "stages":
        segment = _thought_stage_segment(li, siblings, fields) if def_type == "ThoughtDef" else None
    else:
        segment = None
        by_tag = {f.tag: f for f in fields}
        for tag in _GENERATION_TAGS.get(list_tag, ()):
            field = by_tag.get(tag)
            if field is None:
                continue
            handle = _segment_value(li, field)
            if handle:
                segment = _handle_with_index(li, siblings, field, handle)
                break
    if segment is None:
        return None
    own = next(i for i, item in enumerate(siblings) if item is li)
    if find_list_item_index(siblings, segment, path_parts, def_type) != own:
        return None
    return segment
