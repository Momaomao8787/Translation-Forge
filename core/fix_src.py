from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from core.errors import LocalizedError, set_result_error, zh_fallback
from core.field_resolve import build_def_element_map, resolve_field_text_from_maps
from core.models import ProjectConfig
from core.paths import definjected_root, discover_defs_roots, resolve_mod_path
from core.scan import build_def_map
from core.src_comment import format_src_comment

SRC_UNKNOWN_RE = re.compile(r"^\s*<!--\s*SRC\s+([^:]+)\s*:\s*\(unknown\)\s*-->\s*$")
TAG_RE = re.compile(r"^\s*<([^>]+)>(.*)</\1>\s*$")


@dataclass
class FixSrcResult:
    ok: bool
    fixed_count: int = 0
    still_unknown_count: int = 0
    files_changed: int = 0
    samples_fixed: list[str] = field(default_factory=list)
    samples_unknown: list[str] = field(default_factory=list)
    error: str = ""
    error_key: str | None = None
    error_params: dict = field(default_factory=dict)


def _fix_file(
    path: Path,
    def_map,
    element_map,
    *,
    dry_run: bool,
) -> tuple[int, int]:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    fixed = 0
    still_unknown = 0
    changed = False

    for i, line in enumerate(lines):
        m = SRC_UNKNOWN_RE.match(line.rstrip("\n"))
        if not m:
            continue
        field_path = m.group(1).strip()
        if i + 1 >= len(lines):
            continue
        tag_m = TAG_RE.match(lines[i + 1].strip())
        if not tag_m:
            continue
        tag = tag_m.group(1)
        if "." not in tag:
            continue
        def_name, tag_field = tag.split(".", 1)
        if tag_field != field_path:
            continue

        def_type = ""
        for rec in def_map.values():
            if rec.def_name == def_name:
                def_type = rec.def_type
                break

        src = resolve_field_text_from_maps(def_map, element_map, def_name, def_type, field_path)
        if not src:
            still_unknown += 1
            continue

        indent = re.match(r"^(\s*)", line)
        prefix = indent.group(1) if indent else "  "
        lines[i] = format_src_comment(field_path, src, indent=prefix) + "\n"
        fixed += 1
        changed = True

    if changed and not dry_run:
        path.write_text("".join(lines), encoding="utf-8")
    return fixed, still_unknown


def run_fix_src(config: ProjectConfig, *, dry_run: bool = False) -> FixSrcResult:
    result = FixSrcResult(ok=False)
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

        defs_roots = discover_defs_roots(source_mod)
        def_map, _ = build_def_map(source_mod, defs_roots)
        element_map = build_def_element_map(def_map, defs_roots)
        di_root = definjected_root(target_mod, config.target_lang)
        if not di_root.is_dir():
            result.error = f"DefInjected not found: {di_root}"
            return result

        for xml_file in sorted(di_root.rglob("*.xml")):
            fixed, unknown = _fix_file(xml_file, def_map, element_map, dry_run=dry_run)
            if fixed:
                result.files_changed += 1
            result.fixed_count += fixed
            result.still_unknown_count += unknown

        result.ok = True
    except LocalizedError as e:
        set_result_error(result, e)
    except OSError as e:
        result.error = str(e)
    return result
