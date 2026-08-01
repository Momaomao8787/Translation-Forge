<p align="center">
  <a href="#zh-hant"><strong>繁體中文</strong></a>
  &nbsp;·&nbsp;
  <a href="#en"><strong>English</strong></a>
</p>

---

<a id="zh-hant"></a>

# Momaomao's Translation Forge

為 RimWorld 模組製作語言包的工具：建立新語言包、檢查缺翻、匯出待譯檔、寫回 `DefInjected`。

## 下載

不想裝 Python？到 [Releases](https://github.com/Momaomao8787/Translation-Forge/releases) 下載 **TranslationForge-UI.exe**，解壓後直接執行。

## 從原始碼安裝

需要 **Python 3.11+**。

```powershell
git clone https://github.com/Momaomao8787/Translation-Forge.git
cd Translation-Forge
pip install -e .
forge-ui
```

## 基本流程

- **從零開始**：

1. **新建語言包** — 選擇來源模組、翻譯語言與目標輸出資料夾，建立 `About` 與 `Languages/.../DefInjected` 骨架，自動匯出 CSV 或 XML 待譯檔 `DefInjected-missing.xml`。
2. 在外部編輯器填好譯文。
3. **寫回** — 將待譯檔內容寫入目標資料夾的 `DefInjected`。

- **維護現有語言包**：
1. **檢查** — 選擇來源模組與目標資料夾，檢查缺翻，匯出 CSV 或 XML 待譯檔。
2. 在外部編輯器填好譯文。
3. **寫回** — 將待譯檔內容寫入目標資料夾的 `DefInjected`。

程式會記住常用的來源模組、翻譯語言與輸出資料夾，下次開啟自動還原。

## 界面說明

頂部有三段：


| 段落    | 用途               |
| ----- | ---------------- |
| 建立待譯檔 | 檢查、匯出、寫回翻譯模組     |
| 新建語言包 | 從零開始翻譯            |
| 設定    | 切換界面語言（15 種，對齊可製作翻譯語言） |


**翻譯語言** 指 RimWorld 的 `Languages` 資料夾名稱，例如 `ChineseTraditional`、`ChineseSimplified`。

## 命令列（選用）

安裝後可用 `forge` 取代圖形界面：

```powershell
forge check --source-mod "..\原版Mod" --target-mod "..\原版Mod-TC" --lang ChineseTraditional
forge export --source-mod "..\原版Mod" --target-mod "..\原版Mod-TC" --lang ChineseTraditional
forge import --source-mod "..\原版Mod" --target-mod "..\原版Mod-TC" --lang ChineseTraditional
forge scaffold --source-mod "..\原版Mod" --target-mod "..\原版Mod-TC" --lang ChineseTraditional
```

修正 `DefInjected` 裡 SRC 註解顯示 `(unknown)` 時：

```powershell
forge fix-src --source-mod "..\原版Mod" --target-mod "..\原版Mod-TC" --lang ChineseTraditional
```

## 已知限制

`forge check`／`export` 以 DefInjected 常見字串欄位為主。下列情況可能出現「Forge 顯示 0 缺譯，遊戲 `TranslationReport` 仍報缺」：

| 類型 | 說明 | 建議 |
|------|------|------|
| 清單索引欄位 | `rulesStrings`、`stringList`、`tips` 等帶數字索引的條目多半未匯出 | 對照遊戲報告手動補進 DefInjected |
| Comp／Verb／Ingest | 如 `comps.*.gizmoLabel`／`gizmoDesc`、`chargeNoun`、`ingestible.ingestCommandString`、`WorkGiverDef.gerund`／`verb` 等常未列入 | 同上；欄位名以 Def 原文為準，含拼寫錯誤如 `gizmoLable` |
| WorkType 附加欄位 | `labelShort`、`pawnLabel`、`gerundLabel`、`verb` 可能只匯出 `description` | 手動補齊 |
| Patch 動態內容 | 僅掃靜態 `Defs/`，`Patches` 寫入的字串可能漏檢 | 進遊戲驗證報告 |
| 多版本 Def 根 | 可能一併掃到舊版子資料夾，產生與目標遊戲版本無關的偽缺 | 來源路徑盡量指向該版實際載入的 Defs；或以報告排除 |
| TC 整合語言路徑 | 預設比對 TC 根目錄 `Languages/`；`Compatibility/.../Languages` 可能未納入 | 手動指定路徑，或進遊戲驗證 |
| Verb 路徑 | 可能依 class 名產出路徑，與遊戲實際用的 label slug 不一致 | 以 TranslationReport 的實際鍵為準 |
| Keyed | 不在 DefInjected 範圍 | 另手動維護 Keyed 檔 |

定稿前請以遊戲內 **TranslationReport** 再對一次。掃描缺口的開發待辦見維護用 monorepo 內 `docs/products/forge-roadmap.md`「掃描與路徑缺口」一節。

## 授權

[MIT](LICENSE)

---

<a id="en"></a>

# Momaomao's Translation Forge

A tool for RimWorld mod localization: scaffold a language pack, find missing translations, export pending files, and import them back into `DefInjected`.

## Download

Don't want to install Python? Get **TranslationForge-UI.exe** from [Releases](https://github.com/Momaomao8787/Translation-Forge/releases) and run it.

## Install from source

Requires **Python 3.11+**.

```powershell
git clone https://github.com/Momaomao8787/Translation-Forge.git
cd Translation-Forge
pip install -e .
forge-ui
```

## Basic workflow

1. **Scaffold** — Pick the source mod, target language, and output folder. Creates `About` and `Languages/.../DefInjected` skeleton.
2. **Export** — Run a missing-translation check and export a CSV or XML pending file.
3. Fill in translations in your editor.
4. **Import** — Write translations back into the target mod's `DefInjected`.

Common paths and language choices are saved and restored on the next launch.

## UI overview

Three tabs at the top:


| Tab      | Purpose                                                          |
| -------- | ---------------------------------------------------------------- |
| Maintain | Check, export, and import for day-to-day work                    |
| Scaffold | First-time language pack setup                                   |
| Settings | UI language — 15 locales aligned with supported translation languages |


**Translation language** is the RimWorld `Languages` folder name, e.g. `ChineseTraditional` or `ChineseSimplified`.

## Command line (optional)

After install, use `forge` instead of the GUI:

```powershell
forge check --source-mod "..\SourceMod" --target-mod "..\SourceMod-TC" --lang ChineseTraditional
forge export --source-mod "..\SourceMod" --target-mod "..\SourceMod-TC" --lang ChineseTraditional
forge import --source-mod "..\SourceMod" --target-mod "..\SourceMod-TC" --lang ChineseTraditional
forge scaffold --source-mod "..\SourceMod" --target-mod "..\SourceMod-TC" --lang ChineseTraditional
```

To fix SRC comments showing `(unknown)` in `DefInjected`:

```powershell
forge fix-src --source-mod "..\SourceMod" --target-mod "..\SourceMod-TC" --lang ChineseTraditional
```

## Known limitations

`forge check` / `export` focus on common DefInjected string fields. You may see **Forge reports 0 missing** while the in-game **TranslationReport** still lists gaps:

| Kind | What happens | What to do |
|------|----------------|------------|
| Indexed list fields | Entries such as `rulesStrings`, `stringList`, and `tips` are often not exported | Add them manually in DefInjected using the game report |
| Comp / Verb / Ingest | Fields like `comps.*.gizmoLabel` / `gizmoDesc`, `chargeNoun`, `ingestible.ingestCommandString`, `WorkGiverDef.gerund` / `verb` are often omitted | Same; keep Def field names as written, including typos such as `gizmoLable` |
| Extra WorkType fields | `labelShort`, `pawnLabel`, `gerundLabel`, `verb` may be missing while only `description` is exported | Fill them manually |
| Patch-added text | Only static `Defs/` are scanned; strings added via `Patches` may be missed | Verify with the in-game report |
| Multi-version Def roots | Older version folders may be scanned, causing false missing entries for your target version | Point the source path at the Defs that version actually loads, or ignore those keys via the report |
| TC compatibility language paths | By default only the TC root `Languages/` tree is compared; `Compatibility/.../Languages` may be skipped | Pass paths manually, or verify in-game |
| Verb path handles | Paths may be built from class names instead of the label slug the game uses | Prefer the keys shown in TranslationReport |
| Keyed | Outside DefInjected scope | Maintain Keyed files separately |

Always re-check with the in-game **TranslationReport** before shipping. Developer backlog for these scan gaps lives in the monorepo file `docs/products/forge-roadmap.md` under “掃描與路徑缺口”.

## License

[MIT](LICENSE)