#Requires -Version 5.1
<#
.SYNOPSIS
    AI Memory Vault v3 — 一鍵 PyInstaller 打包腳本

.DESCRIPTION
    產出 dist/vault-ai/ 目錄，內含三個可執行檔：
      vault-cli.exe       互動式 CLI（雙擊或命令列使用）
      vault-mcp.exe       MCP Server（供 VS Code / Claude Desktop 設定）
      vault-scheduler.exe APScheduler 排程守護模式

    所有 .exe 共用同一份 library 目錄，節省磁碟空間。

.EXAMPLE
    .\build.ps1
    .\build.ps1 -Clean       # 清除舊的 build/ dist/ 後重新打包

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.4
@date 2026.04.06
#>

param(
    ## <summary>打包前清除 build/ 和 dist/ 目錄</summary>
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

#region 常數定義
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython  = Join-Path $ScriptDir "..\.venv\Scripts\python.exe"
$VenvPip     = Join-Path $ScriptDir "..\.venv\Scripts\pip.exe"
$SpecFile    = Join-Path $ScriptDir "build.spec"
$DistDir     = Join-Path $ScriptDir "..\dist\vault-ai"
#endregion

#region Helper
function Write-Header( [string]$Title )
{
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Get-FolderSizeMB( [string]$Path )
{
    if ( -not (Test-Path $Path) ) { return 0 }
    $Bytes = (Get-ChildItem -Path $Path -Recurse -File | Measure-Object -Property Length -Sum).Sum
    return [math]::Round( $Bytes / 1MB, 1 )
}
#endregion

Write-Header "AI Memory Vault v3 — PyInstaller 打包"

# ── Step 1：確認 .venv ──────────────────────────────────────
if ( -not (Test-Path $VenvPython) )
{
    Write-Host "[錯誤] 找不到 .venv，請先執行：" -ForegroundColor Red
    Write-Host "  python -m venv .venv"
    Write-Host "  .venv\Scripts\pip install -r requirements.txt"
    exit 1
}
Write-Host "[OK] .venv 已找到" -ForegroundColor Green

# ── Step 2：確認 PyInstaller ────────────────────────────────
$PyiVersion = & $VenvPython -c "import PyInstaller; print(PyInstaller.__version__)" 2>$null
if ( $LASTEXITCODE -ne 0 -or -not $PyiVersion )
{
    Write-Host "[安裝] PyInstaller 未找到，正在安裝..." -ForegroundColor Yellow
    & $VenvPip install "pyinstaller>=6.0" --quiet
    if ( $LASTEXITCODE -ne 0 ) { Write-Host "[錯誤] PyInstaller 安裝失敗" -ForegroundColor Red; exit 1 }
}
Write-Host "[OK] PyInstaller $PyiVersion" -ForegroundColor Green

# ── Step 3：清除舊建置（選用）─────────────────────────────
if ( $Clean )
{
    Write-Host "[清除] 刪除 build/ 和 dist/ ..." -ForegroundColor Yellow
    @( "build", "dist" ) | ForEach-Object {
        $Dir = Join-Path $ScriptDir "..\$_"
        if ( Test-Path $Dir ) { Remove-Item -Recurse -Force $Dir }
    }
    Write-Host "[OK] 清除完成" -ForegroundColor Green
}

# ── Step 4：執行 PyInstaller ────────────────────────────────
Write-Host ""
Write-Host "[建置] 開始打包（需 10~30 分鐘，視 ML 套件大小而定）..." -ForegroundColor Yellow
Write-Host "       請耐心等候，或觀察 PyInstaller 進度輸出。"
Write-Host ""

$StartTime = Get-Date
$BuildDir = Join-Path $ScriptDir "..\build"
$DistOut  = Join-Path $ScriptDir "..\dist"
& $VenvPython -m PyInstaller $SpecFile --workpath $BuildDir --distpath $DistOut --noconfirm
$Duration  = (Get-Date) - $StartTime

if ( $LASTEXITCODE -ne 0 )
{
    Write-Host ""
    Write-Host "[錯誤] PyInstaller 建置失敗（exit code $LASTEXITCODE）" -ForegroundColor Red
    Write-Host "       請查看上方錯誤訊息，或加 --log-level DEBUG 重試。"
    exit 1
}

# ── Step 5：顯示結果 ────────────────────────────────────────
Write-Header "建置完成！"

$SizeMB = Get-FolderSizeMB $DistDir
Write-Host ""
Write-Host "  輸出目錄  ：$DistDir"
Write-Host "  目錄大小  ：$SizeMB MB"
Write-Host "  建置耗時  ：$([math]::Round($Duration.TotalSeconds))s"
Write-Host ""
Write-Host "  包含執行檔：" -ForegroundColor White
Write-Host "    vault-cli.exe       → 互動式 CLI（雙擊啟動）"
Write-Host "    vault-mcp.exe       → MCP Server"
Write-Host "    vault-scheduler.exe → 排程守護"
Write-Host ""

# ── Step 6：後續設定提示 ────────────────────────────────────
Write-Host "══════════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host "  後續設定（首次使用）" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "  1. 初始化 Vault（首次執行）："
Write-Host "     $DistDir\vault-cli.exe --setup"
Write-Host ""
Write-Host "  2. VS Code / Claude Desktop MCP 設定（更新 mcp.json）："
Write-Host "     {" -ForegroundColor DarkGray
Write-Host '       "servers": {' -ForegroundColor DarkGray
Write-Host '         "ai-memory-vault": {' -ForegroundColor DarkGray
Write-Host "           `"command`": `"$DistDir\vault-mcp.exe`"," -ForegroundColor Yellow
Write-Host '           "args": [],' -ForegroundColor DarkGray
Write-Host "           `"cwd`": `"$DistDir`"" -ForegroundColor DarkGray
Write-Host '         }' -ForegroundColor DarkGray
Write-Host '       }' -ForegroundColor DarkGray
Write-Host '     }' -ForegroundColor DarkGray
Write-Host ""
Write-Host "  3. 排程守護（Ctrl+C 停止）："
Write-Host "     $DistDir\vault-scheduler.exe"
Write-Host ""
Write-Host "[完成]" -ForegroundColor Green
