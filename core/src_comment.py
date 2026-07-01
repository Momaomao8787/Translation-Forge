from __future__ import annotations

import re

SRC_GOOD_RE = re.compile(r"^\s*<!--\s*SRC\s+([^:]+)\s*:\s*(.*?)\s*-->\s*$")
EN_GOOD_RE = re.compile(r"^\s*<!--\s*EN\s+([^:]+)\s*:\s*(.*?)\s*-->\s*$")
EN_LEGACY_RE = re.compile(r"^\s*<!--\s*EN\s*:\s*(.*?)\s*-->\s*$")
LEGACY_FIELD_RE = re.compile(r"^\s*<!--\s*(\w+)\s*:\s*(.*?)\s*-->\s*$")

SKIP_COMMENT_FIELDS = frozenset({"source", "sourcedeffile", "rdt"})


def escape_xml_comment(text: str) -> str:
    s = text or ""
    s = s.replace("--", "—")
    if s.endswith("-"):
        s = s[:-1] + "—"
    return s


def src_text_for_entry(source_text: str) -> str:
    if not (source_text or "").strip():
        return "(empty)"
    return source_text


def format_src_comment(field: str, source_text: str, indent: str = "  ") -> str:
    body = src_text_for_entry(source_text)
    return f"{indent}<!-- SRC {field}: {escape_xml_comment(body)} -->"


def parse_src_line(line: str) -> tuple[str, str] | None:
    m = SRC_GOOD_RE.match(line)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    m = EN_GOOD_RE.match(line)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    m = EN_LEGACY_RE.match(line)
    if m:
        return "", m.group(1).strip()
    m = LEGACY_FIELD_RE.match(line)
    if m:
        field = m.group(1).strip()
        if field.lower() in SKIP_COMMENT_FIELDS:
            return None
        return field, m.group(2).strip()
    return None


def is_src_comment_line(line: str) -> bool:
    return parse_src_line(line) is not None
