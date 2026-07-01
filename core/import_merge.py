from __future__ import annotations

import csv
import re
from pathlib import Path

from core.definjected_write import (
    FolderIndex,
    TagBlock,
    insert_tags,
    is_translated,
    resolve_target,
    update_tag,
)
from core.errors import LocalizedError, set_result_error, zh_fallback
from core.export_merge import default_single_pending_path
from core.meta import find_meta_for_input, meta_to_config, read_meta
from core.models import (
    EXPORT_LAYOUT_BY_SOURCE,
    EXPORT_LAYOUT_SINGLE,
    ImportResult,
    PendingEntry,
    WRITE_MODE_MERGE_EXISTING,
    WRITE_MODE_NEW_FILE,
)
from core.paths import definjected_root, normalize_path, resolve_mod_path
from core.src_comment import is_src_comment_line, parse_src_line

TAG_RE = re.compile(r"^<([^>\s/][^>\s]*)>(.*)</\1>$", re.DOTALL)
SECTION_RE = re.compile(r"^\s*<!--\s*=+\s*(.+?)\s*=+\s*-->\s*$")


def load_entries_csv(path: Path) -> list[PendingEntry]:
    entries: list[PendingEntry] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            entries.append(
                PendingEntry(
                    def_name=row["defName"].strip(),
                    def_type=row["defType"].strip(),
                    field=row["field"].strip(),
                    source_text=row.get("sourceText", "") or "",
                    translation=row.get("translation", "") or "",
                    source_def_file=(row.get("sourceDefFile") or "").strip(),
                )
            )
    return entries


def load_entries_xml(path: Path) -> list[PendingEntry]:
    entries: list[PendingEntry] = []
    current_type = ""
    source_def_file = ""
    pending_field = ""
    pending_source = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        sec = SECTION_RE.match(line)
        if sec:
            current_type = sec.group(1).strip()
            continue
        if "sourceDefFile:" in line:
            source_def_file = line.split("sourceDefFile:", 1)[1].strip().rstrip("-").strip().rstrip("->").strip()
            continue
        parsed = parse_src_line(line)
        if parsed:
            pending_field, pending_source = parsed
            continue
        m = TAG_RE.match(line.strip())
        if not m:
            continue
        tag = m.group(1)
        if "." not in tag:
            continue
        def_name, field = tag.split(".", 1)
        comment_field = pending_field or field
        source_text = pending_source if (not pending_field or pending_field == field) else ""
        entries.append(
            PendingEntry(
                def_name=def_name,
                def_type=current_type,
                field=field,
                source_text=source_text,
                translation=m.group(2),
                source_def_file=source_def_file,
            )
        )
        pending_field = ""
        pending_source = ""
    return entries


def _write_mode_from_meta(meta: dict, write_mode: str | None, use_prefix: bool) -> tuple[bool, str]:
    if write_mode == WRITE_MODE_NEW_FILE:
        return True, (meta.get("importPrefix") or "").strip()
    if write_mode == WRITE_MODE_MERGE_EXISTING:
        return False, (meta.get("importPrefix") or "").strip()
    if use_prefix:
        return True, ""
    mode = meta.get("importWriteMode", WRITE_MODE_MERGE_EXISTING)
    prefix = (meta.get("importPrefix") or "").strip()
    return mode == WRITE_MODE_NEW_FILE, prefix


def run_import(
    input_path: Path | None = None,
    *,
    config=None,
    write_mode: str | None = None,
    prefix: str = "",
    use_prefix: bool = False,
) -> ImportResult:
    result = ImportResult(ok=False)
    try:
        if config is not None:
            target_mod = resolve_mod_path(config.target_mod, "err.specify_target_mod")
            input_path = None
            meta = None
            for ext in ("csv", "xml"):
                candidate = default_single_pending_path(target_mod, ext)
                if candidate.is_file():
                    input_path = candidate
                    meta = read_meta(find_meta_for_input(candidate))
                    break
            if input_path is None or meta is None:
                result.error_key = "err.need_pending_file"
                result.error = zh_fallback("err.need_pending_file")
                return result
        else:
            if input_path is None:
                result.error_key = "err.need_pending_file"
                result.error = zh_fallback("err.need_pending_file")
                return result
            input_path = normalize_path(input_path)
            meta = read_meta(find_meta_for_input(input_path))

        layout = meta.get("layout", EXPORT_LAYOUT_SINGLE)
        if layout == EXPORT_LAYOUT_BY_SOURCE:
            result.error_key = "err.import_by_source_not_supported"
            result.error = zh_fallback("err.import_by_source_not_supported")
            return result

        project = meta_to_config(meta)
        fmt = meta.get("format", "csv").lower()
        use_pref, meta_prefix = _write_mode_from_meta(meta, write_mode, use_prefix)
        prefix = (prefix or meta_prefix or "").strip()
        if use_pref and not prefix:
            result.error_key = "err.need_prefix"
            result.error = zh_fallback("err.need_prefix")
            return result

        entries = load_entries_csv(input_path) if fmt == "csv" else load_entries_xml(input_path)
        di_root = definjected_root(project.target_mod, project.target_lang)
        result.target_lang_path = str(di_root.parent)

        indexes: dict[str, FolderIndex] = {}
        file_blocks: dict[str, list[TagBlock]] = {}
        created: set[str] = set()

        for entry in entries:
            if not is_translated(entry.translation):
                result.skipped += 1
                continue
            if not entry.def_type or not entry.source_def_file:
                result.skipped += 1
                continue

            def_type_dir = di_root / entry.def_type
            if entry.def_type not in indexes:
                indexes[entry.def_type] = FolderIndex(def_type_dir)
            index = indexes[entry.def_type]
            tag = f"{entry.def_name}.{entry.field}"

            if tag in index.tag_values and is_translated(index.tag_values[tag]):
                result.skipped += 1
                continue

            target = resolve_target(entry, index, use_pref, prefix)
            if not target.is_file():
                created.add(str(target))

            if tag in index.tag_values and not is_translated(index.tag_values.get(tag, "")):
                update_tag(target, tag, entry.translation, entry.field, entry.source_text)
                index.refresh_file(target)
                result.updated += 1
                continue

            file_blocks.setdefault(str(target), []).append(
                (tag, entry.translation, entry.source_text, entry.field)
            )

        for file_path, blocks in file_blocks.items():
            path = Path(file_path)
            existed = path.is_file()
            insert_tags(path, blocks)
            if not existed:
                created.add(str(path))
            result.written += len(blocks)
            def_type = path.parent.name
            if def_type in indexes:
                indexes[def_type].refresh_file(path)

        result.files_created = len(created)
        result.ok = True
    except LocalizedError as e:
        set_result_error(result, e)
    except (OSError, ValueError, KeyError, csv.Error) as e:
        result.error = str(e)
    return result
