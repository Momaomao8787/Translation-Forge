from __future__ import annotations

from pathlib import Path

import flet as ft

from core.about_template import default_package_id
from core.export import run_export
from core.export_merge import default_single_pending_path
from core.import_merge import run_import
from core.meta import find_meta_for_input, meta_path_for, read_meta
from core.models import (
    EXPORT_LAYOUT_BY_SOURCE,
    EXPORT_LAYOUT_SINGLE,
    EXPORT_PLACEHOLDER_EMPTY,
    EXPORT_PLACEHOLDER_SOURCE,
    EXPORT_PLACEHOLDER_TODO,
    ExportOptions,
    RIMWORLD_LANGUAGES,
    ScaffoldOptions,
    WORK_MODE_MAINTAIN,
    WORK_MODE_SCAFFOLD,
    WORK_MODE_SETTINGS,
    WRITE_MODE_MERGE_EXISTING,
    WRITE_MODE_NEW_FILE,
    ProjectConfig,
)
from core.path_suggest import lang_package_suffix, suggest_target_mod_path
from core.paths import validate_lang_name, validate_lang_name_strict
from core.prefix import default_prefix
from core.scan import run_check
from core.scaffold import run_scaffold
from core.settings import parse_saved_project_settings, project_settings_for_save, save_settings
from core.target_assess import assess_existing_target
from ui.i18n import SUPPORTED_UI_LOCALES, load_ui_locale, resolve_ui_locale, save_ui_locale
from ui.i18n.formatters import format_check_messages, format_error
from ui.i18n.translator import Translator


def _config(source: str, target: str, lang: str, *, strict_lang: bool = False) -> ProjectConfig:
    validate = validate_lang_name_strict if strict_lang else validate_lang_name
    return ProjectConfig(Path(source), Path(target), validate(lang))


SOURCE_MOD_PATH_EXAMPLE = r"...\Steam\steamapps\workshop\content\294100\3686763186"
TARGET_MOD_PATH_EXAMPLE = r"...\Steam\steamapps\common\RimWorld\Mods\Example Mod"


def main(page: ft.Page) -> None:
    tr = Translator(resolve_ui_locale(load_ui_locale()))

    page.window.width = 760
    page.window.height = 820
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    state = {
        "work_mode": WORK_MODE_MAINTAIN,
        "last_workflow_mode": WORK_MODE_MAINTAIN,
        "target_manually_edited": False,
        "about_name_manually_edited": False,
        "package_id_suffix_manually_edited": False,
        "package_id_manually_edited": False,
        "pending_count": -1,
    }

    source_mod = ft.TextField(expand=True)
    target_mod = ft.TextField(expand=True)
    source_hint = ft.Text(size=11, color=ft.Colors.ON_SURFACE_VARIANT, selectable=True)
    target_hint = ft.Text(size=11, color=ft.Colors.ON_SURFACE_VARIANT, selectable=True)
    lang_path_hint = ft.Text(size=11, color=ft.Colors.ON_SURFACE_VARIANT, selectable=True, visible=False)
    check_result = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT, selectable=True, visible=False)
    workflow_status = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT, selectable=True, visible=False)

    def sync_text_visibility(text: ft.Text) -> None:
        text.visible = bool((text.value or "").strip())

    def lang_label(code: str) -> str:
        key = f"ui.lang.{code}"
        text = tr.t(key)
        return text if text != key else code

    language = ft.Dropdown(
        options=[ft.dropdown.Option(key=code, text=lang_label(code)) for code in RIMWORLD_LANGUAGES],
        value="ChineseTraditional",
        width=260,
    )
    interface_lang = ft.Dropdown(width=260)
    apply_ui_locale_btn = ft.OutlinedButton(content=tr.t("action.apply_ui_locale"))
    settings_hint = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT, selectable=True)

    work_mode_group = ft.SegmentedButton(
        selected=[WORK_MODE_MAINTAIN],
        allow_empty_selection=False,
        segments=[
            ft.Segment(value=WORK_MODE_MAINTAIN, label=tr.t("ui.work_mode.maintain")),
            ft.Segment(value=WORK_MODE_SCAFFOLD, label=tr.t("ui.work_mode.scaffold")),
            ft.Segment(value=WORK_MODE_SETTINGS, label=tr.t("ui.work_mode.settings")),
        ],
    )

    layout_group = ft.RadioGroup(
        value=EXPORT_LAYOUT_SINGLE,
        content=ft.Row(
            [
                ft.Radio(value=EXPORT_LAYOUT_SINGLE, label=tr.t("ui.export_layout.single")),
                ft.Radio(value=EXPORT_LAYOUT_BY_SOURCE, label=tr.t("ui.export_layout.by_source")),
            ]
        ),
    )
    placeholder_group = ft.RadioGroup(
        value=EXPORT_PLACEHOLDER_TODO,
        content=ft.Row(
            [
                ft.Radio(value=EXPORT_PLACEHOLDER_TODO, label=tr.t("ui.placeholder.todo")),
                ft.Radio(value=EXPORT_PLACEHOLDER_EMPTY, label=tr.t("ui.placeholder.empty")),
                ft.Radio(value=EXPORT_PLACEHOLDER_SOURCE, label=tr.t("ui.placeholder.source")),
            ]
        ),
    )
    export_write_mode_group = ft.RadioGroup(
        value=WRITE_MODE_MERGE_EXISTING,
        content=ft.Row(
            [
                ft.Radio(value=WRITE_MODE_MERGE_EXISTING, label=tr.t("ui.write_mode.merge_existing")),
                ft.Radio(value=WRITE_MODE_NEW_FILE, label=tr.t("ui.write_mode.new_file")),
            ]
        ),
    )
    import_write_mode_group = ft.RadioGroup(
        value=WRITE_MODE_MERGE_EXISTING,
        content=ft.Row(
            [
                ft.Radio(value=WRITE_MODE_MERGE_EXISTING, label=tr.t("ui.write_mode.merge_existing")),
                ft.Radio(value=WRITE_MODE_NEW_FILE, label=tr.t("ui.write_mode.new_file")),
            ]
        ),
    )
    create_about = ft.Checkbox(value=True)
    about_name_field = ft.TextField(expand=True)
    package_id_field = ft.TextField(expand=True)
    reset_path_btn = ft.TextButton(content=tr.t("ui.reset_suggested_path"))

    export_prefix_field = ft.TextField(width=220, visible=False)
    import_prefix_field = ft.TextField(width=220, visible=False)
    delete_pending = ft.Checkbox(value=False)
    pending_file = ft.TextField(expand=True, read_only=True)
    export_format = ft.RadioGroup(
        content=ft.Row([ft.Radio(value="xml", label="XML"), ft.Radio(value="csv", label="CSV")]),
        value="csv",
    )
    export_format_row = ft.Row([export_format])

    app_title = ft.Text(tr.t("app.title"), size=20, weight=ft.FontWeight.BOLD)
    check_btn = ft.Button(content=tr.t("action.check"), on_click=lambda _: run_check_click())
    build_btn = ft.Button(content=tr.t("action.build_scaffold"), on_click=lambda _: run_build_click())
    export_btn = ft.Button(content=tr.t("action.export"), on_click=lambda _: run_export_click())
    workflow_actions_row = ft.Row([check_btn, export_btn], spacing=12)
    maintain_actions_block = ft.Column([workflow_actions_row, check_result], spacing=4)
    import_btn = ft.Button(content=tr.t("action.import_write"), on_click=lambda _: run_import_click())

    scaffold_body = ft.Column(visible=False, spacing=10)
    maintain_body = ft.Column(visible=True, spacing=10)
    export_settings_body = ft.Column(spacing=10)
    import_section = ft.Column(spacing=10, visible=True)

    settings_body = ft.Column(visible=False, spacing=12)
    workflow_panel = ft.Column(spacing=8)

    about_section = ft.Column(
        spacing=8,
        controls=[
            create_about,
            ft.Row([ft.Text(tr.t("ui.about_name"), width=140), about_name_field]),
            ft.Row([ft.Text(tr.t("ui.package_id"), width=140), package_id_field]),
        ],
    )

    def is_scaffold_mode() -> bool:
        return state["work_mode"] == WORK_MODE_SCAFFOLD

    def is_settings_mode() -> bool:
        return state["work_mode"] == WORK_MODE_SETTINGS

    def update_lang_path_hint() -> None:
        lang = language.value or ""
        lang_path_hint.value = tr.t("ui.lang_path_hint", lang=lang) if lang else ""
        sync_text_visibility(lang_path_hint)

    def sync_about_fields_from_target() -> None:
        target_path = (target_mod.value or "").strip()
        if not target_path:
            return
        target = Path(target_path)
        if not state["about_name_manually_edited"]:
            about_name_field.value = target.name
        source = (source_mod.value or "").strip()
        lang = language.value or ""
        if not source or not lang:
            return
        if not package_id_field.value or not state.get("package_id_manually_edited"):
            package_id_field.value = default_package_id(Path(source), lang)

    def apply_suggested_target() -> None:
        source = (source_mod.value or "").strip()
        lang = language.value or ""
        if not source or not lang:
            return
        try:
            path, _ = suggest_target_mod_path(Path(source), lang)
            target_mod.value = str(path)
            sync_about_fields_from_target()
        except OSError:
            pass

    def apply_translations() -> None:
        page.title = tr.t("app.title")
        app_title.value = tr.t("app.title")
        source_mod.label = tr.t("ui.source_mod")
        target_mod.label = tr.t("ui.target_mod")
        source_hint.value = tr.t("ui.path_example", path=SOURCE_MOD_PATH_EXAMPLE)
        target_hint.value = tr.t("ui.path_example", path=TARGET_MOD_PATH_EXAMPLE)
        language.label = tr.t("ui.mod_language")
        language.options = [ft.dropdown.Option(key=code, text=lang_label(code)) for code in RIMWORLD_LANGUAGES]
        interface_lang.label = tr.t("ui.interface_language")
        interface_lang.options = [ft.dropdown.Option(key=loc, text=label) for loc, label in tr.locale_options()]
        interface_lang.value = tr.locale
        export_prefix_field.label = tr.t("ui.prefix")
        import_prefix_field.label = tr.t("ui.prefix")
        delete_pending.label = tr.t("ui.delete_pending")
        pending_file.label = tr.t("ui.pending_file")
        create_about.label = tr.t("ui.create_about")
        check_btn.content = tr.t("action.check")
        build_btn.content = tr.t("action.build_scaffold")
        export_btn.content = tr.t("action.export")
        import_btn.content = tr.t("action.import_write")
        apply_ui_locale_btn.content = tr.t("action.apply_ui_locale")
        settings_hint.value = tr.t("notify.restart_body")
        reset_path_btn.content = tr.t("ui.reset_suggested_path")
        work_mode_group.segments = [
            ft.Segment(value=WORK_MODE_MAINTAIN, label=tr.t("ui.work_mode.maintain")),
            ft.Segment(value=WORK_MODE_SCAFFOLD, label=tr.t("ui.work_mode.scaffold")),
            ft.Segment(value=WORK_MODE_SETTINGS, label=tr.t("ui.work_mode.settings")),
        ]
        update_lang_path_hint()

    def update_pending_path_hint() -> None:
        target = (target_mod.value or "").strip()
        lang = language.value or ""
        fmt = export_format.value or "csv"
        if target and lang:
            pending_file.value = str(default_single_pending_path(Path(target), fmt))
        else:
            pending_file.value = ""

    def export_options() -> ExportOptions:
        write_mode = export_write_mode_group.value or WRITE_MODE_MERGE_EXISTING
        prefix = export_prefix_field.value or ""
        if write_mode == WRITE_MODE_NEW_FILE and not prefix.strip():
            source = (source_mod.value or "").strip()
            if source:
                prefix = default_prefix(source)
        return ExportOptions(
            layout=layout_group.value or EXPORT_LAYOUT_SINGLE,
            placeholder=placeholder_group.value or EXPORT_PLACEHOLDER_TODO,
            write_mode=write_mode,
            prefix=prefix,
            fmt=export_format.value or "csv",
        )

    def save_project_settings() -> None:
        workflow_mode = state["work_mode"]
        if workflow_mode == WORK_MODE_SETTINGS:
            workflow_mode = state["last_workflow_mode"]
        patch = project_settings_for_save(
            source_mod.value or "",
            target_mod.value or "",
            language.value or "",
            export_format.value or "csv",
            work_mode=workflow_mode,
            create_about=bool(create_about.value),
            export_layout=layout_group.value or EXPORT_LAYOUT_SINGLE,
            export_placeholder=placeholder_group.value or EXPORT_PLACEHOLDER_TODO,
            export_write_mode=export_write_mode_group.value or WRITE_MODE_MERGE_EXISTING,
            export_prefix=export_prefix_field.value or "",
            import_write_mode=import_write_mode_group.value or WRITE_MODE_MERGE_EXISTING,
            import_prefix=import_prefix_field.value or "",
            about_name=about_name_field.value or "",
            package_id=package_id_field.value or "",
        )
        if patch:
            save_settings(patch)

    def load_project_settings() -> None:
        saved = parse_saved_project_settings()
        if saved.get("sourceMod"):
            source_mod.value = saved["sourceMod"]
        if saved.get("targetMod"):
            target_mod.value = saved["targetMod"]
            state["target_manually_edited"] = True
        if saved.get("modLanguage"):
            language.value = saved["modLanguage"]
        if saved.get("exportFormat"):
            export_format.value = saved["exportFormat"]
        if saved.get("exportLayout"):
            layout_group.value = saved["exportLayout"]
        if saved.get("exportPlaceholder"):
            placeholder_group.value = saved["exportPlaceholder"]
        if saved.get("exportWriteMode"):
            export_write_mode_group.value = saved["exportWriteMode"]
        if saved.get("exportPrefix"):
            export_prefix_field.value = saved["exportPrefix"]
        if saved.get("importWriteMode"):
            import_write_mode_group.value = saved["importWriteMode"]
        if saved.get("importPrefix"):
            import_prefix_field.value = saved["importPrefix"]
        if saved.get("workMode") in (WORK_MODE_MAINTAIN, WORK_MODE_SCAFFOLD):
            state["work_mode"] = saved["workMode"]
            state["last_workflow_mode"] = saved["workMode"]
            work_mode_group.selected = [saved["workMode"]]
        if "createAbout" in saved:
            create_about.value = saved["createAbout"]
        if saved.get("aboutName"):
            about_name_field.value = saved["aboutName"]
            state["about_name_manually_edited"] = True
        if saved.get("packageId"):
            package_id_field.value = saved["packageId"]
            state["package_id_manually_edited"] = True

    def refresh_mode_visibility() -> None:
        settings = is_settings_mode()
        scaffold = is_scaffold_mode()
        maintain = state["work_mode"] == WORK_MODE_MAINTAIN
        by_source = layout_group.value == EXPORT_LAYOUT_BY_SOURCE

        settings_body.visible = settings
        workflow_panel.visible = not settings
        scaffold_body.visible = scaffold
        maintain_body.visible = maintain
        about_section.visible = scaffold and bool(create_about.value)
        export_settings_body.visible = not settings
        import_visible = maintain and not by_source
        import_section.visible = import_visible
        maintain_body.visible = import_visible
        export_format_row.visible = not by_source
        pending_file.visible = not by_source
        export_write_mode_group.visible = maintain and by_source
        export_prefix_field.visible = maintain and by_source and export_write_mode_group.value == WRITE_MODE_NEW_FILE
        build_btn.visible = scaffold
        check_btn.visible = maintain
        if maintain and state["pending_count"] == 0:
            export_btn.visible = False
            import_section.visible = False
            maintain_body.visible = False
        else:
            export_btn.visible = maintain or scaffold
        page.update()

    def on_work_mode_change(e: ft.Event[ft.SegmentedButton]) -> None:
        selected_list = work_mode_group.selected
        if not selected_list:
            return
        selected = selected_list[0]
        state["work_mode"] = selected
        if selected in (WORK_MODE_MAINTAIN, WORK_MODE_SCAFFOLD):
            state["last_workflow_mode"] = selected
        if selected == WORK_MODE_SCAFFOLD and not state["target_manually_edited"]:
            apply_suggested_target()
        refresh_mode_visibility()

    work_mode_group.on_change = on_work_mode_change

    def apply_ui_locale_click(_):
        value = interface_lang.value
        if value not in SUPPORTED_UI_LOCALES:
            return
        if value == tr.locale:
            return
        save_ui_locale(value)
        notify(tr.t("notify.restart_title"), tr.t("notify.restart_body"))

    apply_ui_locale_btn.on_click = apply_ui_locale_click

    def on_export_write_mode_change(_):
        export_prefix_field.visible = export_write_mode_group.value == WRITE_MODE_NEW_FILE
        if export_prefix_field.visible and source_mod.value:
            export_prefix_field.value = default_prefix(source_mod.value)
        page.update()

    export_write_mode_group.on_change = on_export_write_mode_change

    def on_import_write_mode_change(_):
        import_prefix_field.visible = import_write_mode_group.value == WRITE_MODE_NEW_FILE
        if import_prefix_field.visible and source_mod.value:
            import_prefix_field.value = default_prefix(source_mod.value)
        page.update()

    import_write_mode_group.on_change = on_import_write_mode_change

    def on_layout_change(_):
        refresh_mode_visibility()

    layout_group.on_change = on_layout_change

    def on_create_about_change(_):
        refresh_mode_visibility()

    create_about.on_change = on_create_about_change

    def on_source_change(_):
        if export_write_mode_group.value == WRITE_MODE_NEW_FILE:
            export_prefix_field.value = default_prefix(source_mod.value or "")
        if import_write_mode_group.value == WRITE_MODE_NEW_FILE:
            import_prefix_field.value = default_prefix(source_mod.value or "")
        if is_scaffold_mode() and not state["target_manually_edited"]:
            apply_suggested_target()
        update_pending_path_hint()
        page.update()

    source_mod.on_change = on_source_change

    def on_target_change(_):
        state["target_manually_edited"] = True
        sync_about_fields_from_target()
        page.update()

    target_mod.on_change = on_target_change

    def on_language_change(_):
        update_lang_path_hint()
        update_pending_path_hint()
        if is_scaffold_mode():
            if not state["target_manually_edited"]:
                apply_suggested_target()
            sync_about_fields_from_target()
        page.update()

    language.on_select = on_language_change

    def on_about_name_change(_):
        state["about_name_manually_edited"] = True

    about_name_field.on_change = on_about_name_change

    def on_package_id_change(_):
        state["package_id_manually_edited"] = True

    package_id_field.on_change = on_package_id_change

    def on_reset_path(_):
        state["target_manually_edited"] = False
        state["about_name_manually_edited"] = False
        apply_suggested_target()
        page.update()

    reset_path_btn.on_click = on_reset_path

    file_picker = ft.FilePicker()
    page.file_picker = file_picker

    def close_dialog(_=None) -> None:
        page.pop_dialog()

    def notify(title: str, body: str, folder: str | None = None) -> None:
        actions: list[ft.Control] = []
        if folder and Path(folder).exists():

            def open_folder(_):
                import os

                os.startfile(folder)

            actions.append(ft.TextButton(tr.t("dialog.open_folder"), on_click=open_folder))
        actions.append(ft.TextButton(tr.t("dialog.close"), on_click=close_dialog))
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(title),
                content=ft.Text(body, selectable=True),
                actions=actions,
            )
        )

    async def pick_folder(field: ft.TextField) -> None:
        path = await file_picker.get_directory_path()
        if path:
            field.value = path
            if field is source_mod:
                if export_write_mode_group.value == WRITE_MODE_NEW_FILE:
                    export_prefix_field.value = default_prefix(path)
                if import_write_mode_group.value == WRITE_MODE_NEW_FILE:
                    import_prefix_field.value = default_prefix(path)
                if is_scaffold_mode() and not state["target_manually_edited"]:
                    apply_suggested_target()
            if field is target_mod:
                state["target_manually_edited"] = True
                sync_about_fields_from_target()
                update_pending_path_hint()
            page.update()

    def on_export_format_change(_):
        update_pending_path_hint()
        page.update()

    export_format.on_change = on_export_format_change

    def scaffold_options() -> ScaffoldOptions:
        return ScaffoldOptions(
            create_about=bool(create_about.value),
            about_name=about_name_field.value or "",
            package_id=package_id_field.value or "",
            about_description=tr.t("about.description.template", app=tr.t("app.title")),
        )

    def run_check_click():
        check_result.value = ""
        sync_text_visibility(check_result)
        try:
            cfg = _config(source_mod.value, target_mod.value, language.value or "")
            result = run_check(
                cfg,
                ui_import_mode=import_write_mode_group.value or WRITE_MODE_MERGE_EXISTING,
                import_prefix=import_prefix_field.value or "",
            )
            if not result.ok:
                notify(tr.t("notify.check_failed"), format_error(result, tr))
                return
            check_result.value = format_check_messages(result, tr)
            sync_text_visibility(check_result)
            state["pending_count"] = result.pending_count
            refresh_mode_visibility()
            save_project_settings()
        except Exception as ex:
            from core.errors import LocalizedError

            if isinstance(ex, LocalizedError):
                notify(tr.t("notify.check_failed"), tr.t(ex.key, **ex.params))
            else:
                notify(tr.t("notify.check_failed"), str(ex))
        page.update()

    def run_build_click():
        try:
            cfg = _config(source_mod.value, target_mod.value, language.value or "", strict_lang=True)
            target_path = Path(target_mod.value or "")
            assess = assess_existing_target(target_path, language.value or "")
            if assess.needs_repeat_confirm:
                pending_note = ""
                if target_path.is_dir():
                    check_preview = run_check(cfg)
                    if check_preview.ok and check_preview.pending_count > 0:
                        pending_note = tr.t("dialog.scaffold_repeat_pending", count=check_preview.pending_count)
                body = tr.t("dialog.scaffold_repeat_body", path=str(target_path))
                if pending_note:
                    body = f"{body}\n\n{pending_note}"

                def on_confirm(_):
                    page.pop_dialog()
                    do_build()

                page.show_dialog(
                    ft.AlertDialog(
                        modal=True,
                        title=ft.Text(tr.t("dialog.scaffold_repeat_title")),
                        content=ft.Text(body, selectable=True),
                        actions=[
                            ft.TextButton(tr.t("dialog.cancel"), on_click=close_dialog),
                            ft.TextButton(tr.t("dialog.scaffold_confirm_yes"), on_click=on_confirm),
                        ],
                    )
                )
                page.update()
                return
            do_build()
        except Exception as ex:
            from core.errors import LocalizedError

            if isinstance(ex, LocalizedError):
                notify(tr.t("notify.scaffold_failed"), tr.t(ex.key, **ex.params))
            else:
                notify(tr.t("notify.scaffold_failed"), str(ex))
            page.update()

    def do_build():
        try:
            cfg = _config(source_mod.value, target_mod.value, language.value or "", strict_lang=True)
            result = run_scaffold(cfg, scaffold_options(), app_title=tr.t("app.title"))
            if not result.ok:
                msg = format_error(result, tr) if result.error_key else result.error
                notify(tr.t("notify.scaffold_failed"), msg)
                return
            check_result_val = run_check(
                cfg,
                ui_import_mode=import_write_mode_group.value or WRITE_MODE_MERGE_EXISTING,
                import_prefix=import_prefix_field.value or "",
            )
            export_result = run_export(
                cfg,
                export_options(),
                import_write_mode=import_write_mode_group.value or WRITE_MODE_MERGE_EXISTING,
                import_prefix=import_prefix_field.value or "",
            )
            state["work_mode"] = WORK_MODE_MAINTAIN
            state["last_workflow_mode"] = WORK_MODE_MAINTAIN
            work_mode_group.selected = [WORK_MODE_MAINTAIN]
            if check_result_val.ok:
                check_result.value = format_check_messages(check_result_val, tr)
                sync_text_visibility(check_result)
                state["pending_count"] = check_result_val.pending_count
            workflow_status.value = tr.t(
                "notify.scaffold_done_body",
                path=result.lang_path,
                entries=export_result.entry_count if export_result.ok else 0,
                files=result.files_created,
            )
            sync_text_visibility(workflow_status)
            refresh_mode_visibility()
            save_project_settings()
            notify(
                tr.t("notify.scaffold_done"),
                workflow_status.value,
                result.lang_path,
            )
        except Exception as ex:
            from core.errors import LocalizedError

            if isinstance(ex, LocalizedError):
                notify(tr.t("notify.scaffold_failed"), tr.t(ex.key, **ex.params))
            else:
                notify(tr.t("notify.scaffold_failed"), str(ex))
        page.update()

    def run_build_click():
        do_build()

    def do_export() -> None:
        try:
            cfg = _config(source_mod.value, target_mod.value, language.value or "")
            opts = export_options()
            result = run_export(
                cfg,
                opts,
                import_write_mode=import_write_mode_group.value or WRITE_MODE_MERGE_EXISTING,
                import_prefix=import_prefix_field.value or "",
            )
            if not result.ok:
                notify(tr.t("notify.export_failed"), format_error(result, tr))
                return
            update_pending_path_hint()
            folder = str(Path(result.output_path).parent) if result.output_path else None
            notify(
                tr.t("notify.exported"),
                tr.t("export.count_body", count=result.entry_count, path=result.output_path),
                folder,
            )
            save_project_settings()
        except Exception as ex:
            from core.errors import LocalizedError

            if isinstance(ex, LocalizedError):
                notify(tr.t("notify.export_failed"), tr.t(ex.key, **ex.params))
            else:
                notify(tr.t("notify.export_failed"), str(ex))
        page.update()

    def run_export_click():
        do_export()

    def run_import_click():
        try:
            write_mode = import_write_mode_group.value or WRITE_MODE_MERGE_EXISTING
            prefix = import_prefix_field.value or ""
            if write_mode == WRITE_MODE_NEW_FILE and not prefix.strip():
                notify(tr.t("notify.import_failed"), tr.t("err.need_prefix"))
                return
            cfg = _config(source_mod.value, target_mod.value, language.value or "")
            result = run_import(config=cfg, write_mode=write_mode, prefix=prefix)
            if not result.ok:
                notify(tr.t("notify.import_failed"), format_error(result, tr))
                return
            inp = Path(pending_file.value or "")
            deleted_note = ""
            if delete_pending.value and inp.is_file():
                try:
                    meta_path = find_meta_for_input(inp)
                    inp.unlink(missing_ok=True)
                    meta_path.unlink(missing_ok=True)
                    alt_meta = inp.with_name(inp.stem + ".meta.json")
                    if alt_meta != meta_path:
                        alt_meta.unlink(missing_ok=True)
                    pending_file.value = ""
                    deleted_note = tr.t("import.deleted_pending")
                except OSError as ex:
                    deleted_note = tr.t("import.delete_failed", reason=str(ex))
            summary = tr.t(
                "import.summary",
                written=result.written,
                skipped=result.skipped,
                updated=result.updated,
                files_created=result.files_created,
            )
            notify(
                tr.t("notify.import_done"),
                f"{summary}{deleted_note}\n{result.target_lang_path}",
                result.target_lang_path,
            )
            save_project_settings()
        except Exception as ex:
            from core.errors import LocalizedError

            if isinstance(ex, LocalizedError):
                notify(tr.t("notify.import_failed"), tr.t(ex.key, **ex.params))
            else:
                notify(tr.t("notify.import_failed"), str(ex))
        page.update()

    export_settings_body.controls = [
        ft.Text(tr.t("ui.export_layout"), size=13),
        layout_group,
        ft.Text(tr.t("ui.placeholder"), size=13),
        placeholder_group,
        export_format_row,
        pending_file,
        export_write_mode_group,
        export_prefix_field,
    ]

    import_section.controls = [
        ft.Divider(),
        ft.Text(tr.t("tab.import"), size=13, weight=ft.FontWeight.BOLD),
        import_write_mode_group,
        import_prefix_field,
        delete_pending,
        import_btn,
    ]

    maintain_body.controls = [
        import_section,
    ]

    scaffold_body.controls = [
        about_section,
        workflow_status,
        build_btn,
    ]

    settings_body.controls = [
        ft.Text(tr.t("ui.interface_language"), size=13),
        ft.Row([interface_lang, apply_ui_locale_btn], alignment=ft.MainAxisAlignment.START),
        settings_hint,
    ]

    workflow_panel.controls = [
        ft.Row(
            [
                source_mod,
                ft.IconButton(
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda _: page.run_task(pick_folder, source_mod),
                ),
            ]
        ),
        source_hint,
        language,
        lang_path_hint,
        ft.Row(
            [
                target_mod,
                ft.IconButton(
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda _: page.run_task(pick_folder, target_mod),
                ),
            ]
        ),
        target_hint,
        reset_path_btn,
        export_settings_body,
        maintain_actions_block,
        maintain_body,
        scaffold_body,
    ]

    apply_translations()
    load_project_settings()
    update_lang_path_hint()
    update_pending_path_hint()
    on_export_write_mode_change(None)
    on_import_write_mode_change(None)
    if state["work_mode"] == WORK_MODE_SCAFFOLD and not state["target_manually_edited"] and source_mod.value:
        apply_suggested_target()
    refresh_mode_visibility()

    page.add(
        app_title,
        work_mode_group,
        settings_body,
        workflow_panel,
    )


def launch() -> None:
    ft.run(main)


if __name__ == "__main__":
    launch()
