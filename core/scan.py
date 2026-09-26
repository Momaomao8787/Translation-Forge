from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.check_quality import (
    find_duplicate_tags,
    find_manifest_strategy_hint,
    find_pending_format_mix,
    find_write_strategy_mix,
)
from core.errors import LocalizedError, add_result_message, add_result_warning, set_result_error, zh_fallback
from core.export_merge import default_single_pending_path
from core.field_collect import collect_fields
from core.field_resolve import build_def_element_map, index_path
from core.har_field_rules import should_skip_from_pending
from core.meta import find_meta_for_input, read_meta
from core.models import DEFAULT_FIELDS, CheckResult, DefRecord, PendingEntry, ProjectConfig
from core.def_inherit import DefIndex, build_def_index
from core.paths import (
    definjected_root,
    discover_defs_roots,
    discover_mod_subfolders,
    lang_root,
    resolve_game_version,
    resolve_mod_path,
)
from core.stale_keys import find_stale_keys, read_patch_text


def _is_translated(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return False
    if "TODO" in v.upper():
        return False
    return True


def _def_fields(node: ET.Element, allowed_fields: tuple[str, ...]) -> dict[str, str]:
    if allowed_fields == DEFAULT_FIELDS:
        return collect_fields(node)
    fields: dict[str, str] = {}
    for f in allowed_fields:
        el = node.find(f)
        if el is not None:
            fields[f] = (el.text or "").strip()
    return fields


def _source_rel(def_file: Path, source_mod: Path) -> str:
    try:
        rel = str(def_file.resolve().relative_to(source_mod.resolve()))
    except ValueError:
        rel = str(def_file)
    return rel.replace("\\", "/")


def _def_key(def_type: str, def_name: str) -> tuple[str, str]:
    return (def_type, def_name)


def _format_duplicate(def_type: str, def_name: str) -> str:
    return f"{def_type}/{def_name}"


def build_def_map(
    source_mod: Path,
    defs_roots: list[Path],
    allowed_fields: tuple[str, ...] = DEFAULT_FIELDS,
    index: DefIndex | None = None,
):
    index = index if index is not None else build_def_index(defs_roots)
    def_map: dict[tuple[str, str], DefRecord] = {}
    duplicate: list[str] = []
    for def_file, def_name, node in index.def_nodes():
        fields = _def_fields(index.resolved(node)[0], allowed_fields)
        if not fields:
            continue
        source_rel = _source_rel(def_file, source_mod)
        key = _def_key(node.tag, def_name)
        if key in def_map:
            duplicate.append(f"{_format_duplicate(node.tag, def_name)} ← 略過 {source_rel}")
            continue
        def_map[key] = DefRecord(
            def_name=def_name,
            def_type=node.tag,
            source_rel=source_rel,
            source_def_file=def_file.name,
            fields=fields,
        )
    return def_map, duplicate


def build_tr_map(definjected: Path) -> dict[str, set[str]]:
    tr_map: dict[str, set[str]] = {}
    if not definjected.is_dir():
        return tr_map
    for tr_file in definjected.rglob("*.xml"):
        try:
            tree = ET.parse(tr_file)
        except ET.ParseError:
            continue
        ld = tree.getroot()
        if ld.tag != "LanguageData":
            continue
        for child in ld:
            if not isinstance(child.tag, str) or "." not in child.tag:
                continue
            def_name, field = child.tag.split(".", 1)
            def_name = def_name.strip()
            field = field.strip()
            if not def_name or not field:
                continue
            text = child.text or ""
            if _is_translated(text):
                tr_map.setdefault(def_name, set()).add(field)
    return tr_map


def find_leaf_collisions(def_map: dict[tuple[str, str], DefRecord]) -> list[str]:
    by_type_leaf: dict[tuple[str, str], list[str]] = {}
    for rec in def_map.values():
        key = (rec.def_type, rec.source_def_file)
        by_type_leaf.setdefault(key, []).append(rec.source_rel)
    collisions = []
    for (def_type, leaf), sources in by_type_leaf.items():
        if len(set(sources)) > 1:
            collisions.append(
                f"{def_type} 的 {leaf} 對應 {len(set(sources))} 個不同來源 Def 檔"
            )
    return collisions


def _translated_index_paths(def_elem: ET.Element | None, def_type: str, fields: set[str]) -> set[str]:
    if def_elem is None or not fields:
        return set()
    paths = {index_path(def_elem, def_type, f) for f in fields}
    paths.discard(None)
    return paths


def _warning_preview(items: list[str], limit: int = 2) -> str:
    if not items:
        return ""
    preview = "；".join(items[:limit])
    if len(items) > limit:
        preview += f"；…共 {len(items)} 項"
    return preview


def scan_pending(config: ProjectConfig, allowed_fields: tuple[str, ...] = DEFAULT_FIELDS) -> tuple[list[PendingEntry], dict[tuple[str, str], DefRecord], list[str], list[str], list[Path], int]:
    source_mod = resolve_mod_path(config.source_mod, "err.specify_source_mod")
    target_mod = resolve_mod_path(config.target_mod, "err.specify_target_mod")
    defs_roots = discover_defs_roots(source_mod, resolve_game_version(config.game_version, target_mod, source_mod))
    index = build_def_index(defs_roots)
    def_map, duplicate = build_def_map(source_mod, defs_roots, allowed_fields, index)
    di_root = definjected_root(target_mod, config.target_lang)
    tr_map = build_tr_map(di_root)
    collisions = find_leaf_collisions(def_map)
    element_map = build_def_element_map(def_map, defs_roots, index) if tr_map else {}

    pending: list[PendingEntry] = []
    har_skipped = 0
    restrict_top_level = allowed_fields != DEFAULT_FIELDS
    for rec in sorted(def_map.values(), key=lambda r: (r.def_type, r.def_name)):
        translated = tr_map.get(rec.def_name, set())
        def_elem = element_map.get((rec.def_type, rec.def_name))
        translated_paths = _translated_index_paths(def_elem, rec.def_type, translated)
        keys = [f for f in allowed_fields if f in rec.fields] if restrict_top_level else sorted(rec.fields.keys())
        for field_name in keys:
            if should_skip_from_pending(rec.def_type, field_name):
                har_skipped += 1
                continue
            if field_name in translated:
                continue
            if translated_paths and index_path(def_elem, rec.def_type, field_name) in translated_paths:
                continue
            pending.append(
                PendingEntry(
                    def_name=rec.def_name,
                    def_type=rec.def_type,
                    field=field_name,
                    source_text=rec.fields[field_name],
                    translation="",
                    source_def_file=rec.source_def_file,
                )
            )
    return pending, def_map, duplicate, collisions, defs_roots, har_skipped


def run_check(
    config: ProjectConfig,
    *,
    ui_import_mode: str | None = None,
    import_prefix: str = "",
) -> CheckResult:
    result = CheckResult(ok=False)
    try:
        source_mod = resolve_mod_path(config.source_mod, "err.specify_source_mod")
        target_mod = resolve_mod_path(config.target_mod, "err.specify_target_mod")
        if not source_mod.is_dir():
            result.error_key = "err.source_mod_missing"
            result.error = zh_fallback("err.source_mod_missing")
            return result
        if not target_mod.is_dir():
            result.error_key = "err.target_mod_missing"
            result.error = zh_fallback("err.target_mod_missing")
            return result
        version = resolve_game_version(config.game_version, target_mod, source_mod)
        defs_roots = discover_defs_roots(source_mod, version)
        if not defs_roots:
            result.error_key = "err.defs_not_found"
            result.error = zh_fallback("err.defs_not_found")
            return result
        result.defs_roots = [str(p) for p in defs_roots]
        lr = lang_root(target_mod, config.target_lang)
        result.lang_path = str(lr)
        result.lang_will_create = not lr.is_dir()
        pending, def_map, duplicate, collisions, defs_roots, har_skipped = scan_pending(config)
        result.def_record_count = len(def_map)
        result.har_skipped_count = har_skipped
        result.pending_count = len(pending)
        result.duplicate_def_names = duplicate
        result.leaf_collisions = collisions
        di_root = definjected_root(target_mod, config.target_lang)
        result.duplicate_tags = find_duplicate_tags(di_root)
        result.stale_keys = find_stale_keys(
            di_root,
            build_def_index(defs_roots),
            read_patch_text(discover_mod_subfolders(source_mod, "Patches", version)),
        )
        prefix = (import_prefix or "").strip()
        if not prefix:
            for ext in ("xml", "csv"):
                candidate = default_single_pending_path(target_mod, ext)
                if candidate.is_file():
                    try:
                        meta = read_meta(find_meta_for_input(candidate))
                        prefix = (meta.get("importPrefix") or "").strip()
                        if prefix:
                            break
                    except (FileNotFoundError, OSError, ValueError):
                        pass
        result.write_strategy_mix = find_write_strategy_mix(di_root, prefix)
        add_result_message(result, "msg.check.def_records", count=result.def_record_count)
        add_result_message(result, "msg.check.pending", count=len(pending))
        if har_skipped > 0:
            add_result_message(result, "msg.check.har_skipped", count=har_skipped)
        if len(defs_roots) > 1:
            add_result_message(result, "msg.check.defs_roots", count=len(defs_roots))
        if result.lang_will_create:
            add_result_message(result, "msg.check.lang_will_create", lang=config.target_lang)
        if duplicate:
            add_result_message(result, "msg.check.duplicate_warning", count=len(duplicate))
            preview = _warning_preview(duplicate)
            if preview:
                add_result_message(result, "msg.check.warning_preview", preview=preview)
        if collisions:
            add_result_message(result, "msg.check.collision_warning", count=len(collisions))
            preview = _warning_preview(collisions)
            if preview:
                add_result_message(result, "msg.check.warning_preview", preview=preview)
        if result.duplicate_tags:
            add_result_warning(result, "msg.check.duplicate_tags", count=len(result.duplicate_tags))
            preview = _warning_preview(result.duplicate_tags)
            if preview:
                add_result_warning(result, "msg.check.warning_preview", preview=preview)
        if result.stale_keys:
            add_result_warning(result, "msg.check.stale_keys", count=len(result.stale_keys))
            preview = _warning_preview(result.stale_keys)
            if preview:
                add_result_warning(result, "msg.check.warning_preview", preview=preview)
        if result.write_strategy_mix:
            add_result_warning(result, "msg.check.write_strategy_mix", count=len(result.write_strategy_mix))
            preview = _warning_preview(result.write_strategy_mix)
            if preview:
                add_result_warning(result, "msg.check.warning_preview", preview=preview)
        if find_pending_format_mix(target_mod):
            add_result_warning(result, "msg.check.pending_format_mix")
        if ui_import_mode:
            meta = None
            for ext in ("xml", "csv"):
                candidate = default_single_pending_path(target_mod, ext)
                if candidate.is_file():
                    try:
                        meta = read_meta(find_meta_for_input(candidate))
                        break
                    except (FileNotFoundError, OSError, ValueError):
                        pass
            hint = find_manifest_strategy_hint(meta, ui_import_mode)
            if hint:
                result.strategy_hints = [hint]
                add_result_warning(result, "msg.check.strategy_hint", hint=hint)
        result.ok = True
    except LocalizedError as e:
        set_result_error(result, e)
    except OSError as e:
        result.error = str(e)
    return result
