#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Version = (Select-String -Path "pyproject.toml" -Pattern '^version = "([^"]+)"' | ForEach-Object { $_.Matches[0].Groups[1].Value })
if (-not $Version) {
    $Version = "0.0.0"
}

Write-Host "Translation Forge UI build (version $Version)"

python -m pip install -q -e ".[build]"

$DistPath = Join-Path $Root "dist"
$BuildPath = Join-Path $Root "build"
New-Item -ItemType Directory -Force -Path $DistPath | Out-Null

$LocaleSrc = Join-Path $Root "ui\i18n\locales"
$AddData = "$LocaleSrc$([IO.Path]::PathSeparator)ui\i18n\locales"

$fletArgs = @(
    "pack",
    "ui\main.py",
    "--name", "TranslationForge-UI",
    "--distpath", $DistPath,
    "--product-name", "Momaomao's Translation Forge",
    "--product-version", $Version,
    "--file-version", "$Version.0",
    "--add-data", $AddData,
    "--hidden-import", "core",
    "--hidden-import", "ui.i18n",
    "-y"
)

Write-Host "Running: flet $($fletArgs -join ' ')"
& flet @fletArgs
if ($LASTEXITCODE -ne 0) {
    Write-Warning "flet pack failed; trying PyInstaller spec fallback"
    python -m PyInstaller --noconfirm --clean TranslationForge-UI-fallback.spec
    if ($LASTEXITCODE -ne 0) {
        throw "UI build failed"
    }
}

$ExePath = Join-Path $DistPath "TranslationForge-UI.exe"
if (-not (Test-Path $ExePath)) {
    throw "Expected output not found: $ExePath"
}

Write-Host "Built: $ExePath"
