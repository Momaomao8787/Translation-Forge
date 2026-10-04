from __future__ import annotations

from pathlib import Path

from core.models import (
    DEFAULT_EXPORT_BASENAME,
    EXPORT_PLACEHOLDER_EMPTY,
    EXPORT_PLACEHOLDER_SOURCE,
    EXPORT_PLACEHOLDER_TODO,
    PendingEntry,
)


def default_single_pending_path(target_mod: Path, fmt: str) -> Path:
    ext = "csv" if fmt.lower() == "csv" else "xml"
    return Path(target_mod) / f"{DEFAULT_EXPORT_BASENAME}.{ext}"


def default_stale_list_path(target_mod: Path) -> Path:
    return Path(target_mod) / f"{DEFAULT_EXPORT_BASENAME}.stale.txt"


def placeholder_text(mode: str, source_text: str) -> str:
    if mode == EXPORT_PLACEHOLDER_EMPTY:
        return ""
    if mode == EXPORT_PLACEHOLDER_SOURCE:
        return source_text
    return "TODO"


def entry_key(entry: PendingEntry) -> tuple[str, str, str]:
    return (entry.def_type, entry.def_name, entry.field)


def merge_pending_entries(
    new_pending: list[PendingEntry],
    old_entries: list[PendingEntry],
    placeholder: str,
) -> list[PendingEntry]:
    old_map = {entry_key(e): e for e in old_entries}
    merged: list[PendingEntry] = []
    for entry in new_pending:
        key = entry_key(entry)
        if key in old_map:
            old = old_map[key]
            merged.append(
                PendingEntry(
                    def_name=entry.def_name,
                    def_type=entry.def_type,
                    field=entry.field,
                    source_text=entry.source_text,
                    translation=old.translation,
                    source_def_file=entry.source_def_file or old.source_def_file,
                )
            )
        else:
            merged.append(
                PendingEntry(
                    def_name=entry.def_name,
                    def_type=entry.def_type,
                    field=entry.field,
                    source_text=entry.source_text,
                    translation=placeholder_text(placeholder, entry.source_text),
                    source_def_file=entry.source_def_file,
                )
            )
    return merged
