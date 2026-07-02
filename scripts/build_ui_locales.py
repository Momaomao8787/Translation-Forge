from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_DIR = ROOT / "ui" / "i18n" / "locales"
sys.path.insert(0, str(ROOT))

from core.ui_locales import SUPPORTED_UI_LOCALES, UI_LOCALE_LABELS, ui_locale_setting_key

EXTRA_EN = {
    "ui.export_layout": "Layout",
    "ui.export_layout.single": "Single file",
    "ui.export_layout.by_source": "By source file",
    "ui.placeholder": "Placeholder",
    "ui.placeholder.todo": "TODO",
    "ui.placeholder.empty": "Empty",
    "ui.placeholder.source": "Source text",
    "ui.write_mode.merge_existing": "Merge into existing XML",
    "ui.write_mode.new_file": "New prefixed files",
    "err.import_by_source_not_supported": "By-source layout does not need import; edit DefInjected XML directly",
    "msg.import.done": "Written {written} · Updated {updated} · Skipped {skipped}",
    "msg.import.meta_target_mismatch": "Warning: pending metadata target differs from left column; writing to left column (metadata: {meta})",
    "msg.import.meta_source_mismatch": "Warning: pending metadata source differs from left column (metadata: {meta})",
    "msg.import.meta_lang_mismatch": "Warning: pending metadata language differs from left column; writing to left column (metadata: {meta})",
    "msg.scaffold.done": "Language scaffold created at {path}",
    "msg.fix_src.done": "Fixed {count} SRC comment(s)",
    "msg.done": "Done",
}

LANG_LABELS_BY_UI: dict[str, dict[str, str]] = {
    "en": {
        "ChineseTraditional": "Traditional Chinese",
        "ChineseSimplified": "Simplified Chinese",
        "English": "English",
        "Japanese": "Japanese",
        "Korean": "Korean",
        "Russian": "Russian",
        "French": "French",
        "German": "German",
        "Spanish": "Spanish",
        "Italian": "Italian",
        "PortugueseBrazilian": "Portuguese (Brazil)",
        "Polish": "Polish",
        "Czech": "Czech",
        "Turkish": "Turkish",
        "Ukrainian": "Ukrainian",
    },
    "zh-Hant": {
        "ChineseTraditional": "繁體中文",
        "ChineseSimplified": "簡體中文",
        "English": "English",
        "Japanese": "日文",
        "Korean": "韓文",
        "Russian": "俄文",
        "French": "法文",
        "German": "德文",
        "Spanish": "西班牙文",
        "Italian": "義大利文",
        "PortugueseBrazilian": "巴西葡萄牙文",
        "Polish": "波蘭文",
        "Czech": "捷克文",
        "Turkish": "土耳其文",
        "Ukrainian": "烏克蘭文",
    },
    "zh-Hans": {
        "ChineseTraditional": "繁体中文",
        "ChineseSimplified": "简体中文",
        "English": "English",
        "Japanese": "日文",
        "Korean": "韩文",
        "Russian": "俄文",
        "French": "法文",
        "German": "德文",
        "Spanish": "西班牙文",
        "Italian": "意大利文",
        "PortugueseBrazilian": "巴西葡萄牙文",
        "Polish": "波兰文",
        "Czech": "捷克文",
        "Turkish": "土耳其文",
        "Ukrainian": "乌克兰文",
    },
    "ja": {
        "ChineseTraditional": "繁体中国語",
        "ChineseSimplified": "簡体中国語",
        "English": "英語",
        "Japanese": "日本語",
        "Korean": "韓国語",
        "Russian": "ロシア語",
        "French": "フランス語",
        "German": "ドイツ語",
        "Spanish": "スペイン語",
        "Italian": "イタリア語",
        "PortugueseBrazilian": "ブラジルポルトガル語",
        "Polish": "ポーランド語",
        "Czech": "チェコ語",
        "Turkish": "トルコ語",
        "Ukrainian": "ウクライナ語",
    },
    "ko": {
        "ChineseTraditional": "번체 중국어",
        "ChineseSimplified": "간체 중국어",
        "English": "영어",
        "Japanese": "일본어",
        "Korean": "한국어",
        "Russian": "러시아어",
        "French": "프랑스어",
        "German": "독일어",
        "Spanish": "스페인어",
        "Italian": "이탈리아어",
        "PortugueseBrazilian": "브라질 포르투갈어",
        "Polish": "폴란드어",
        "Czech": "체코어",
        "Turkish": "터키어",
        "Ukrainian": "우크라이나어",
    },
    "ru": {
        "ChineseTraditional": "Китайский (традиционный)",
        "ChineseSimplified": "Китайский (упрощённый)",
        "English": "Английский",
        "Japanese": "Японский",
        "Korean": "Корейский",
        "Russian": "Русский",
        "French": "Французский",
        "German": "Немецкий",
        "Spanish": "Испанский",
        "Italian": "Итальянский",
        "PortugueseBrazilian": "Португальский (Бразилия)",
        "Polish": "Польский",
        "Czech": "Чешский",
        "Turkish": "Турецкий",
        "Ukrainian": "Украинский",
    },
    "fr": {
        "ChineseTraditional": "Chinois traditionnel",
        "ChineseSimplified": "Chinois simplifié",
        "English": "Anglais",
        "Japanese": "Japonais",
        "Korean": "Coréen",
        "Russian": "Russe",
        "French": "Français",
        "German": "Allemand",
        "Spanish": "Espagnol",
        "Italian": "Italien",
        "PortugueseBrazilian": "Portugais (Brésil)",
        "Polish": "Polonais",
        "Czech": "Tchèque",
        "Turkish": "Turc",
        "Ukrainian": "Ukrainien",
    },
    "de": {
        "ChineseTraditional": "Traditionelles Chinesisch",
        "ChineseSimplified": "Vereinfachtes Chinesisch",
        "English": "Englisch",
        "Japanese": "Japanisch",
        "Korean": "Koreanisch",
        "Russian": "Russisch",
        "French": "Französisch",
        "German": "Deutsch",
        "Spanish": "Spanisch",
        "Italian": "Italisch",
        "PortugueseBrazilian": "Portugiesisch (Brasilien)",
        "Polish": "Polnisch",
        "Czech": "Tschechisch",
        "Turkish": "Türkisch",
        "Ukrainian": "Ukrainisch",
    },
    "es": {
        "ChineseTraditional": "Chino tradicional",
        "ChineseSimplified": "Chino simplificado",
        "English": "Inglés",
        "Japanese": "Japonés",
        "Korean": "Coreano",
        "Russian": "Ruso",
        "French": "Francés",
        "German": "Alemán",
        "Spanish": "Español",
        "Italian": "Italiano",
        "PortugueseBrazilian": "Portugués (Brasil)",
        "Polish": "Polaco",
        "Czech": "Checo",
        "Turkish": "Turco",
        "Ukrainian": "Ucraniano",
    },
}

NATIVE_UI_LOCALES = frozenset({"ja", "ko", "ru", "fr", "de", "es"})
PLACEHOLDER_UI_LOCALES = frozenset({"it", "pt-BR", "pl", "cs", "tr", "uk"})


def _load_overlay(name: str) -> dict[str, str]:
    path = Path(__file__).with_name("locale_overlays") / f"{name}.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _locale_labels(ui_locale: str) -> dict[str, str]:
    labels = dict(LANG_LABELS_BY_UI.get(ui_locale, LANG_LABELS_BY_UI["en"]))
    for loc, native in UI_LOCALE_LABELS.items():
        labels_key = ui_locale_setting_key(loc)
    return labels


def _apply_locale_meta(table: dict[str, str], ui_locale: str) -> None:
    for loc, native in UI_LOCALE_LABELS.items():
        table[ui_locale_setting_key(loc)] = native
    lang_labels = LANG_LABELS_BY_UI.get(ui_locale, LANG_LABELS_BY_UI["en"])
    for rw_lang, label in lang_labels.items():
        table[f"ui.lang.{rw_lang}"] = label


def _write_locale(ui_locale: str, table: dict[str, str]) -> None:
    _apply_locale_meta(table, ui_locale)
    ordered = dict(sorted(table.items()))
    path = LOCALES_DIR / f"{ui_locale}.json"
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    en = json.loads((LOCALES_DIR / "en.json").read_text(encoding="utf-8"))
    hant = json.loads((LOCALES_DIR / "zh-Hant.json").read_text(encoding="utf-8"))
    hans = json.loads((LOCALES_DIR / "zh-Hans.json").read_text(encoding="utf-8"))
    en.update(EXTRA_EN)

    master_keys = sorted(set(en) | set(hant) | set(hans))
    for key in master_keys:
        if key not in en:
            en[key] = hant.get(key) or hans.get(key) or key

    for key in master_keys:
        if key not in hant and key in en:
            hant[key] = en[key]
        if key not in hans and key in en:
            hans[key] = en[key]

    _write_locale("en", en)
    _write_locale("zh-Hant", hant)
    _write_locale("zh-Hans", hans)

    for ui_locale in SUPPORTED_UI_LOCALES:
        if ui_locale in {"en", "zh-Hant", "zh-Hans"}:
            continue
        table = dict(en)
        if ui_locale in NATIVE_UI_LOCALES:
            table.update(_load_overlay(ui_locale))
        _write_locale(ui_locale, table)

    print(f"Wrote {len(SUPPORTED_UI_LOCALES)} locale files to {LOCALES_DIR}")


if __name__ == "__main__":
    main()
