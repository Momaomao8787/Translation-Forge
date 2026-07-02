from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORGE_ROOT = ROOT / "Momaomao's Translation Forge"
LOCALES_DIR = ROOT / "Translation Forge" / "ui" / "i18n" / "locales"
OVERLAYS_DIR = ROOT / "Translation Forge" / "scripts" / "locale_overlays"

RIMWORLD_LANGS = (
    "ChineseTraditional",
    "ChineseSimplified",
    "English",
    "Japanese",
    "Korean",
    "Russian",
    "French",
    "German",
    "Spanish",
    "Italian",
    "PortugueseBrazilian",
    "Polish",
    "Czech",
    "Turkish",
    "Ukrainian",
)

RIMWORLD_TO_UI = {
    "ChineseTraditional": "zh-Hant",
    "ChineseSimplified": "zh-Hans",
    "English": "en",
    "Japanese": "ja",
    "Korean": "ko",
    "Russian": "ru",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "PortugueseBrazilian": "pt-BR",
    "Polish": "pl",
    "Czech": "cs",
    "Turkish": "tr",
    "Ukrainian": "uk",
}

FORGE_UI_KEYS = (
    "Forge.ModTitle",
    "Forge.MainMenuEntry",
    "Forge.OpenWorkbench",
    "Forge.SettingsLaunchHint",
    "Forge.SectionWorkflow",
    "Forge.SectionPaths",
    "Forge.SectionExport",
    "Forge.SectionImport",
    "Forge.WorkModeMaintain",
    "Forge.WorkModeScaffold",
    "Forge.SourceMod",
    "Forge.TargetMod",
    "Forge.TargetModPath",
    "Forge.Language",
    "Forge.ScaffoldPathHint",
    "Forge.ScaffoldCreatePath",
    "Forge.SectionScaffold",
    "Forge.CreateAbout",
    "Forge.AboutName",
    "Forge.PackageId",
    "Forge.ScaffoldAutoExport",
    "Forge.ExportLayout",
    "Forge.ExportFormat",
    "Forge.ExportLayoutSingle",
    "Forge.ExportLayoutBySource",
    "Forge.ExportPlaceholder",
    "Forge.PlaceholderEmpty",
    "Forge.PlaceholderSource",
    "Forge.ExportWriteMode",
    "Forge.ImportWriteMode",
    "Forge.WriteModeMerge",
    "Forge.WriteModeNewFile",
    "Forge.ExportPrefix",
    "Forge.ImportPrefix",
    "Forge.CheckPending",
    "Forge.ExportPending",
    "Forge.ImportPending",
    "Forge.FixSrc",
    "Forge.OpenExportFolder",
    "Forge.DeletePendingAfterImport",
    "Forge.BuildScaffold",
    "Forge.ExternalEditHint",
    "Forge.HarExportHint",
    "Forge.HarImportHint",
    "Forge.StatusIdle",
    "Forge.StatusRunning",
    "Forge.ScaffoldRepeatTitle",
    "Forge.ScaffoldRepeatBody",
    "Forge.ScaffoldRepeatConfirm",
    "Forge.ScaffoldRepeatCancel",
)

FORGE_UI_FROM_LOCALE = {
    "Forge.ModTitle": "app.title",
    "Forge.MainMenuEntry": "Forge.MainMenuEntry",
    "Forge.OpenWorkbench": "Forge.OpenWorkbench",
    "Forge.SettingsLaunchHint": "Forge.SettingsLaunchHint",
    "Forge.SectionWorkflow": "Forge.SectionWorkflow",
    "Forge.SectionPaths": "Forge.SectionPaths",
    "Forge.SectionExport": "Forge.SectionExport",
    "Forge.SectionImport": "Forge.SectionImport",
    "Forge.WorkModeMaintain": "Forge.WorkModeMaintain",
    "Forge.WorkModeScaffold": "Forge.WorkModeScaffold",
    "Forge.SourceMod": "Forge.SourceMod",
    "Forge.TargetMod": "Forge.TargetMod",
    "Forge.TargetModPath": "Forge.TargetModPath",
    "Forge.Language": "Forge.Language",
    "Forge.ScaffoldPathHint": "Forge.ScaffoldPathHint",
    "Forge.ScaffoldCreatePath": "Forge.ScaffoldCreatePath",
    "Forge.SectionScaffold": "Forge.SectionScaffold",
    "Forge.CreateAbout": "ui.create_about",
    "Forge.AboutName": "ui.about_name",
    "Forge.PackageId": "ui.package_id",
    "Forge.ScaffoldAutoExport": "Forge.ScaffoldAutoExport",
    "Forge.ExportLayout": "ui.export_layout",
    "Forge.ExportFormat": "Forge.ExportFormat",
    "Forge.ExportLayoutSingle": "ui.export_layout.single",
    "Forge.ExportLayoutBySource": "ui.export_layout.by_source",
    "Forge.ExportPlaceholder": "ui.placeholder",
    "Forge.PlaceholderEmpty": "ui.placeholder.empty",
    "Forge.PlaceholderSource": "ui.placeholder.source",
    "Forge.ExportWriteMode": "Forge.ExportWriteMode",
    "Forge.ImportWriteMode": "Forge.ImportWriteMode",
    "Forge.WriteModeMerge": "ui.write_mode.merge_existing",
    "Forge.WriteModeNewFile": "ui.write_mode.new_file",
    "Forge.ExportPrefix": "ui.prefix",
    "Forge.ImportPrefix": "ui.prefix",
    "Forge.CheckPending": "action.check",
    "Forge.ExportPending": "action.export",
    "Forge.ImportPending": "action.import_write",
    "Forge.FixSrc": "Forge.FixSrc",
    "Forge.OpenExportFolder": "dialog.open_folder",
    "Forge.DeletePendingAfterImport": "ui.delete_pending",
    "Forge.BuildScaffold": "action.build_scaffold",
    "Forge.ExternalEditHint": "Forge.ExternalEditHint",
    "Forge.HarExportHint": "Forge.HarExportHint",
    "Forge.HarImportHint": "Forge.HarImportHint",
    "Forge.StatusIdle": "Forge.StatusIdle",
    "Forge.StatusRunning": "Forge.StatusRunning",
    "Forge.ScaffoldRepeatTitle": "dialog.scaffold_repeat_title",
    "Forge.ScaffoldRepeatBody": "dialog.scaffold_repeat_body",
    "Forge.ScaffoldRepeatConfirm": "dialog.scaffold_confirm_yes",
    "Forge.ScaffoldRepeatCancel": "dialog.cancel",
}

FORGE_UI_MANUAL = {
    "en": {
        "Forge.MainMenuEntry": "Translation Forge",
        "Forge.OpenWorkbench": "Open Translation Forge",
        "Forge.SettingsLaunchHint": "Open the full workbench from the main menu, or use the button below.",
        "Forge.SectionWorkflow": "Workflow",
        "Forge.SectionPaths": "Paths",
        "Forge.SectionExport": "Export",
        "Forge.SectionImport": "Import",
        "Forge.WorkModeMaintain": "Maintain language pack",
        "Forge.WorkModeScaffold": "New language pack",
        "Forge.SourceMod": "Source module",
        "Forge.TargetMod": "Target module",
        "Forge.TargetModPath": "Path",
        "Forge.Language": "Translation language",
        "Forge.ScaffoldPathHint": "The module name becomes the new folder name. Default location: Documents\\Rimworld Mod.",
        "Forge.ScaffoldCreatePath": "Target creation path",
        "Forge.SectionScaffold": "New language pack",
        "Forge.ScaffoldAutoExport": "Auto export after scaffold",
        "Forge.ExportFormat": "File format",
        "Forge.ExportWriteMode": "Export write mode",
        "Forge.ImportWriteMode": "Import write mode",
        "Forge.FixSrc": "Fix SRC comments",
        "Forge.ExternalEditHint": "Edit the pending file in an external editor. Writeback applies translations to DefInjected in the translation module and language selected in the left column—not the source module.",
        "Forge.HarExportHint": "This source includes HAR races. Forge auto-skips color channel names, body addon identifiers, and similar technical keys—do not add them to the pending file manually.",
        "Forge.HarImportHint": "If the pending file contains colorChannels or bodyAddons technical keys, keep the English source values on writeback or addon textures may break.",
        "Forge.StatusIdle": "Ready.",
        "Forge.StatusRunning": "Running…",
    },
    "zh-Hant": {
        "Forge.MainMenuEntry": "翻譯鍛造台",
        "Forge.OpenWorkbench": "開啟翻譯鍛造台",
        "Forge.SettingsLaunchHint": "完整工作台可從主選單進入，或點下方按鈕開啟。",
        "Forge.SectionWorkflow": "工作模式",
        "Forge.SectionPaths": "路徑",
        "Forge.SectionExport": "匯出",
        "Forge.SectionImport": "寫回",
        "Forge.WorkModeMaintain": "維護現有語言包",
        "Forge.WorkModeScaffold": "新建語言包",
        "Forge.SourceMod": "來源模組",
        "Forge.TargetMod": "翻譯模組",
        "Forge.TargetModPath": "路徑",
        "Forge.Language": "翻譯語言",
        "Forge.ScaffoldPathHint": "模組名稱即將建立的資料夾名稱。預設建立在「文件\\Rimworld Mod」。",
        "Forge.ScaffoldCreatePath": "目標建立路徑",
        "Forge.SectionScaffold": "新建語言包",
        "Forge.ScaffoldAutoExport": "建立後自動匯出待譯檔",
        "Forge.ExportFormat": "檔案格式",
        "Forge.ExportWriteMode": "匯出寫入策略",
        "Forge.ImportWriteMode": "寫回策略",
        "Forge.FixSrc": "修正 SRC 註解",
        "Forge.ExternalEditHint": "請在外部編輯器修改待譯檔。寫回會將譯文寫入左欄所選翻譯模組與翻譯語言的 DefInjected，而非來源模組。",
        "Forge.HarExportHint": "此來源含 HAR 種族。Forge 會自動略過著色通道名稱、附加部位識別碼等技術鍵，勿手動加入待譯檔。",
        "Forge.HarImportHint": "若待譯檔含 colorChannels 或 bodyAddons 技術鍵，寫回時須保留英文原值，否則附加貼圖可能失效。",
        "Forge.StatusIdle": "就緒。",
        "Forge.StatusRunning": "執行中…",
    },
    "zh-Hans": {
        "Forge.MainMenuEntry": "翻译锻造台",
        "Forge.OpenWorkbench": "开启翻译锻造台",
        "Forge.SettingsLaunchHint": "完整工作台可从主菜单进入，或点下方按钮开启。",
        "Forge.SectionWorkflow": "工作模式",
        "Forge.SectionPaths": "路径",
        "Forge.SectionExport": "导出",
        "Forge.SectionImport": "写回",
        "Forge.WorkModeMaintain": "维护现有语言包",
        "Forge.WorkModeScaffold": "新建语言包",
        "Forge.SourceMod": "来源模组",
        "Forge.TargetMod": "翻译模组",
        "Forge.TargetModPath": "路径",
        "Forge.Language": "翻译语言",
        "Forge.ScaffoldPathHint": "模组名称即将建立的文件夹名称。默认建立在「文档\\Rimworld Mod」。",
        "Forge.ScaffoldCreatePath": "目标建立路径",
        "Forge.SectionScaffold": "新建语言包",
        "Forge.ScaffoldAutoExport": "建立后自动导出待译档",
        "Forge.ExportFormat": "文件格式",
        "Forge.ExportWriteMode": "导出写入策略",
        "Forge.ImportWriteMode": "写回策略",
        "Forge.FixSrc": "修正 SRC 注释",
        "Forge.ExternalEditHint": "请在外部编辑器修改待译档。写回会将译文写入左栏所选翻译模组与翻译语言的 DefInjected，而非来源模组。",
        "Forge.HarExportHint": "此来源含 HAR 种族。Forge 会自动略过着色通道名称、附加部位识别码等技术键，勿手动加入待译档。",
        "Forge.HarImportHint": "若待译档含 colorChannels 或 bodyAddons 技术键，写回时须保留英文原值，否则附加贴图可能失效。",
        "Forge.StatusIdle": "就绪。",
        "Forge.StatusRunning": "执行中…",
    },
}


def to_forge_key(internal: str) -> str:
    parts = internal.split(".")
    out = "Forge."
    for part in parts:
        for segment in part.split("_"):
            if not segment:
                continue
            out += segment[0].upper() + segment[1:]
    return out


def load_table(ui_locale: str) -> dict[str, str]:
    table = json.loads((LOCALES_DIR / f"{ui_locale}.json").read_text(encoding="utf-8"))
    overlay_path = OVERLAYS_DIR / f"{ui_locale}.json"
    if overlay_path.is_file():
        table.update(json.loads(overlay_path.read_text(encoding="utf-8")))
    manual = FORGE_UI_MANUAL.get(ui_locale, {})
    return table


def forge_ui_text(forge_key: str, ui_locale: str, table: dict[str, str]) -> str:
    manual = FORGE_UI_MANUAL.get(ui_locale, {})
    if forge_key in manual:
        return manual[forge_key]
    if forge_key.startswith("Forge."):
        mo_key = f"mo_ui.{forge_key}"
        if mo_key in table:
            return table[mo_key]
    locale_key = FORGE_UI_FROM_LOCALE.get(forge_key)
    if locale_key and locale_key in table:
        text = table[locale_key]
        if forge_key == "Forge.ScaffoldRepeatBody":
            text = text.replace("{path}", "{0}")
        return text
    en = load_table("en")
    locale_key = FORGE_UI_FROM_LOCALE.get(forge_key)
    if locale_key and locale_key in en:
        return en[locale_key]
    return forge_key


def message_keys(table: dict[str, str]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key, value in sorted(table.items()):
        if key.startswith("err.") or key.startswith("msg."):
            rows.append((to_forge_key(key), value))
    return rows


def write_keyed(path: Path, entries: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>"]
    for keyed, text in entries:
        escaped = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "\\n")
        )
        lines.append(f"\t<{keyed}>{escaped}</{keyed}>")
    lines.append("</LanguageData>")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_about_locale_texts_cs(path: Path) -> None:
    lines = [
        "// Generated by scripts/generate_mo_keyed.py. Do not edit.",
        "using System.Collections.Generic;",
        "",
        "namespace Momaomao.TranslationForge.ForgeCore",
        "{",
        "    public static class AboutLocaleTexts",
        "    {",
        "        private static readonly Dictionary<string, string> ByLang = new Dictionary<string, string>",
        "        {",
    ]
    for rw_lang in RIMWORLD_LANGS:
        ui_locale = RIMWORLD_TO_UI[rw_lang]
        table = load_table(ui_locale)
        text = table.get("about.description.template") or load_table("en").get(
            "about.description.template", ""
        )
        escaped = text.replace("\\", "\\\\").replace("\"", "\\\"")
        lines.append(f'            ["{rw_lang}"] = "{escaped}",')
    lines.extend(
        [
            "        };",
            "",
            "        public static string DefaultDescription(string rimworldLang)",
            "        {",
            "            if (!string.IsNullOrEmpty(rimworldLang) && ByLang.TryGetValue(rimworldLang, out var text))",
            "            {",
            "                return text;",
            "            }",
            "            return ByLang[\"English\"];",
            "        }",
            "    }",
            "}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    about_cs = FORGE_ROOT / "Source" / "TranslationForge" / "ForgeCore" / "AboutLocaleTexts.cs"
    write_about_locale_texts_cs(about_cs)
    for rw_lang in RIMWORLD_LANGS:
        ui_locale = RIMWORLD_TO_UI[rw_lang]
        table = load_table(ui_locale)
        forge_entries = [(key, forge_ui_text(key, ui_locale, table)) for key in FORGE_UI_KEYS]
        base = FORGE_ROOT / "Languages" / rw_lang / "Keyed"
        write_keyed(base / "Forge.xml", forge_entries)
        write_keyed(base / "ForgeMessages.xml", message_keys(table))
        print(rw_lang, ui_locale, len(forge_entries), len(message_keys(table)))


if __name__ == "__main__":
    main()
