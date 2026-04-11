#Requires -Version 5.1
<#
.SYNOPSIS
    AI Memory Vault v3 — 一鍵 Inno Setup 打包腳本

.DESCRIPTION
    從 dist/vault-ai/ 產出 Windows 安裝程式：
      dist/AI-Memory-Vault-Setup-v3.4.0.exe

    前置需求：
      1. 已執行 .\build.ps1 產出 dist/vault-ai/
      2. 已安裝 Inno Setup 6.x
         下載：https://jrsoftware.org/isdl.php

.EXAMPLE
    .\build-installer.ps1
    .\build-installer.ps1 -IsccPath "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.4
@date 2026.04.06
#>

param(
    ## <summary>ISCC.exe 路徑（自動搜尋，找不到才需手動指定）</summary>
    [string]$IsccPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

#region 常數
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$IssFile     = Join-Path $ScriptDir "installer.iss"
$DistVaultAi = Join-Path $ScriptDir "..\dist\vault-ai"

# 從 installer.iss 動態讀取版本號
$AppVersion  = (Select-String -Path $IssFile -Pattern '#define AppVersion\s+"([^"]+)"').Matches[0].Groups[1].Value
$OutputExe   = Join-Path $ScriptDir "..\dist\AI-Memory-Vault-Setup-v$AppVersion.exe"

# Inno Setup 預設安裝位置（依序搜尋）
$IsccCandidates = @(
    $IsccPath,
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
)
#endregion

#region Helper
function Write-Header( [string]$Title )
{
    Write-Host ""
    Write-Host "=======================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "=======================================" -ForegroundColor Cyan
}
#endregion

Write-Header "AI Memory Vault v3 — 建立安裝程式"

# ── Step 1：確認 dist/vault-ai/ 存在 ────────────────────────
if ( -not (Test-Path $DistVaultAi) )
{
    Write-Host "[錯誤] 找不到 $DistVaultAi" -ForegroundColor Red
    Write-Host "       請先執行 .\build.ps1 產出 exe 檔案。"
    exit 1
}
$ExeCount = (Get-ChildItem $DistVaultAi -Filter "vault-*.exe").Count
if ( $ExeCount -lt 3 )
{
    Write-Host "[錯誤] dist\vault-ai\ 中只找到 $ExeCount 個 exe（需要 3 個）" -ForegroundColor Red
    Write-Host "       請重新執行 .\build.ps1 -Clean"
    exit 1
}
Write-Host "[OK] dist\vault-ai\ 包含 $ExeCount 個執行檔" -ForegroundColor Green

# ── Step 2：找到 ISCC.exe ─────────────────────────────────────
$IsccExe = $null
foreach ( $Candidate in $IsccCandidates )
{
    if ( $Candidate -and (Test-Path $Candidate) )
    {
        $IsccExe = $Candidate
        break
    }
}

if ( -not $IsccExe )
{
    Write-Host ""
    Write-Host "[未安裝] 找不到 Inno Setup 6" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  請先下載並安裝 Inno Setup 6.x：" -ForegroundColor White
    Write-Host "  https://jrsoftware.org/isdl.php" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  安裝完成後重新執行：" -ForegroundColor White
    Write-Host "  .\build-installer.ps1"
    Write-Host ""
    Write-Host "  或指定 ISCC.exe 路徑："
    Write-Host "  .\build-installer.ps1 -IsccPath 'C:\...\ISCC.exe'"
    exit 1
}
Write-Host "[OK] Inno Setup：$IsccExe" -ForegroundColor Green

# ── Step 3：執行 ISCC ────────────────────────────────────────
Write-Host ""
Write-Host "[建置] 正在編譯安裝程式..." -ForegroundColor Yellow
$StartTime = Get-Date

Push-Location $ScriptDir
& $IsccExe $IssFile
$ExitCode = $LASTEXITCODE
Pop-Location

$Duration = (Get-Date) - $StartTime

if ( $ExitCode -ne 0 )
{
    Write-Host ""
    Write-Host "[錯誤] Inno Setup 編譯失敗（exit code $ExitCode）" -ForegroundColor Red
    exit 1
}

# ── Step 4：顯示結果 ─────────────────────────────────────────
Write-Header "安裝程式建置完成！"

$SizeMB = [math]::Round( (Get-Item $OutputExe).Length / 1MB, 1 )
Write-Host ""
Write-Host "  輸出檔案：$OutputExe"
Write-Host "  檔案大小：$SizeMB MB"
Write-Host "  建置耗時：$([math]::Round($Duration.TotalSeconds))s"
Write-Host ""
Write-Host "  使用方式：" -ForegroundColor White
Write-Host "    雙擊 AI-Memory-Vault-Setup-v$AppVersion.exe → 安裝精靈"
Write-Host "    安裝後從桌面或開始功能表啟動"
Write-Host ""
Write-Host "[完成]" -ForegroundColor Green
