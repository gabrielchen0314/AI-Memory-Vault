#Requires -Version 5.1
<#
.SYNOPSIS
    AI Memory Vault v3 — 環境設定互動選單
    首次執行（無 config.json）→ 自動跑完整設定引導
    後續執行 → 顯示區段選單

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.0
@date 2026.04.04
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

#region 常數定義
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $ScriptDir "config.json"
$PythonExe  = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$MainPy     = Join-Path $ScriptDir "main.py"
#endregion

#region Helper Functions

## <summary>清除畫面並顯示標題列。</summary>
function Show-Header
{
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   AI Memory Vault v3 — 環境設定工具   " -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

## <summary>暫停並等待使用者按 Enter。</summary>
function Pause-Menu
{
    Write-Host ""
    Write-Host "按下 Enter 返回選單..." -ForegroundColor DarkGray
    $null = Read-Host
}

## <summary>檢查 Python venv 是否存在。</summary>
function Assert-Python
{
    if( -not (Test-Path $PythonExe) )
    {
        Write-Host "  ❌ 找不到 Python 虛擬環境：$PythonExe" -ForegroundColor Red
        Write-Host "     請先建立 venv：python -m venv .venv" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "按 Enter 離開"
        exit 1
    }
}

## <summary>呼叫 main.py 並傳入參數。</summary>
function Invoke-Setup( [string[]]$iArgs )
{
    & $PythonExe $MainPy @iArgs
}

#endregion

#region 選單動作

## <summary>完整設定引導（首次或重新）。</summary>
function Action-FullSetup
{
    Show-Header
    Write-Host "[ 重新完整設定 ]" -ForegroundColor Yellow
    Write-Host ""
    Invoke-Setup @( "--reconfigure" )
    Pause-Menu
}

## <summary>設定 Vault 路徑。</summary>
function Action-VaultPath
{
    Show-Header
    Write-Host "[ Vault 路徑設定 ]" -ForegroundColor Yellow
    Write-Host ""
    Invoke-Setup @( "--setup-section", "vault" )
    Pause-Menu
}

## <summary>設定使用者資訊。</summary>
function Action-UserInfo
{
    Show-Header
    Write-Host "[ 使用者資訊設定 ]" -ForegroundColor Yellow
    Write-Host ""
    Invoke-Setup @( "--setup-section", "user" )
    Pause-Menu
}

## <summary>組織管理。</summary>
function Action-OrgManage
{
    Show-Header
    Write-Host "[ 組織管理 ]" -ForegroundColor Yellow
    Write-Host ""
    Invoke-Setup @( "--setup-section", "org" )
    Pause-Menu
}

## <summary>LLM 設定。</summary>
function Action-LLM
{
    Show-Header
    Write-Host "[ LLM 設定 ]" -ForegroundColor Yellow
    Write-Host ""
    Invoke-Setup @( "--setup-section", "llm" )
    Pause-Menu
}

#endregion

#region 主程式

Assert-Python

# ── 首次執行：config.json 不存在 → 直接跑完整引導 ────────
if( -not (Test-Path $ConfigFile) )
{
    Show-Header
    Write-Host "  首次執行，將啟動完整設定引導。" -ForegroundColor Yellow
    Write-Host ""
    Invoke-Setup @( "--setup" )
    Write-Host ""
    Write-Host "  設定完成！下次啟動將顯示設定選單。" -ForegroundColor Green
    Pause-Menu
}

# ── 後續執行：顯示區段選單 ────────────────────────────────
while( $true )
{
    Show-Header
    Write-Host "  1) Vault 路徑"
    Write-Host "  2) 使用者資訊（名稱、信箱）"
    Write-Host "  3) 組織管理（新增 / 移除）"
    Write-Host "  4) LLM 設定（供應商、模型）"
    Write-Host "  5) 重新完整設定"
    Write-Host "  0) 離開"
    Write-Host ""

    $_Choice = ( Read-Host "  請選擇 (0-5)" ).Trim()

    switch( $_Choice )
    {
        "1" { Action-VaultPath }
        "2" { Action-UserInfo  }
        "3" { Action-OrgManage }
        "4" { Action-LLM       }
        "5" { Action-FullSetup }
        "0" { Write-Host "Bye!"; exit 0 }
        default
        {
            Write-Host "  ❌ 請輸入 0-5。" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}

#endregion
