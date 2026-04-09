#Requires -Version 5.1
<#
.SYNOPSIS
    AI Memory Vault v3 — 排程管理互動選單

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.0
@date 2026.04.02
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

#region 常數定義
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$AutoTasks  = Join-Path $ScriptDir "auto_tasks.ps1"

$TypeMenu = @{
    "1" = "sync"
    "2" = "daily-review"
    "3" = "weekly-review"
    "4" = "monthly-review"
    "5" = "ai-analysis"
}

$DayMenu = @{
    "0" = "Sunday"
    "1" = "Monday"
    "2" = "Tuesday"
    "3" = "Wednesday"
    "4" = "Thursday"
    "5" = "Friday"
    "6" = "Saturday"
}
#endregion

#region Helper Functions

## <summary>清除畫面並顯示標題列。</summary>
function Show-Header
{
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   AI Memory Vault v3 — 排程管理工具   " -ForegroundColor Cyan
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

## <summary>呼叫 auto_tasks.ps1 並傳入參數，同時捕捉輸出。</summary>
function Invoke-AutoTasks( [string[]]$iArgs )
{
    & powershell -ExecutionPolicy Bypass -File $AutoTasks @iArgs
}

## <summary>互動式詢問並回傳任務名稱，確保不為空。</summary>
function Read-TaskName
{
    while( $true )
    {
        $_Name = ( Read-Host "  排程名稱（英文/數字，不可重複）" ).Trim()
        if( $_Name ) { return $_Name }
        Write-Host "  ❌ 名稱不可為空。" -ForegroundColor Red
    }
}

## <summary>互動式選擇任務類型，回傳類型字串。</summary>
function Read-TaskType
{
    Write-Host "  任務類型："
    Write-Host "    1) sync           — 同步 Vault 檔案至向量資料庫"
    Write-Host "    2) daily-review   — 每日工作回顧"
    Write-Host "    3) weekly-review  — 每週工作回顧"
    Write-Host "    4) monthly-review — 每月工作回顧"
    Write-Host "    5) ai-analysis    — AI 每月分析報告"
    while( $true )
    {
        $_Key = ( Read-Host "  請選擇 (1-5)" ).Trim()
        if( $TypeMenu.ContainsKey($_Key) ) { return $TypeMenu[$_Key] }
        Write-Host "  ❌ 請輸入 1-5。" -ForegroundColor Red
    }
}

## <summary>互動式選擇排程頻率，回傳 daily/weekly/monthly。</summary>
function Read-Schedule
{
    Write-Host "  排程頻率："
    Write-Host "    1) daily   — 每天"
    Write-Host "    2) weekly  — 每週"
    Write-Host "    3) monthly — 每月"
    while( $true )
    {
        $_Key = ( Read-Host "  請選擇 (1-3)" ).Trim()
        switch( $_Key )
        {
            "1" { return "daily"   }
            "2" { return "weekly"  }
            "3" { return "monthly" }
        }
        Write-Host "  ❌ 請輸入 1-3。" -ForegroundColor Red
    }
}

## <summary>互動式輸入時間，格式 HH:MM，回傳字串。</summary>
function Read-Time
{
    while( $true )
    {
        $_T = ( Read-Host "  執行時間（例如 20:00，24 小時制）" ).Trim()
        if( $_T -match '^\d{1,2}:\d{2}$' ) { return $_T }
        Write-Host "  ❌ 格式錯誤，請輸入如 20:00。" -ForegroundColor Red
    }
}

## <summary>回傳 weekly 排程的星期幾字串。</summary>
function Read-DayOfWeek
{
    Write-Host "  每週幾執行："
    Write-Host "    0) 週日  1) 週一  2) 週二  3) 週三  4) 週四  5) 週五  6) 週六"
    while( $true )
    {
        $_Key = ( Read-Host "  請選擇 (0-6)" ).Trim()
        if( $DayMenu.ContainsKey($_Key) ) { return $DayMenu[$_Key] }
        Write-Host "  ❌ 請輸入 0-6。" -ForegroundColor Red
    }
}

## <summary>回傳 monthly 排程的日期數字字串（1-28）。</summary>
function Read-DayOfMonth
{
    while( $true )
    {
        $_D = ( Read-Host "  每月第幾日執行（1-28）" ).Trim()
        $_Num = 0
        if( [int]::TryParse($_D, [ref]$_Num) -and $_Num -ge 1 -and $_Num -le 28 )
        {
            return $_D
        }
        Write-Host "  ❌ 請輸入 1-28 之間的數字。" -ForegroundColor Red
    }
}

## <summary>回傳工作空間名稱，review 類任務必填。</summary>
function Read-Workspace( [string]$iType )
{
    if( @( "daily-review", "weekly-review", "monthly-review" ) -contains $iType )
    {
        while( $true )
        {
            $_Ws = ( Read-Host "  工作空間名稱（必填，例如 lifeofdevelopment）" ).Trim()
            if( $_Ws ) { return $_Ws }
            Write-Host "  ❌ $iType 必須填寫工作空間名稱。" -ForegroundColor Red
        }
    }
    return ""
}

#endregion

#region 選單動作

## <summary>顯示排程清單。</summary>
function Action-List
{
    Show-Header
    Write-Host "[ 排程清單 ]" -ForegroundColor Yellow
    Write-Host ""
    Invoke-AutoTasks @( "-List" )
    Pause-Menu
}

## <summary>引導新增排程的互動流程。</summary>
function Action-Add
{
    Show-Header
    Write-Host "[ 新增排程 ]" -ForegroundColor Yellow
    Write-Host ""

    $_Name     = Read-TaskName
    Write-Host ""
    $_Type     = Read-TaskType
    Write-Host ""
    $_Schedule = Read-Schedule
    Write-Host ""
    $_Time     = Read-Time
    $_Day      = ""
    $_Workspace = Read-Workspace $_Type

    if( $_Schedule -eq "weekly" )
    {
        Write-Host ""
        $_Day = Read-DayOfWeek
    }
    elseif( $_Schedule -eq "monthly" )
    {
        Write-Host ""
        $_Day = Read-DayOfMonth
    }

    Write-Host ""
    Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "  名稱      : $_Name"
    Write-Host "  類型      : $_Type"
    Write-Host "  頻率      : $_Schedule"
    if( $_Day )       { Write-Host "  日期      : $_Day" }
    Write-Host "  時間      : $_Time"
    if( $_Workspace ) { Write-Host "  工作空間  : $_Workspace" }
    Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""

    $_Confirm = ( Read-Host "  確認新增？(y/Enter = 確認，n = 取消)" ).Trim().ToLower()
    if( $_Confirm -eq "n" )
    {
        Write-Host "  已取消。" -ForegroundColor Yellow
        Pause-Menu
        return
    }

    Write-Host ""
    $ArgList = [System.Collections.Generic.List[string]]@(
        "-Add", "-Name", $_Name, "-Type", $_Type,
        "-Schedule", $_Schedule, "-Time", $_Time
    )
    if( $_Day )        { $ArgList.Add("-Day");       $ArgList.Add($_Day) }
    if( $_Workspace )  { $ArgList.Add("-Workspace"); $ArgList.Add($_Workspace) }

    Invoke-AutoTasks $ArgList
    Pause-Menu
}

## <summary>引導刪除排程的互動流程。</summary>
function Action-Remove
{
    Show-Header
    Write-Host "[ 刪除排程 ]" -ForegroundColor Yellow
    Write-Host ""
    Invoke-AutoTasks @( "-List" )
    Write-Host ""

    $_Name = ( Read-Host "  輸入要刪除的排程名稱（輸入 0 取消）" ).Trim()
    if( $_Name -eq "0" -or -not $_Name )
    {
        Write-Host "  已取消。" -ForegroundColor Yellow
        Pause-Menu
        return
    }

    Write-Host ""
    $_Confirm = ( Read-Host "  確認刪除 '$_Name'？(y/Enter = 確認，n = 取消)" ).Trim().ToLower()
    if( $_Confirm -eq "n" )
    {
        Write-Host "  已取消。" -ForegroundColor Yellow
        Pause-Menu
        return
    }

    Write-Host ""
    Invoke-AutoTasks @( "-Remove", "-Name", $_Name )
    Pause-Menu
}

## <summary>引導手動立即執行排程的流程。</summary>
function Action-RunNow
{
    Show-Header
    Write-Host "[ 手動立即執行 ]" -ForegroundColor Yellow
    Write-Host ""
    Invoke-AutoTasks @( "-List" )
    Write-Host ""

    $_Name = ( Read-Host "  輸入要執行的排程名稱（輸入 0 取消）" ).Trim()
    if( $_Name -eq "0" -or -not $_Name )
    {
        Write-Host "  已取消。" -ForegroundColor Yellow
        Pause-Menu
        return
    }

    Write-Host ""
    Invoke-AutoTasks @( "-Task", $_Name )
    Pause-Menu
}

## <summary>將 tasks.json 全部重新套用至 Windows 工作排程器。</summary>
function Action-Apply
{
    Show-Header
    Write-Host "[ 重新套用所有排程至 Windows 工作排程器 ]" -ForegroundColor Yellow
    Write-Host ""
    Invoke-AutoTasks @( "-Apply" )
    Pause-Menu
}

#endregion

#region 主選單迴圈
while( $true )
{
    Show-Header
    Write-Host "  1) 查看排程清單"
    Write-Host "  2) 新增排程"
    Write-Host "  3) 刪除排程"
    Write-Host "  4) 手動立即執行排程"
    Write-Host "  5) 重新套用所有排程（修改 tasks.json 後使用）"
    Write-Host "  0) 離開"
    Write-Host ""

    $_Choice = ( Read-Host "  請選擇 (0-5)" ).Trim()

    switch( $_Choice )
    {
        "1" { Action-List    }
        "2" { Action-Add     }
        "3" { Action-Remove  }
        "4" { Action-RunNow  }
        "5" { Action-Apply   }
        "0" { Write-Host "Bye!"; exit 0 }
        default
        {
            Write-Host "  ❌ 請輸入 0-5。" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
#endregion
