from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DefIndex:
    by_name: dict[str, list[tuple[str, ET.Element]]] = field(default_factory=dict)
    named: dict[str, ET.Element] = field(default_factory=dict)
    files: list[tuple[Path, list[ET.Element]]] = field(default_factory=list)
    _resolved: dict[int, tuple[ET.Element, bool]] = field(default_factory=dict)

    def candidates(self, def_name: str) -> list[tuple[str, ET.Element]]:
        return self.by_name.get(def_name, [])

    def def_nodes(self) -> Iterator[tuple[Path, str, ET.Element]]:
        for def_file, nodes in self.files:
            for node in nodes:
                def_name = _def_name(node)
                if def_name:
                    yield def_file, def_name, node

    def resolved(self, node: ET.Element) -> tuple[ET.Element, bool]:
        key = id(node)
        if key not in self._resolved:
            self._resolved[key] = _resolve(node, self.named, set())
        return self._resolved[key]


def build_def_index(defs_roots: list[Path]) -> DefIndex:
    index = DefIndex()
    for root in defs_roots:
        root_path = Path(root)
        if not root_path.is_dir():
            continue
        for def_file in sorted(root_path.rglob("*.xml")):
            try:
                tree = ET.parse(def_file)
            except ET.ParseError:
                continue
            nodes = [node for node in tree.getroot() if isinstance(node.tag, str)]
            index.files.append((def_file, nodes))
            for node in nodes:
                name_attr = node.get("Name")
                if name_attr and name_attr not in index.named:
                    index.named[name_attr] = node
                def_name = _def_name(node)
                if def_name:
                    index.by_name.setdefault(def_name, []).append((node.tag, node))
    return index


def _def_name(node: ET.Element) -> str:
    def_name_el = node.find("defName")
    return (def_name_el.text or "").strip() if def_name_el is not None else ""


def _resolve(node: ET.Element, named: dict[str, ET.Element], seen: set[int]) -> tuple[ET.Element, bool]:
    parent_name = node.get("ParentName")
    if not parent_name:
        return node, True
    parent = named.get(parent_name)
    if parent is None or id(node) in seen:
        return node, False
    seen.add(id(node))
    parent_resolved, complete = _resolve(parent, named, seen)
    merged = copy.deepcopy(parent_resolved)
    merged.tag = node.tag
    _overwrite(node, merged)
    return merged, complete


def _is_list_element(elem: ET.Element) -> bool:
    return elem.tag == "li"


def _overwrite(child: ET.Element, current: ET.Element) -> None:
    if (child.get("Inherit") or "").lower() == "false":
        for sub in list(current):
            current.remove(sub)
        current.text = child.text
        for sub in child:
            current.append(copy.deepcopy(sub))
        current.attrib.update({k: v for k, v in child.attrib.items() if k != "Inherit"})
        return
    current.attrib = dict(child.attrib)
    elements = [sub for sub in child if isinstance(sub.tag, str)]
    text = child.text if child.text and child.text.strip() else None
    if text is not None:
        for sub in list(current):
            current.remove(sub)
        current.text = child.text
        return
    if not elements:
        if any(isinstance(sub.tag, str) for sub in current):
            return
        for sub in list(current):
            current.remove(sub)
        current.text = None
        return
    for sub in elements:
        if _is_list_element(sub):
            current.append(copy.deepcopy(sub))
            continue
        existing = next((c for c in current if c.tag == sub.tag), None)
        if existing is not None:
            _overwrite(sub, existing)
            continue
        current.append(copy.deepcopy(sub))
