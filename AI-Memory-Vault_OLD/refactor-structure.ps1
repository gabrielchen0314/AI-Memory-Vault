<#
.SYNOPSIS
    AI Memory Vault 架構剝離腳本
.DESCRIPTION
    將現有的 _AI_Engine + 根目錄內容 重構為 AI_Engine/ + Vault/ 結構。
.NOTES
    @author gabrielchen
    @version 1.0
    @date 2026.04.01
#>

param(
    [switch]$DryRun = $false,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot | Split-Path -Parent

Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   AI Memory Vault — 架構剝離腳本                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if( $DryRun )
{
    Write-Host "[DRY RUN] 僅預覽變更，不會實際執行" -ForegroundColor Yellow
}

# ── Step 1: 確認目前結構 ────────────────────────────────────
Write-Host "`n[1/5] 確認目前結構..." -ForegroundColor Green

$_RequiredPaths = @(
    "_AI_Engine",
    "_system",
    "work",
    "life",
    "knowledge",
    "templates"
)

$_MissingPaths = @()
foreach( $_Path in $_RequiredPaths )
{
    $_FullPath = Join-Path $ROOT $_Path
    if( -not ( Test-Path $_FullPath ) )
    {
        $_MissingPaths += $_Path
    }
}

if( $_MissingPaths.Count -gt 0 )
{
    Write-Host "  [ERROR] 缺少必要目錄: $( $_MissingPaths -join ', ' )" -ForegroundColor Red
    exit 1
}

Write-Host "  [OK] 目前結構確認完成" -ForegroundColor Green

# ── Step 2: 建立新目錄結構 ──────────────────────────────────
Write-Host "`n[2/5] 建立新目錄結構..." -ForegroundColor Green

$_NewDirs = @(
    "AI_Engine",
    "Vault"
)

foreach( $_Dir in $_NewDirs )
{
    $_FullPath = Join-Path $ROOT $_Dir
    if( Test-Path $_FullPath )
    {
        if( $Force )
        {
            Write-Host "  [WARN] 目錄已存在，將覆蓋: $_Dir" -ForegroundColor Yellow
        }
        else
        {
            Write-Host "  [ERROR] 目錄已存在: $_Dir (使用 -Force 覆蓋)" -ForegroundColor Red
            exit 1
        }
    }
    
    if( -not $DryRun )
    {
        New-Item -ItemType Directory -Path $_FullPath -Force | Out-Null
    }
    Write-Host "  [+] 建立: $_Dir" -ForegroundColor Gray
}

# ── Step 3: 移動 AI_Engine ──────────────────────────────────
Write-Host "`n[3/5] 移動 AI_Engine（程式碼）..." -ForegroundColor Green

$_AIEngineSource = Join-Path $ROOT "_AI_Engine"
$_AIEngineDest = Join-Path $ROOT "AI_Engine"

$_AIEngineItems = Get-ChildItem -Path $_AIEngineSource -Force

foreach( $_Item in $_AIEngineItems )
{
    $_DestPath = Join-Path $_AIEngineDest $_Item.Name
    Write-Host "  [MOVE] $( $_Item.Name )" -ForegroundColor Gray
    
    if( -not $DryRun )
    {
        if( $_Item.PSIsContainer )
        {
            Copy-Item -Path $_Item.FullName -Destination $_DestPath -Recurse -Force
        }
        else
        {
            Copy-Item -Path $_Item.FullName -Destination $_DestPath -Force
        }
    }
}

# ── Step 4: 移動 Vault 內容 ─────────────────────────────────
Write-Host "`n[4/5] 移動 Vault 內容..." -ForegroundColor Green

$_VaultSource = @(
    "_system",
    "work",
    "life",
    "knowledge",
    "templates",
    "attachments"
)

$_VaultDest = Join-Path $ROOT "Vault"

foreach( $_Dir in $_VaultSource )
{
    $_SourcePath = Join-Path $ROOT $_Dir
    $_DestPath = Join-Path $_VaultDest $_Dir.TrimStart( "_" )  # _system → system（可選）
    
    # 保持原名（不去底線）
    $_DestPath = Join-Path $_VaultDest $_Dir
    
    if( Test-Path $_SourcePath )
    {
        Write-Host "  [MOVE] $_Dir → Vault/$_Dir" -ForegroundColor Gray
        
        if( -not $DryRun )
        {
            Copy-Item -Path $_SourcePath -Destination $_DestPath -Recurse -Force
        }
    }
    else
    {
        Write-Host "  [SKIP] $_Dir（不存在）" -ForegroundColor DarkGray
    }
}

# ── Step 5: 更新設定檔 ──────────────────────────────────────
Write-Host "`n[5/5] 更新設定檔..." -ForegroundColor Green

# 更新 config.py
$_ConfigPath = Join-Path $ROOT "AI_Engine\config.py"
if( ( Test-Path $_ConfigPath ) -and -not $DryRun )
{
    $_Content = Get-Content $_ConfigPath -Raw
    
    # 修改 VAULT_ROOT
    $_OldPattern = 'VAULT_ROOT\s*=\s*Path\(\s*__file__\s*\)\.resolve\(\)\.parent\.parent'
    $_NewValue = 'VAULT_ROOT = Path( __file__ ).resolve().parent.parent / "Vault"'
    
    if( $_Content -match $_OldPattern )
    {
        $_Content = $_Content -replace $_OldPattern, $_NewValue
        Set-Content -Path $_ConfigPath -Value $_Content -Encoding UTF8
        Write-Host "  [UPDATE] config.py: VAULT_ROOT → ../Vault" -ForegroundColor Gray
    }
}

Write-Host "`n════════════════════════════════════════════════════" -ForegroundColor Cyan

if( $DryRun )
{
    Write-Host "[DRY RUN 完成] 預覽結束，未執行任何變更" -ForegroundColor Yellow
    Write-Host "執行 .\refactor-structure.ps1 以實際執行" -ForegroundColor Yellow
}
else
{
    Write-Host "[完成] 架構剝離成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "後續步驟:" -ForegroundColor Cyan
    Write-Host "  1. 確認 AI_Engine/ 和 Vault/ 結構正確"
    Write-Host "  2. 刪除舊目錄: _AI_Engine, _system, work, life, knowledge, templates, attachments"
    Write-Host "  3. 更新 .vscode/mcp.json 中的 cwd"
    Write-Host "  4. 測試 MCP Server: cd AI_Engine && python main.py --mode mcp"
}
