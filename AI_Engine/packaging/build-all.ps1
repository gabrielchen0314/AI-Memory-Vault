#Requires -Version 5.1
<#
.SYNOPSIS
    AI Memory Vault v3 — 一鍵完整打包腳本（PyInstaller + Inno Setup）

.DESCRIPTION
    依序執行：
      Step 1: PyInstaller → dist/vault-ai/  (3 個 exe)
      Step 2: Inno Setup  → dist/AI-Memory-Vault-Setup-v3.4.0.exe

    前置需求：
      - 已安裝 Inno Setup 6.x：https://jrsoftware.org/isdl.php

.PARAMETER Clean
    重新打包前先清除 build/ 與 dist/（完整重建）

.PARAMETER IsccPath
    ISCC.exe 路徑（預設自動搜尋）

.EXAMPLE
    .\build-all.ps1
    .\build-all.ps1 -Clean
#>

param(
    [switch]$Clean,
    [string]$IsccPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartTime = Get-Date

function Write-Header( [string]$Title )
{
    Write-Host ""
    Write-Host "=======================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "=======================================" -ForegroundColor Cyan
}

Write-Header "AI Memory Vault v3 — 完整打包"

# ── Step 1：PyInstaller ──────────────────────────────────────
Write-Host ""
Write-Host "[Step 1/2] PyInstaller — 打包 exe..." -ForegroundColor Yellow
& "$ScriptDir\build.ps1" @( if ($Clean) { "-Clean" } )
if ( $LASTEXITCODE -ne 0 )
{
    Write-Host "[錯誤] PyInstaller 打包失敗" -ForegroundColor Red
    exit 1
}

# ── Step 2：Inno Setup ───────────────────────────────────────
Write-Host ""
Write-Host "[Step 2/2] Inno Setup — 建立安裝程式..." -ForegroundColor Yellow
$BuildInstallerArgs = @()
if ( $IsccPath ) { $BuildInstallerArgs += "-IsccPath"; $BuildInstallerArgs += $IsccPath }
& "$ScriptDir\build-installer.ps1" @BuildInstallerArgs
if ( $LASTEXITCODE -ne 0 )
{
    exit 1
}

# ── 完成 ─────────────────────────────────────────────────────
$Duration = (Get-Date) - $StartTime
Write-Header "全部完成！"
Write-Host "  總耗時：$([math]::Round($Duration.TotalMinutes, 1)) 分鐘"
Write-Host ""
$InstallerOut = Join-Path $ScriptDir "..\dist\AI-Memory-Vault-Setup-v3.4.0.exe"
  Write-Host "  安裝程式：$InstallerOut" -ForegroundColor Green
Write-Host ""
