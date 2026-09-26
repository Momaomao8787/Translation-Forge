from __future__ import annotations

import xml.etree.ElementTree as ET

from core.def_inherit import DefIndex, build_def_index
from core.field_path import parse_field_path, slug_segment
from core.list_segment import find_list_item_index, list_items
from core.models import DefRecord

_BACKSTORY_TYPES = frozenset({"BackstoryDef", "AlienRace.AlienBackstoryDef"})


def _local_tag(elem: ET.Element) -> str:
    tag = elem.tag
    if isinstance(tag, str) and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return str(tag)


def _element_text(elem: ET.Element | None) -> str | None:
    if elem is None:
        return None
    text = (elem.text or "").strip()
    return text if text else None


def _find_child_ignore_case(container: ET.Element, segment: str) -> ET.Element | None:
    wanted = segment.lower()
    for child in container:
        if isinstance(child.tag, str) and _local_tag(child) != "li" and _local_tag(child).lower() == wanted:
            return child
    return None


def index_path(def_elem: ET.Element | None, def_type: str, field_path: str) -> str | None:
    parts = parse_field_path(field_path)
    if def_elem is None or not parts:
        return None
    current = def_elem
    tags: list[str] = []
    out: list[str] = []
    for segment in parts[:-1]:
        child = None if segment.isdigit() else _find_child_ignore_case(current, segment)
        if child is not None:
            tag = _local_tag(child)
            current = child
            tags.append(tag)
            out.append(tag.lower())
            continue
        items = list_items(current)
        if not items:
            return None
        idx = find_list_item_index(items, segment, tags, def_type)
        if idx is None:
            return None
        current = items[idx]
        tags.append(str(idx))
        out.append(str(idx))
    out.append(parts[-1].lower())
    return ".".join(out)


def _find_li_by_segment(
    container: ET.Element,
    segment: str,
    path_parts: list[str],
    def_type: str,
) -> ET.Element | None:
    items = list_items(container)
    idx = find_list_item_index(items, segment, path_parts, def_type)
    if idx is not None:
        return items[idx]
    if segment.isdigit():
        return None

    seg_slug = slug_segment(segment)
    for li in items:
        vc = li.find("verbClass")
        if vc is not None and (vc.text or "").strip() == segment:
            return li
        cc = li.find("compClass")
        if cc is not None and (cc.text or "").strip() == segment:
            return li
        for key in ("customLabel", "def", "label"):
            el = li.find(key)
            if el is None:
                continue
            raw = (el.text or "").strip()
            if not raw:
                continue
            if raw == segment or slug_segment(raw) == seg_slug:
                return li
    return None


def _field_lookup_order(field_path: str, def_type: str) -> list[str]:
    parts = parse_field_path(field_path)
    if not parts:
        return []
    if parts[-1] == "description" and def_type in _BACKSTORY_TYPES:
        base = ".".join(parts[:-1] + ["baseDesc"]) if len(parts) > 1 else "baseDesc"
        return [field_path, base]
    return [field_path]


def resolve_field_text(def_elem: ET.Element, field_path: str, *, def_type: str = "") -> str | None:
    def_type = def_type or _local_tag(def_elem)
    for candidate in _field_lookup_order(field_path, def_type):
        text = _resolve_field_text_once(def_elem, candidate, def_type)
        if text is not None:
            return text

    if field_path.startswith("verbs.") and field_path.endswith(".label"):
        return _element_text(def_elem.find("label"))
    return None


def _resolve_field_text_once(def_elem: ET.Element, field_path: str, def_type: str = "") -> str | None:
    parts = parse_field_path(field_path)
    if not parts:
        return None

    current: ET.Element | None = def_elem
    tags: list[str] = []
    for i, segment in enumerate(parts):
        if current is None:
            return None
        is_last = i == len(parts) - 1

        if is_last:
            if _local_tag(current) == segment:
                return _element_text(current)
            leaf = current.find(segment)
            return _element_text(leaf)

        child = None if segment.isdigit() else current.find(segment)
        if child is not None:
            current = child
            tags.append(segment)
            continue

        li = _find_li_by_segment(current, segment, tags, def_type)
        if li is not None:
            current = li
            tags.append(segment)
            continue
        return None
    return None


def _def_map_key(def_type: str, def_name: str) -> tuple[str, str]:
    return (def_type, def_name)


def _lookup_def_record(
    def_map: dict[tuple[str, str], DefRecord],
    def_name: str,
    def_type: str,
) -> DefRecord | None:
    if def_type:
        key = _def_map_key(def_type, def_name)
        if key in def_map:
            return def_map[key]
        if def_type == "BackstoryDef":
            key = _def_map_key("AlienRace.AlienBackstoryDef", def_name)
            if key in def_map:
                return def_map[key]
    for rec in def_map.values():
        if rec.def_name == def_name:
            return rec
    return None


def build_def_element_map(
    def_map: dict[tuple[str, str], DefRecord],
    defs_roots: list,
    index: DefIndex | None = None,
) -> dict[tuple[str, str], ET.Element]:
    index = index if index is not None else build_def_index(defs_roots)
    out: dict[tuple[str, str], ET.Element] = {}
    for _, def_name, node in index.def_nodes():
        key = _def_map_key(node.tag, def_name)
        if key not in out:
            out[key] = index.resolved(node)[0]
    return out


def resolve_field_text_for_def(
    def_elem: ET.Element | None,
    def_type: str,
    field_path: str,
) -> str | None:
    if def_elem is None:
        return None
    return resolve_field_text(def_elem, field_path, def_type=def_type)


def resolve_field_text_from_maps(
    def_map: dict[tuple[str, str], DefRecord],
    element_map: dict[tuple[str, str], ET.Element],
    def_name: str,
    def_type: str,
    field_path: str,
) -> str | None:
    rec = _lookup_def_record(def_map, def_name, def_type)
    dtype = rec.def_type if rec else def_type
    key = _def_map_key(dtype, def_name)
    elem = element_map.get(key)
    if elem is None and rec:
        elem = element_map.get(_def_map_key(rec.def_type, def_name))
    return resolve_field_text_for_def(elem, dtype, field_path)
