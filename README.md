**[繁體中文](#zh-hant)**  ·  **[English](#en)**

---



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

1. **新建語言包** — 選原版 Mod、翻譯語言與目標資料夾，建立 `About` 與 `Languages/.../DefInjected` 骨架。
2. **建立待譯檔** — 檢查缺翻，匯出 CSV 或 XML 待譯檔。
3. 在外部編輯器填好譯文。
4. **寫回** — 將待譯檔內容寫入目標 Mod 的 `DefInjected`。

程式會記住常用的來源 Mod、目標 Mod 與語言設定，下次開啟自動還原。

## 界面說明

頂部有三段：


| 段落    | 用途               |
| ----- | ---------------- |
| 建立待譯檔 | 檢查、匯出、寫回日常維護     |
| 新建語言包 | 第一次開坑            |
| 設定    | 切換界面語言（繁中／简中／英文） |


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

## 授權

[MIT](LICENSE)

---



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
| Settings | UI language (Traditional Chinese / Simplified Chinese / English) |


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

## License

[MIT](LICENSE)