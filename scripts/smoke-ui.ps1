#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$ExePath = Join-Path $Root "dist\TranslationForge-UI.exe"

if (-not (Test-Path $ExePath)) {
    Write-Host "SKIP: $ExePath not found (run scripts/build-release.ps1 first)"
    exit 0
}

$Size = (Get-Item $ExePath).Length
if ($Size -lt 1MB) {
    throw "Executable suspiciously small: $Size bytes"
}

Write-Host "OK: TranslationForge-UI.exe exists ($([math]::Round($Size / 1MB, 2)) MB)"
Write-Host "Manual: double-click to verify UI launches"
