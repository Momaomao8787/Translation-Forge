from __future__ import annotations

import csv
from pathlib import Path

from core.definjected_write import (
    FolderIndex,
    TagBlock,
    insert_tags,
    is_translated,
    resolve_target,
    update_tag,
)
from core.errors import LocalizedError, add_result_message, add_result_warning, set_result_error, zh_fallback
from core.export_merge import (
    default_single_pending_path,
    merge_pending_entries,
    placeholder_text,
)
from core.import_merge import load_entries_csv, load_entries_xml
from core.meta import meta_path_for, write_meta
from core.models import (
    EXPORT_LAYOUT_BY_SOURCE,
    EXPORT_LAYOUT_SINGLE,
    ExportOptions,
    ExportResult,
    PendingEntry,
    ProjectConfig,
    WRITE_MODE_MERGE_EXISTING,
    WRITE_MODE_NEW_FILE,
)
from core.har_field_rules import should_skip_from_pending
from core.paths import definjected_root, normalize_path, resolve_mod_path
from core.prefix import default_prefix
from core.scan import scan_pending
from core.src_comment import format_src_comment


def export_xml(output_path: Path, pending: list[PendingEntry]) -> None:
    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        "<LanguageData>",
        "",
    ]
    current_type = None
    for entry in sorted(pending, key=lambda e: (e.def_type, e.def_name, e.field)):
        if entry.def_type != current_type:
            if current_type is not None:
                lines.append("")
            lines.append(f"  <!-- ==================== {entry.def_type} ==================== -->")
            lines.append("")
            current_type = entry.def_type
        tag = f"{entry.def_name}.{entry.field}"
        lines.append(format_src_comment(entry.field, entry.source_text))
        lines.append(f"  <!-- sourceDefFile: {entry.source_def_file} -->")
        lines.append(f"  <{tag}>{entry.translation}</{tag}>")
        lines.append("")
    lines.append("</LanguageData>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_csv(output_path: Path, pending: list[PendingEntry]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["defName", "defType", "field", "sourceText", "translation", "sourceDefFile"])
        for entry in sorted(pending, key=lambda e: (e.def_type, e.def_name, e.field)):
            writer.writerow(
                [
                    entry.def_name,
                    entry.def_type,
                    entry.field,
                    entry.source_text,
                    entry.translation,
                    entry.source_def_file,
                ]
            )


def _load_old_pending(output_path: Path, fmt: str) -> list[PendingEntry]:
    if not output_path.is_file():
        return []
    if fmt == "csv":
        return load_entries_csv(output_path)
    return load_entries_xml(output_path)


def _export_single_file(
    output_path: Path,
    pending: list[PendingEntry],
    fmt: str,
) -> None:
    if fmt == "csv":
        export_csv(output_path, pending)
    else:
        export_xml(output_path, pending)


def _run_export_by_source(
    config: ProjectConfig,
    options: ExportOptions,
    pending: list[PendingEntry],
    defs_roots: list[Path],
) -> ExportResult:
    result = ExportResult(ok=False)
    try:
        target_mod = resolve_mod_path(config.target_mod, "err.specify_target_mod")
        source_mod = resolve_mod_path(config.source_mod, "err.specify_source_mod")
        use_prefix = options.write_mode == WRITE_MODE_NEW_FILE
        prefix = (options.prefix or "").strip()
        if use_prefix and not prefix:
            prefix = default_prefix(str(source_mod))
        if use_prefix and not prefix:
            result.error_key = "err.need_prefix"
            result.error = zh_fallback("err.need_prefix")
            return result

        di_root = definjected_root(target_mod, config.target_lang)
        scan_warnings: list[str] = []
        indexes: dict[str, FolderIndex] = {}
        file_blocks: dict[str, list[TagBlock]] = {}
        written = 0
        skipped = 0

        for entry in pending:
            if not entry.def_type or not entry.source_def_file:
                skipped += 1
                continue
            def_type_dir = di_root / entry.def_type
            if entry.def_type not in indexes:
                indexes[entry.def_type] = FolderIndex(def_type_dir, scan_warnings)
            index = indexes[entry.def_type]
            tag = f"{entry.def_name}.{entry.field}"
            if tag in index.tag_values and is_translated(index.tag_values[tag]):
                skipped += 1
                continue

            text = placeholder_text(options.placeholder, entry.source_text)
            target = resolve_target(entry, index, use_prefix, prefix)

            if tag in index.tag_values and not is_translated(index.tag_values.get(tag, "")):
                update_tag(target, tag, text, entry.field, entry.source_text)
                index.refresh_file(target)
                written += 1
                continue

            file_blocks.setdefault(str(target), []).append(
                (tag, text, entry.source_text, entry.field)
            )

        for file_path, blocks in file_blocks.items():
            path = Path(file_path)
            insert_tags(path, blocks)
            written += len(blocks)
            def_type = path.parent.name
            if def_type in indexes:
                indexes[def_type].refresh_file(path)

        result.ok = True
        result.output_path = str(di_root)
        result.entry_count = written
        result.meta_path = ""
        for item in scan_warnings:
            add_result_warning(result, "msg.export.bad_xml_skipped", file=item)
    except LocalizedError as e:
        set_result_error(result, e)
    except OSError as e:
        result.error = str(e)
    return result


def run_export(
    config: ProjectConfig,
    options: ExportOptions,
    output_path: Path | None = None,
    *,
    import_write_mode: str = WRITE_MODE_MERGE_EXISTING,
    import_prefix: str = "",
) -> ExportResult:
    result = ExportResult(ok=False)
    try:
        fmt = (options.fmt or "xml").lower()
        if fmt not in ("xml", "csv"):
            result.error_key = "err.invalid_format"
            result.error = zh_fallback("err.invalid_format")
            return result

        pending, _, _, _, defs_roots, har_skipped = scan_pending(config)
        layout = options.layout or EXPORT_LAYOUT_SINGLE

        if layout == EXPORT_LAYOUT_BY_SOURCE:
            if fmt != "xml":
                fmt = "xml"
            return _run_export_by_source(config, options, pending, defs_roots)

        target_mod = resolve_mod_path(config.target_mod, "err.specify_target_mod")
        out = normalize_path(output_path) if output_path else default_single_pending_path(target_mod, fmt)
        old_entries = _load_old_pending(out, fmt)
        merged = merge_pending_entries(pending, old_entries, options.placeholder)
        merged = [e for e in merged if not should_skip_from_pending(e.def_type, e.field)]
        _export_single_file(out, merged, fmt)

        meta = meta_path_for(out)
        write_meta(
            meta,
            config,
            defs_roots,
            fmt,
            layout=EXPORT_LAYOUT_SINGLE,
            placeholder=options.placeholder,
            import_write_mode=import_write_mode,
            import_prefix=import_prefix,
        )
        result.ok = True
        result.output_path = str(out)
        result.meta_path = str(meta)
        result.entry_count = len(merged)
        add_result_message(result, "msg.export.done", count=len(merged), path=str(out))
        if har_skipped > 0:
            add_result_message(result, "msg.export.har_skipped", count=har_skipped)
    except LocalizedError as e:
        set_result_error(result, e)
    except OSError as e:
        result.error = str(e)
    except ValueError as e:
        result.error = str(e)
    return result
