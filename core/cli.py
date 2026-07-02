from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

from core.export import run_export
from core.export_merge import default_single_pending_path
from core.fix_src import run_fix_src
from core.import_merge import run_import
from core.models import (
    EXPORT_LAYOUT_BY_SOURCE,
    EXPORT_LAYOUT_SINGLE,
    EXPORT_PLACEHOLDER_EMPTY,
    EXPORT_PLACEHOLDER_SOURCE,
    EXPORT_PLACEHOLDER_TODO,
    ExportOptions,
    ProjectConfig,
    ScaffoldOptions,
    WRITE_MODE_MERGE_EXISTING,
    WRITE_MODE_NEW_FILE,
)
from core.paths import validate_lang_name
from core.prefix import default_prefix
from core.scan import run_check
from core.scaffold import run_scaffold
from core.ui_locales import SUPPORTED_UI_LOCALES
from ui.i18n.translator import Translator

APP_TITLE = "Momaomao's Translation Forge"


def _config_from_args(args) -> ProjectConfig:
    return ProjectConfig(
        source_mod=Path(args.source_mod),
        target_mod=Path(args.target_mod),
        target_lang=validate_lang_name(args.lang),
    )


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value


def _localize_result(result, locale: str | None):
    if not locale:
        return result
    tr = Translator(locale)
    updates: dict = {}
    if getattr(result, "error_key", None):
        updates["error"] = tr.t(result.error_key, **getattr(result, "error_params", {}))
    message_keys = getattr(result, "message_keys", None)
    if message_keys:
        updates["messages"] = [tr.t(key, **params) for key, params in message_keys]
    warning_keys = getattr(result, "warning_keys", None)
    if warning_keys:
        updates["warnings"] = [tr.t(key, **params) for key, params in warning_keys]
    if updates:
        return replace(result, **updates)
    return result


def _emit_result(result, locale: str | None) -> None:
    payload = _json_ready(asdict(_localize_result(result, locale)))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _export_options_from_args(args) -> ExportOptions:
    return ExportOptions(
        layout=args.layout,
        placeholder=args.placeholder,
        write_mode=args.write_mode,
        prefix=args.prefix or "",
        fmt=args.format,
    )


def _scaffold_options_from_args(args) -> ScaffoldOptions:
    return ScaffoldOptions(
        create_about=args.create_about,
        about_name=getattr(args, "about_name", "") or "",
        package_id=getattr(args, "package_id", "") or "",
        package_id_suffix=getattr(args, "package_id_suffix", "") or "",
        about_description=getattr(args, "about_description", "") or "",
    )


def cmd_check(args) -> int:
    result = run_check(_config_from_args(args))
    _emit_result(result, args.locale)
    return 0 if result.ok else 1


def cmd_export(args) -> int:
    config = _config_from_args(args)
    options = _export_options_from_args(args)
    output = Path(args.output) if getattr(args, "output", None) else None
    if options.layout == EXPORT_LAYOUT_SINGLE and output is None:
        output = default_single_pending_path(config.target_mod, options.fmt)
    result = run_export(
        config,
        options,
        output,
        import_write_mode=args.import_write_mode,
        import_prefix=args.import_prefix or "",
    )
    _emit_result(result, args.locale)
    return 0 if result.ok else 1


def cmd_import(args) -> int:
    if getattr(args, "input", None):
        result = run_import(
            Path(args.input),
            write_mode=args.write_mode,
            prefix=args.prefix or "",
            use_prefix=args.use_prefix,
        )
    else:
        result = run_import(
            config=_config_from_args(args),
            write_mode=args.write_mode,
            prefix=args.prefix or "",
            use_prefix=args.use_prefix,
        )
    _emit_result(result, args.locale)
    return 0 if result.ok else 1


def cmd_default_prefix(args) -> int:
    print(default_prefix(args.source_mod))
    return 0


def cmd_scaffold(args) -> int:
    config = _config_from_args(args)
    options = _scaffold_options_from_args(args)
    result = run_scaffold(config, options, app_title=APP_TITLE)
    _emit_result(result, args.locale)
    return 0 if result.ok else 1


def cmd_fix_src(args) -> int:
    result = run_fix_src(_config_from_args(args), dry_run=args.dry_run)
    _emit_result(result, args.locale)
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="forge")
    parser.add_argument("--locale", choices=list(SUPPORTED_UI_LOCALES), default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check")
    p_check.add_argument("--source-mod", required=True)
    p_check.add_argument("--target-mod", required=True)
    p_check.add_argument("--lang", required=True)
    p_check.set_defaults(func=cmd_check)

    p_export = sub.add_parser("export")
    p_export.add_argument("--source-mod", required=True)
    p_export.add_argument("--target-mod", required=True)
    p_export.add_argument("--lang", required=True)
    p_export.add_argument("--output")
    p_export.add_argument("--format", choices=["xml", "csv"], default="xml")
    p_export.add_argument(
        "--layout",
        choices=[EXPORT_LAYOUT_SINGLE, EXPORT_LAYOUT_BY_SOURCE],
        default=EXPORT_LAYOUT_SINGLE,
    )
    p_export.add_argument(
        "--placeholder",
        choices=[EXPORT_PLACEHOLDER_TODO, EXPORT_PLACEHOLDER_EMPTY, EXPORT_PLACEHOLDER_SOURCE],
        default=EXPORT_PLACEHOLDER_TODO,
    )
    p_export.add_argument(
        "--write-mode",
        choices=[WRITE_MODE_MERGE_EXISTING, WRITE_MODE_NEW_FILE],
        default=WRITE_MODE_MERGE_EXISTING,
    )
    p_export.add_argument("--prefix", default="")
    p_export.add_argument(
        "--import-write-mode",
        choices=[WRITE_MODE_MERGE_EXISTING, WRITE_MODE_NEW_FILE],
        default=WRITE_MODE_MERGE_EXISTING,
    )
    p_export.add_argument("--import-prefix", default="")
    p_export.set_defaults(func=cmd_export)

    p_import = sub.add_parser("import")
    p_import.add_argument("--source-mod")
    p_import.add_argument("--target-mod")
    p_import.add_argument("--lang")
    p_import.add_argument("--input")
    p_import.add_argument("--use-prefix", action="store_true")
    p_import.add_argument(
        "--write-mode",
        choices=[WRITE_MODE_MERGE_EXISTING, WRITE_MODE_NEW_FILE],
        default=None,
    )
    p_import.add_argument("--prefix", default="")
    p_import.set_defaults(func=cmd_import)

    p_prefix = sub.add_parser("default-prefix")
    p_prefix.add_argument("--source-mod", required=True)
    p_prefix.set_defaults(func=cmd_default_prefix)

    p_scaffold = sub.add_parser("scaffold")
    p_scaffold.add_argument("--source-mod", required=True)
    p_scaffold.add_argument("--target-mod", required=True)
    p_scaffold.add_argument("--lang", required=True)
    about_group = p_scaffold.add_mutually_exclusive_group()
    about_group.add_argument("--create-about", dest="create_about", action="store_true")
    about_group.add_argument("--no-create-about", dest="create_about", action="store_false")
    p_scaffold.add_argument("--about-name", default="")
    p_scaffold.add_argument("--package-id", default="")
    p_scaffold.add_argument("--package-id-suffix", default="")
    p_scaffold.add_argument("--about-description", default="")
    p_scaffold.set_defaults(create_about=True, func=cmd_scaffold)

    p_fix = sub.add_parser("fix-src")
    p_fix.add_argument("--source-mod", required=True)
    p_fix.add_argument("--target-mod", required=True)
    p_fix.add_argument("--lang", required=True)
    p_fix.add_argument("--dry-run", action="store_true")
    p_fix.set_defaults(func=cmd_fix_src)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
