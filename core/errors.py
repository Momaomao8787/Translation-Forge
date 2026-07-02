from __future__ import annotations

_ZH_FALLBACK: dict[str, str] = {
    "err.specify_source_mod": "請指定來源 Mod",
    "err.specify_target_mod": "請指定目標 Mod",
    "err.invalid_lang_name": "語言名稱無效",
    "err.source_mod_missing": "來源 Mod 不存在",
    "err.target_mod_missing": "目標 Mod 不存在",
    "err.defs_not_found": "找不到 Defs",
    "err.invalid_format": "格式必須為 xml 或 csv",
    "err.need_prefix": "請輸入前綴",
    "err.metadata_not_found": "找不到待譯檔 metadata",
    "err.need_output_path": "請指定輸出路徑",
    "err.need_pending_file": "請選擇待譯檔",
    "err.scaffold_target_same_as_source": "目標 Mod 必須與來源不同",
    "err.scaffold_target_inside_source": "目標不可位於來源 Mod 目錄內",
    "err.scaffold_target_is_file": "目標路徑是檔案而非資料夾",
    "err.scaffold_parent_not_writable": "目標父目錄無寫入權限",
    "err.scaffold_parent_not_writable_hint": "請改開坑到可寫入的資料夾，或以系統管理員執行",
    "err.import_by_source_not_supported": "依原版分檔不需寫回，請直接在 DefInjected XML 內修改",
    "msg.scaffold.duplicate_warning": "警告：{count} 個同類型同名 Def 重複",
    "msg.scaffold.collision_warning": "警告：{count} 項檔名可能混淆",
    "msg.scaffold.existing_lang": "警告：已存在語言路徑 {path}，將僅補缺",
    "msg.check.scanned_defs": "已掃描 {count} 處 Defs",
    "msg.check.def_records": "共掃描 {count} 個 Def",
    "msg.check.pending": "尚待翻譯 {count} 條",
    "msg.check.har_skipped": "已略過 {count} 條 HAR 技術鍵（著色通道、附加部位識別碼等，勿翻譯）",
    "msg.check.defs_roots": "Defs 根目錄 {count} 處",
    "msg.check.lang_will_create": "寫回時將建立 Languages/{lang}/",
    "msg.check.duplicate_warning": "警告：{count} 個同類型同名 Def 重複，匯出只保留先掃到的定義",
    "msg.check.collision_warning": "警告：{count} 項寫回檔名可能混淆（同一 DefType 內多個來源共用 leaf 檔名）",
    "msg.check.warning_preview": "{preview}",
    "msg.check.duplicate_tags": "警告：{count} 個 DefInjected 檔內有重複 tag",
    "msg.check.write_strategy_mix": "警告：{count} 個 tag 同時出現於前綴檔與非前綴檔",
    "msg.check.strategy_hint": "警告：待譯檔 manifest 寫入策略與目前設定不一致（{hint}）",
    "msg.check.pending_format_mix": "警告：同時存在 CSV 與 XML 待譯檔，請勿混用格式",
    "msg.scaffold.existing_about": "警告：已存在 About.xml，建立時可能覆寫",
    "msg.export.bad_xml_skipped": "警告：略過無法讀取的 XML：{file}",
    "msg.export.done": "已匯出 {count} 條至 {path}",
    "msg.export.har_skipped": "已略過 {count} 條 HAR 技術鍵，未列入待譯檔",
    "msg.import.har_blocked": "警告：略過 {count} 條 HAR 技術鍵譯文（須保留英文原值，否則附加貼圖可能失效）",
}


class LocalizedError(ValueError):
    def __init__(self, key: str, **params: object) -> None:
        self.key = key
        self.params = params
        super().__init__(key)


def zh_fallback(key: str, **params: object) -> str:
    template = _ZH_FALLBACK.get(key, key)
    try:
        return template.format(**params)
    except KeyError:
        return template


def set_result_error(result, error: LocalizedError) -> None:
    result.error_key = error.key
    result.error_params = dict(error.params)
    result.error = zh_fallback(error.key, **error.params)


def add_result_message(result, key: str, **params: object) -> None:
    result.message_keys.append((key, dict(params)))
    result.messages.append(zh_fallback(key, **params))


def add_result_warning(result, key: str, **params: object) -> None:
    result.warning_keys.append((key, dict(params)))
    if hasattr(result, "warnings"):
        result.warnings.append(zh_fallback(key, **params))


def format_error_with_hints(result, tr=None) -> str:
    if getattr(result, "error_key", None):
        if tr is not None:
            msg = tr.t(result.error_key, **getattr(result, "error_params", {}))
        else:
            msg = zh_fallback(result.error_key, **getattr(result, "error_params", {}))
        hint_key = f"{result.error_key}_hint"
        if tr is not None:
            hint = tr.t(hint_key)
            if hint != hint_key:
                return f"{msg}\n{hint}"
        elif hint_key in _ZH_FALLBACK:
            return f"{msg}\n{_ZH_FALLBACK[hint_key]}"
        return msg
    return getattr(result, "error", "") or (tr.t("err.unknown") if tr else zh_fallback("err.unknown"))
