from __future__ import annotations

import re

_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9_]+")


def slug_segment(text: str) -> str:
    s = (text or "").strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = _SLUG_NON_ALNUM.sub("", s)
    return s


def parse_field_path(field: str) -> list[str]:
    field = (field or "").strip()
    if not field:
        return []
    return [part for part in field.split(".") if part]
