from __future__ import annotations

from pathlib import Path

from core.about_template import build_about_fields, write_about_xml
from core.errors import LocalizedError, add_result_warning, set_result_error, zh_fallback
from core.models import ProjectConfig, ScaffoldOptions, ScaffoldResult
from core.path_suggest import validate_scaffold_target
from core.paths import definjected_root, discover_defs_roots, lang_root, resolve_mod_path
from core.scan import scan_pending
from core.target_assess import assess_existing_target


def run_scaffold(config: ProjectConfig, options: ScaffoldOptions, app_title: str = "") -> ScaffoldResult:
    result = ScaffoldResult(ok=False)
    try:
        source_mod = resolve_mod_path(config.source_mod, "err.specify_source_mod")
        target_mod = resolve_mod_path(config.target_mod, "err.specify_target_mod")
        err = validate_scaffold_target(source_mod, target_mod)
        if err:
            result.error_key = err
            result.error = zh_fallback(err)
            return result

        assess = assess_existing_target(target_mod, config.target_lang)
        if assess.lang_path_exists:
            lr = lang_root(target_mod, config.target_lang)
            add_result_warning(result, "msg.scaffold.existing_lang", path=str(lr))
        if assess.about_exists:
            add_result_warning(result, "msg.scaffold.existing_about")

        defs_roots = discover_defs_roots(source_mod)
        if not defs_roots:
            result.error_key = "err.defs_not_found"
            result.error = zh_fallback("err.defs_not_found")
            return result

        pending, _, duplicate, collisions, _, _ = scan_pending(config)
        if duplicate:
            result.warnings.append(zh_fallback("msg.scaffold.duplicate_warning", count=len(duplicate)))
        if collisions:
            result.warnings.append(zh_fallback("msg.scaffold.collision_warning", count=len(collisions)))

        target_mod.mkdir(parents=True, exist_ok=True)
        di_root = definjected_root(target_mod, config.target_lang)
        def_types = sorted({e.def_type for e in pending})
        created_dirs = 0
        for def_type in def_types:
            type_dir = di_root / def_type
            if not type_dir.is_dir():
                type_dir.mkdir(parents=True, exist_ok=True)
                created_dirs += 1

        if options.create_about:
            fields = build_about_fields(
                source_mod,
                target_mod,
                config.target_lang,
                about_name=options.about_name,
                package_id=options.package_id,
                package_id_suffix=options.package_id_suffix,
                description=options.about_description,
                load_after=options.load_after or None,
                supported_versions=options.supported_versions or None,
                app_title=app_title or None,
            )
            write_about_xml(target_mod, fields)
            result.about_created = True

        result.ok = True
        result.target_mod_path = str(target_mod)
        result.lang_path = str(lang_root(target_mod, config.target_lang))
        result.files_created = created_dirs + (1 if result.about_created else 0)
        result.entries_written = 0
    except LocalizedError as e:
        set_result_error(result, e)
    except OSError as e:
        result.error = str(e)
    return result
