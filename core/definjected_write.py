from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from core.models import PendingEntry
from core.src_comment import format_src_comment, is_src_comment_line

TAG_RE = re.compile(r"^<([^>\s/][^>\s]*)>(.*)</\1>$", re.DOTALL)
TagBlock = tuple[str, str, str, str]


def is_translated(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return False
    return "TODO" not in v.upper()


def escape_xml_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class FolderIndex:
    def __init__(self, def_type_dir: Path, warnings: list[str] | None = None):
        self.def_type_dir = def_type_dir
        self.warnings = warnings
        self.tag_to_file: dict[str, str] = {}
        self.tag_values: dict[str, str] = {}
        self.def_to_file: dict[str, str] = {}
        if def_type_dir.is_dir():
            self._scan()

    def _scan(self) -> None:
        def_files: dict[str, set[str]] = {}
        for xml_file in self.def_type_dir.glob("*.xml"):
            try:
                text = xml_file.read_text(encoding="utf-8")
            except OSError as exc:
                if self.warnings is not None:
                    self.warnings.append(f"{xml_file.name}: {exc}")
                continue
            try:
                ET.parse(xml_file)
            except ET.ParseError as exc:
                if self.warnings is not None:
                    self.warnings.append(f"{xml_file.name}: {exc}")
                continue
            for line in text.splitlines():
                m = TAG_RE.match(line.strip())
                if not m:
                    continue
                tag = m.group(1)
                val = m.group(2)
                self.tag_to_file[tag] = str(xml_file)
                self.tag_values[tag] = val
                def_name = tag.split(".", 1)[0]
                def_files.setdefault(def_name, set()).add(str(xml_file))
        for def_name, files in def_files.items():
            self.def_to_file[def_name] = sorted(files)[0]

    def refresh_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        for tag in list(self.tag_to_file.keys()):
            if self.tag_to_file[tag] == str(path):
                del self.tag_to_file[tag]
                self.tag_values.pop(tag, None)
        def_files: dict[str, set[str]] = {}
        for line in text.splitlines():
            m = TAG_RE.match(line.strip())
            if not m:
                continue
            tag = m.group(1)
            self.tag_to_file[tag] = str(path)
            self.tag_values[tag] = m.group(2)
            def_name = tag.split(".", 1)[0]
            def_files.setdefault(def_name, set()).add(str(path))
        for def_name, files in def_files.items():
            self.def_to_file[def_name] = sorted(files)[0]


def target_filename(entry: PendingEntry, use_prefix: bool, prefix: str) -> str:
    leaf = entry.source_def_file
    if not leaf.lower().endswith(".xml"):
        leaf = f"{leaf}.xml"
    if use_prefix:
        return f"{prefix}_{leaf}"
    return leaf


def resolve_target(entry: PendingEntry, index: FolderIndex, use_prefix: bool, prefix: str) -> Path:
    tag = f"{entry.def_name}.{entry.field}"
    if tag in index.tag_to_file and not use_prefix:
        return Path(index.tag_to_file[tag])
    if entry.def_name in index.def_to_file and not use_prefix:
        return Path(index.def_to_file[entry.def_name])
    return index.def_type_dir / target_filename(entry, use_prefix, prefix)


def ensure_language_data(path: Path) -> None:
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n\n</LanguageData>\n',
        encoding="utf-8",
    )


def _has_src_above(lines: list[str], tag_idx: int) -> bool:
    j = tag_idx - 1
    while j >= 0 and not lines[j].strip():
        j -= 1
    return j >= 0 and is_src_comment_line(lines[j])


def insert_tags(path: Path, blocks: list[TagBlock]) -> None:
    ensure_language_data(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, line in enumerate(lines) if line.strip() == "</LanguageData>")
    insert: list[str] = []
    if idx > 0 and lines[idx - 1].strip():
        insert.append("")
    for tag, text, source_text, field in blocks:
        insert.append(format_src_comment(field, source_text))
        insert.append(f"  <{tag}>{escape_xml_text(text)}</{tag}>")
    lines = lines[:idx] + insert + lines[idx:]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_tag(path: Path, tag: str, text: str, field: str, source_text: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    tag_idx = None
    for i, line in enumerate(lines):
        m = TAG_RE.match(line.strip())
        if m and m.group(1) == tag:
            tag_idx = i
            break
    if tag_idx is None:
        return
    has_src = _has_src_above(lines, tag_idx)
    out: list[str] = []
    for i, line in enumerate(lines):
        if i == tag_idx:
            if not has_src:
                out.append(format_src_comment(field, source_text))
            out.append(f"  <{tag}>{escape_xml_text(text)}</{tag}>")
        else:
            out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
