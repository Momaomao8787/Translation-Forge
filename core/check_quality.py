from __future__ import annotations

import re
from pathlib import Path

from core.definjected_write import TAG_RE
from core.export_merge import default_single_pending_path
from core.models import WRITE_MODE_MERGE_EXISTING, WRITE_MODE_NEW_FILE

_SUFFIX_RE = re.compile(r"-\d+$")


def find_duplicate_tags(definjected_root: Path) -> list[str]:
    if not definjected_root.is_dir():
        return []
    out: list[str] = []
    for xml_file in definjected_root.rglob("*.xml"):
        counts: dict[str, int] = {}
        try:
            text = xml_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            m = TAG_RE.match(line.strip())
            if not m:
                continue
            tag = m.group(1)
            counts[tag] = counts.get(tag, 0) + 1
        for tag, n in sorted(counts.items()):
            if n > 1:
                rel = xml_file.relative_to(definjected_root)
                out.append(f"{rel}: {tag} x{n}")
    return out


def find_write_strategy_mix(definjected_root: Path, prefix: str) -> list[str]:
    if not definjected_root.is_dir() or not (prefix or "").strip():
        return []
    prefix = prefix.strip()
    tag_files: dict[str, set[str]] = {}
    for xml_file in definjected_root.rglob("*.xml"):
        name = xml_file.name
        try:
            text = xml_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            m = TAG_RE.match(line.strip())
            if not m:
                continue
            tag_files.setdefault(m.group(1), set()).add(name)
    out: list[str] = []
    for tag, files in sorted(tag_files.items()):
        if len(files) < 2:
            continue
        has_prefixed = any(f.startswith(f"{prefix}_") for f in files)
        has_plain = any(not f.startswith(f"{prefix}_") for f in files)
        if has_prefixed and has_plain:
            out.append(f"{tag}: {', '.join(sorted(files))}")
    return out


def find_manifest_strategy_hint(meta: dict | None, ui_import_mode: str | None) -> str | None:
    if not meta or not ui_import_mode:
        return None
    meta_mode = meta.get("importWriteMode", WRITE_MODE_MERGE_EXISTING)
    if meta_mode != ui_import_mode:
        return f"manifest:{meta_mode} vs ui:{ui_import_mode}"
    return None


def find_pending_format_mix(target_mod: Path) -> bool:
    csv_path = default_single_pending_path(target_mod, "csv")
    xml_path = default_single_pending_path(target_mod, "xml")
    return csv_path.is_file() and xml_path.is_file()


def has_collision_suffix(folder_name: str) -> bool:
    return bool(_SUFFIX_RE.search(folder_name.strip()))
