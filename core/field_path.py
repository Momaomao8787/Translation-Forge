from __future__ import annotations

import re

_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9_]+")
_FORMAT_SYMBOLS = re.compile(r"\{.*?\}")
_UNDERSCORE_RUN = re.compile(r"_+")
_HANDLE_ALLOWED = frozenset("qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890-_")


def slug_segment(text: str) -> str:
    s = (text or "").strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = _SLUG_NON_ALNUM.sub("", s)
    return s


def normalized_handle(text: str) -> str:
    handle = (text or "").strip()
    if not handle:
        return ""
    handle = handle.replace(" ", "_").replace("\n", "_").replace("\r", "").replace("\t", "_")
    handle = handle.replace(".", "").replace("-", "")
    handle = _FORMAT_SYMBOLS.sub("", handle)
    handle = "".join(ch for ch in handle if ch in _HANDLE_ALLOWED)
    handle = _UNDERSCORE_RUN.sub("_", handle).strip("_")
    if handle and handle.isdigit():
        handle = "_" + handle
    return handle


def parse_field_path(field: str) -> list[str]:
    field = (field or "").strip()
    if not field:
        return []
    return [part for part in field.split(".") if part]
