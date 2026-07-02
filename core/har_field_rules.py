from __future__ import annotations

import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path

from core.paths import discover_defs_roots


class HarSkipReason(Enum):
    NONE = "none"
    COLOR_CHANNEL_NAME = "color_channel_name"
    BODY_ADDON_NAME = "body_addon_name"
    BODY_PART_LABEL_CONDITION = "body_part_label_condition"


def is_har_def_type(def_type: str) -> bool:
    return bool(def_type) and "alienrace" in def_type.lower()


def get_skip_reason(def_type: str, field_path: str) -> HarSkipReason:
    if not field_path:
        return HarSkipReason.NONE
    if _matches_body_part_label_condition(field_path):
        return HarSkipReason.BODY_PART_LABEL_CONDITION
    if _matches_color_channel_name(field_path):
        return HarSkipReason.COLOR_CHANNEL_NAME
    if _matches_body_addon_name(field_path):
        return HarSkipReason.BODY_ADDON_NAME
    return HarSkipReason.NONE


def should_skip_from_pending(def_type: str, field_path: str) -> bool:
    return get_skip_reason(def_type, field_path) != HarSkipReason.NONE


def should_block_import(
    def_type: str,
    field_path: str,
    source_text: str,
    translation: str,
) -> bool:
    if get_skip_reason(def_type, field_path) == HarSkipReason.NONE:
        return False
    src = (source_text or "").strip()
    tr = (translation or "").strip()
    if not src:
        return bool(tr)
    return src != tr


def resolve_import_text(
    def_type: str,
    field_path: str,
    source_text: str,
    translation: str,
) -> str:
    if not should_block_import(def_type, field_path, source_text, translation):
        return translation
    return source_text


def source_mod_uses_har(source_mod: Path) -> bool:
    if not source_mod.is_dir():
        return False
    for root in discover_defs_roots(source_mod):
        for def_file in root.rglob("*.xml"):
            try:
                tree = ET.parse(def_file)
            except ET.ParseError:
                continue
            for node in tree.getroot():
                if isinstance(node.tag, str) and is_har_def_type(node.tag):
                    return True
    return False


def count_har_fields_in_def_map(def_map) -> int:
    count = 0
    for rec in def_map.values():
        for field in rec.fields:
            if should_skip_from_pending(rec.def_type, field):
                count += 1
    return count


def _matches_color_channel_name(field: str) -> bool:
    return ".colorChannels." in field and field.endswith(".name")


def _matches_body_addon_name(field: str) -> bool:
    return (
        ".bodyAddons." in field
        and field.endswith(".name")
        and ".conditions." not in field
    )


def _matches_body_part_label_condition(field: str) -> bool:
    return (
        ".bodyAddons." in field
        and ".conditions." in field
        and field.endswith(".bodyPartLabel")
    )
