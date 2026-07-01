from __future__ import annotations

from core.meta import normalize_meta, read_meta
from core.models import (
    EXPORT_LAYOUT_SINGLE,
    WRITE_MODE_MERGE_EXISTING,
    WRITE_MODE_NEW_FILE,
)


def test_normalize_meta_defaults_layout():
    raw = {"sourceMod": "a", "targetMod": "b", "targetLang": "ChineseTraditional"}
    meta = normalize_meta(raw)
    assert meta["layout"] == EXPORT_LAYOUT_SINGLE
    assert meta["importWriteMode"] == WRITE_MODE_MERGE_EXISTING
    assert meta["importPrefix"] == ""


def test_normalize_meta_use_prefix_migration():
    raw = {
        "usePrefix": True,
        "prefix": "Demo_Mod",
        "format": "csv",
    }
    meta = normalize_meta(raw)
    assert meta["importWriteMode"] == WRITE_MODE_NEW_FILE
    assert meta["importPrefix"] == "Demo_Mod"


def test_read_meta_applies_normalize(tmp_path):
    meta_path = tmp_path / "DefInjected-missing.csv.meta.json"
    meta_path.write_text(
        '{"usePrefix": true, "prefix": "X", "format": "csv", "sourceMod": "s", "targetMod": "t", "targetLang": "ChineseTraditional"}',
        encoding="utf-8",
    )
    meta = read_meta(meta_path)
    assert meta["importWriteMode"] == WRITE_MODE_NEW_FILE
    assert meta["importPrefix"] == "X"
