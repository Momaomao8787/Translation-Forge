#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

& (Join-Path $PSScriptRoot "build-ui.ps1")

$DistPath = Join-Path $Root "dist"
$ExePath = Join-Path $DistPath "TranslationForge-UI.exe"
if (-not (Test-Path $ExePath)) {
    throw "Release build missing: $ExePath"
}

$HashPath = Join-Path $DistPath "SHA256SUMS.txt"
$Hash = (Get-FileHash -Path $ExePath -Algorithm SHA256).Hash.ToLowerInvariant()
$Line = "$Hash  TranslationForge-UI.exe"
[System.IO.File]::WriteAllText($HashPath, $Line + "`n")

Write-Host "Checksum: $HashPath"
Get-Content $HashPath
