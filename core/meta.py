from __future__ import annotations

import json
from pathlib import Path

from core.errors import LocalizedError
from core.models import (
    EXPORT_LAYOUT_SINGLE,
    EXPORT_PLACEHOLDER_TODO,
    ProjectConfig,
    WRITE_MODE_MERGE_EXISTING,
    WRITE_MODE_NEW_FILE,
)

APP_DISPLAY_NAME = "Momaomao's Translation Forge"
META_VERSION = 1


def meta_path_for(output_path: Path) -> Path:
    return output_path.with_suffix(output_path.suffix + ".meta.json")


def normalize_meta(raw: dict) -> dict:
    meta = dict(raw)
    if not meta.get("layout"):
        meta["layout"] = EXPORT_LAYOUT_SINGLE
    if not meta.get("placeholder"):
        meta["placeholder"] = EXPORT_PLACEHOLDER_TODO
    if meta.get("usePrefix") and not meta.get("importWriteMode"):
        meta["importWriteMode"] = WRITE_MODE_NEW_FILE
    elif not meta.get("importWriteMode"):
        meta["importWriteMode"] = WRITE_MODE_MERGE_EXISTING
    if meta.get("usePrefix") and meta.get("prefix") and not meta.get("importPrefix"):
        meta["importPrefix"] = meta["prefix"]
    if "importPrefix" not in meta:
        meta["importPrefix"] = ""
    return meta


def write_meta(
    meta_path: Path,
    config: ProjectConfig,
    defs_roots: list[Path],
    fmt: str,
    *,
    layout: str = EXPORT_LAYOUT_SINGLE,
    placeholder: str = EXPORT_PLACEHOLDER_TODO,
    import_write_mode: str = WRITE_MODE_MERGE_EXISTING,
    import_prefix: str = "",
) -> None:
    payload = {
        "metaVersion": META_VERSION,
        "sourceMod": str(Path(config.source_mod).resolve()),
        "targetMod": str(Path(config.target_mod).resolve()),
        "targetLang": config.target_lang,
        "defsRoots": [str(p) for p in defs_roots],
        "format": fmt,
        "layout": layout,
        "placeholder": placeholder,
        "importWriteMode": import_write_mode,
        "importPrefix": import_prefix,
    }
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_meta(meta_path: Path) -> dict:
    if not meta_path.is_file():
        raise FileNotFoundError(f"找不到 metadata: {meta_path}")
    return normalize_meta(json.loads(meta_path.read_text(encoding="utf-8")))


def meta_to_config(meta: dict) -> ProjectConfig:
    normalized = normalize_meta(meta)
    return ProjectConfig(
        source_mod=Path(normalized["sourceMod"]),
        target_mod=Path(normalized["targetMod"]),
        target_lang=normalized["targetLang"],
    )


def find_meta_for_input(input_path: Path) -> Path:
    sidecar = meta_path_for(input_path)
    if sidecar.is_file():
        return sidecar
    alt = input_path.with_name(input_path.stem + ".meta.json")
    if alt.is_file():
        return alt
    raise LocalizedError("err.metadata_not_found")
