from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.def_inherit import DefIndex
from core.field_resolve import index_path


def _short_type(type_name: str) -> str:
    return type_name.rsplit(".", 1)[-1]


def _type_compatible(folder: str, def_type: str) -> bool:
    a = _short_type(folder)
    b = _short_type(def_type)
    return a == b or b.startswith(a) or b.endswith(a) or a.startswith(b) or a.endswith(b)


def read_patch_text(patch_roots: list[Path]) -> str:
    chunks: list[str] = []
    for root in patch_roots:
        for patch_file in sorted(Path(root).rglob("*.xml")):
            try:
                chunks.append(patch_file.read_text(encoding="utf-8-sig", errors="replace"))
            except OSError:
                continue
    return "\n".join(chunks)


def is_stale_key(folder: str, def_name: str, field: str, index: DefIndex, patch_text: str) -> bool:
    candidates = index.candidates(def_name)
    patched = bool(patch_text) and def_name in patch_text
    if not candidates:
        return not patched
    compatible = [(t, n) for t, n in candidates if _type_compatible(folder, t)]
    if not compatible:
        return True
    uncertain = patched
    for def_type, node in compatible:
        resolved, complete = index.resolved(node)
        if index_path(resolved, def_type, field) is not None:
            return False
        if not complete:
            uncertain = True
    return not uncertain


def find_stale_keys(definjected: Path, index: DefIndex, patch_text: str = "") -> list[str]:
    out: list[str] = []
    if not definjected.is_dir():
        return out
    for tr_file in sorted(definjected.rglob("*.xml")):
        rel = tr_file.relative_to(definjected)
        if len(rel.parts) < 2:
            continue
        folder = rel.parts[0]
        try:
            root = ET.parse(tr_file).getroot()
        except ET.ParseError:
            continue
        if root.tag != "LanguageData":
            continue
        for child in root:
            if not isinstance(child.tag, str) or "." not in child.tag:
                continue
            def_name, field = child.tag.split(".", 1)
            if is_stale_key(folder, def_name.strip(), field.strip(), index, patch_text):
                out.append(f"{rel.as_posix()}: {child.tag}")
    return out
