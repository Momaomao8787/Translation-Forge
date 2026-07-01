# Momaomao's Translation Forge

RimWorld 模組語言包開坑與 `DefInjected` 往返工具。目前版本 **0.7.4**。Steam 伴侶 Mod 規劃中。

## 安裝

```powershell
git clone https://github.com/Momaomao8787/Translation-Forge.git
cd Translation-Forge
pip install -e .
forge-ui
```

僅使用 CLI：`pip install -e .` 後執行 `forge` 或 `python -m core.cli`。

## 版本摘要

- **0.7.4** — 獨立 repo 發布；UI 文案與版面調整、`forge-ui` 入口修正
- **0.7.3** — Flet UI exe 建置腳本
- **0.7.1** — 邊際情況：重複建立確認、check 品質警告、manifest 相容
- **0.7.0** — 工作流重構：`single` / `by_source`、固定待譯檔、scaffold 縮小
- **0.6.x** — `scaffold`、巢狀 Def 欄位、`fix-src`
- **0.5.x** — 新建語言骨架、About 模板、路徑建議
- **0.4.x** — 專案設定記憶、CLI `--locale`
- **0.3.x** — 界面多語 Flet
- **0.2.x** — 寫回時自動插入 SRC 註解

## 邊際情況 0.7.1

- **重複建立**：Flet「建立語言包」與伴侶 Mod 在目標已含 About 或 `Languages` 時會先確認；CLI `scaffold` 仍直接執行。
- **check 警告**：重複 tag、前綴／非前綴混用、manifest 寫入策略與 UI 不一致、CSV 與 XML 待譯檔混用。
- **舊 manifest**：`usePrefix: true` 會遷移為 `importWriteMode: new_file` 與 `importPrefix`。
- **by_source**：格式錯誤的 DefInjected XML 略過並警告，不 crash。

## 需求

- Python 3.11+
- 桌面 UI：**Flet** — `pip install -e .` 後 `forge-ui` 或 `python -m ui.main`

## CLI

在專案根目錄：

```powershell
python -m core.cli check --source-mod "..\Monolyn Race" --target-mod "..\Monolyn-Race-TC" --lang ChineseTraditional
python -m core.cli --locale en check --source-mod "..." --target-mod "..." --lang ChineseTraditional
python -m core.cli export --source-mod "..." --target-mod "..." --lang ChineseTraditional --format csv
python -m core.cli export --source-mod "..." --target-mod "..." --lang ChineseTraditional --layout by_source --placeholder todo
python -m core.cli import --source-mod "..." --target-mod "..." --lang ChineseTraditional
python -m core.cli import --input pending.csv --write-mode new_file --prefix Monolyn_Race
python -m core.cli default-prefix --source-mod "..\Monolyn Race"
python -m core.cli scaffold --source-mod "..." --target-mod "..." --lang ChineseTraditional --create-about --about-name "Monolyn Race-TC"
python -m core.cli fix-src --source-mod "..\2549028560" --target-mod "..\Moosesian-Race-TC" --lang ChineseTraditional
python -m core.cli fix-src --dry-run --source-mod "..." --target-mod "..." --lang ChineseTraditional
```

`export` 預設寫入目標 Mod 根目錄 `DefInjected-missing.{csv|xml}`；`--layout by_source` 直寫 `Languages/.../DefInjected/`。`import` 可省略 `--input`，改以固定待譯檔路徑讀取。`scaffold` 僅建立 About 與空 `DefType` 目錄，不寫譯文 tag。

`fix-src` 會掃描目標 Mod 的 `DefInjected`，將 `<!-- SRC …: (unknown) -->` 依原版 Defs 巢狀路徑解析後改寫。`--dry-run` 只統計不寫檔。

`--locale` 可選 `zh-Hant`、`zh-Hans`、`en`。未指定時 JSON 的 `error` / `messages` / `warnings` 仍為繁中；`error_key` / `message_keys` / `warning_keys` 始終保留。

## 桌面 UI

### Flet（Python 原生）

```powershell
pip install -e .
python -m ui.main
```

或：

```powershell
forge-ui
```

### Windows UI exe 建置

無 Python 環境時可建置獨立桌面程式，行為與 `forge-ui` 相同。

**需求**：Python 3.11+、Windows。

```powershell
pip install -e ".[build]"
powershell -ExecutionPolicy Bypass -File scripts\build-release.ps1
```

產物：

- `dist/TranslationForge-UI.exe`
- `dist/SHA256SUMS.txt`

驗證（可選）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-ui.ps1
```

`flet pack` 失敗時腳本會改用 `TranslationForge-UI-fallback.spec`。本機實測環境：Python 3.11、flet 0.85+。`dist/` 不納入 git；發佈可上傳 GitHub Releases。

## 設定記憶

Flet UI 會將常用專案欄位寫入 `%APPDATA%\RimworldDefInjectTranslator\settings.json`：

- 來源 Mod、目標 Mod、Mod 語言、匯出格式、版面、佔位符、寫入策略
- 與界面語言 `uiLocale` 共用同一檔案
- 在 **檢查**、**匯出**、**寫回** 成功後更新
- **不記**待譯檔路徑

重啟 Momaomao's Translation Forge 後會自動還原上述欄位。

## 0.5 新建語言包

Flet UI 頂部 **SegmentedButton 三段**：

| 段 | 值 | 內容 |
|----|-----|------|
| 建立待譯檔 | `maintain` | 來源／目標／翻譯語言、檢查、匯出／寫回 |
| 新建語言包 | `scaffold` | 開坑選項、About、建立語言包 |
| 設定 | `settings` | 界面語言；**不寫入** `workMode` |

新建流程：

1. 選 **來源 Mod**（含 Defs 的原版）
2. 選 **翻譯語言**（RimWorld 官方 `Languages/` 資料夾名）
3. 確認 **目標 Mod**（預設 `{RimWorld Mods}/{原名}-{語言簡寫}`，如 `Monolyn Race-TC`）
4. **建立語言包**（目標已存在時會先確認）
5. 建立後自動切換維護模式並執行檢查、匯出

產物結構：

```text
{目標 Mod}/
  About/About.xml          ← 進階設定可關閉
  Languages/<語言>/DefInjected/...
```

**packageId** 預填 `{來源 packageId}.{語言簡寫}`（繁中 `TC`、簡中 `ZH`、日文 `JP`…）。**模組名稱** 預填目標資料夾名。

**Mods 路徑偵測**：來源在 Workshop 或 `RimWorld\Mods` 下時建議到遊戲 `Mods` 資料夾；否則 fallback 與來源同層。

CLI 亦支援 `scaffold`，見上方 CLI 章節。

## Flet API 踩坑

| 問題 | 正確寫法 |
|------|----------|
| `SegmentedButton.selected` | 必須 `list[str]`，**不可** `set` |
| `ExpansionTile` 預設收合 | `expanded=False`，**無** `initially_expanded` |
| `Dropdown` 選項變更 | `on_select`，**非** `on_change` |
| 啟動驗證 | `pytest tests/test_ui_startup.py` |

改 Flet UI 後跑 `pytest tests`；重大 UI 變更應本地 `forge-ui` 確認。

## 核心模組

| 路徑 | 用途 |
|------|------|
| `core/scaffold.py` | `run_scaffold` |
| `core/path_suggest.py` | Mods 偵測、建議路徑 |
| `core/about_template.py` | About 欄位推導 |
| `core/field_collect.py` | 遞迴發現巢狀可譯路徑 |
| `core/field_resolve.py` | 依 Def 解析巢狀欄位原文 |
| `core/fix_src.py` | 批次修正 SRC `(unknown)` |
| `ui/main.py` | Flet 主界面 |

## 語言下拉

`ChineseTraditional` → `ChineseSimplified` → `English` → `Japanese` → `Korean` → `Russian` → `French` → `German` → `Spanish` → `Italian` → `PortugueseBrazilian` → `Polish` → `Czech` → `Turkish` → `Ukrainian`

## 前綴檔

勾選「寫入獨立前綴檔」時，檔名為 `{前綴}_{原Def檔名}.xml`，預設前綴取自**來源 Mod** 資料夾名稱（空白改 `_`、移除非法字元）。

## 待譯檔

Tab2「待譯檔」為 Tab1 匯出的 CSV 或 XML，填完譯文後選同一檔案寫回。寫入路徑以檔內 `.meta.json` metadata 為準。

## SRC 註解

寫回 `DefInjected` 時，每個譯文標籤前會插入一行 SRC 對照註解：

```xml
  <!-- SRC label: Sample Thing -->
  <SampleThing.label>範例物品</SampleThing.label>
```

- 原文來自來源 Mod 的 Defs；空原文寫為 `(empty)`
- 待譯 XML 另含 `sourceDefFile` 註解供路由，**不會**寫入 DefInjected
- 讀取待譯檔時相容舊版 `field:` 與 `EN:` 註解

## 掃描規則

對照目標 Mod 的 `Languages/<語言>/DefInjected`：空字串、含 `TODO` 或不存在者視為待譯。

## 界面語言

Momaomao's Translation Forge **視窗文案**與檢查／錯誤訊息支援三種界面語言：`zh-Hant`、`zh-Hans`、`en`。

- **首次啟動**：依系統 UI 語言自動選擇
- **手動切換**：選擇界面語言後按「套用」，寫入設定檔並提示重新啟動
- 與 Mod 翻譯用的「語言」下拉（`ChineseTraditional` 等）**無關**

## 限制

- 掃描含 Def **頂層**與常見**巢狀**可譯路徑；`tools/*`、`verbs/*`、`comps/*`、`stages/*` 等。ImpliedDefs 或 Patch 衍生、原版 Defs 無對應節點者仍可能 `(unknown)`。
- 無 Keyed、無 validate / normalize 命令
- 無 metadata 的舊版待譯檔拒絕寫入
- 既有已譯但未補 SRC 的條目不會自動批次補註解

## 版本路線

目前 **0.7.4**。後續：fix-src UI、Steam 伴侶 Mod 與 C# 核心移植。

## 測試

```powershell
pip install pytest
python -m pytest tests -q
```

## 目錄結構

```text
core/          Python 掃描、匯出、寫回、开坑
core/path_suggest.py  目標 Mod 路徑建議
core/scaffold.py      新建語言骨架
core/about_template.py  About 模板
core/settings.py  共用設定持久化
ui/            Flet 桌面 UI
ui/i18n/       界面語言與字串檔
tests/         fixture 與 pytest
scripts/       build-ui.ps1、build-release.ps1、smoke-ui.ps1
```
