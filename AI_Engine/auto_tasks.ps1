<#
.SYNOPSIS
    AI Memory Vault v3 — 可設定排程管理器
.DESCRIPTION
    排程由 tasks.json 控制。支援新增/移除排程，並同步至 Windows 工作排程器。

.EXAMPLE
    .\auto_tasks.ps1 -List
    .\auto_tasks.ps1 -Add -Name vault-sync -Type sync -Schedule daily -Time "20:00"
    .\auto_tasks.ps1 -Add -Name daily-lod -Type daily-review -Schedule daily -Time "18:00" -Workspace lifeofdevelopment
    .\auto_tasks.ps1 -Add -Name weekly-lod -Type weekly-review -Schedule weekly -Time "19:00" -Day Sunday -Workspace lifeofdevelopment
    .\auto_tasks.ps1 -Add -Name monthly-lod -Type monthly-review -Schedule monthly -Time "10:00" -Day 1 -Workspace lifeofdevelopment
    .\auto_tasks.ps1 -Remove -Name vault-sync
    .\auto_tasks.ps1 -Apply
    .\auto_tasks.ps1 -Task vault-sync

@author gabrielchen
@version 3.1
@since AI-Memory-Vault 3.0
@date 2026.04.02
#>

param(
    ## <summary>顯示所有已設定的排程及 Windows 工作排程器狀態</summary>
    [switch]$List,

    ## <summary>新增一筆排程並立即註冊到 Windows 工作排程器</summary>
    [switch]$Add,

    ## <summary>從 tasks.json 移除排程，並從 Windows 工作排程器刪除</summary>
    [switch]$Remove,

    ## <summary>將 tasks.json 全部重新套用至 Windows 工作排程器（修改 tasks.json 後使用）</summary>
    [switch]$Apply,

    ## <summary>手動立即執行指定名稱的排程</summary>
    [string]$Task = "",

    # -Add 參數
    ## <summary>排程的唯一識別名稱</summary>
    [string]$Name = "",

    ## <summary>任務類型</summary>
    [string]$Type = "",        # sync | daily-review | weekly-review | monthly-review | ai-analysis

    ## <summary>排程頻率</summary>
    [string]$Schedule = "",    # daily | weekly | monthly

    ## <summary>執行時間（24 小時制，格式 HH:MM）</summary>
    [string]$Time = "",

    ## <summary>週排程：星期幾（Sunday-Saturday）；月排程：第幾日（1-28）</summary>
    [string]$Day = "",

    ## <summary>工作空間名稱（review 類任務必填）</summary>
    [string]$Workspace = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

#region 常數定義
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$EngineDir  = $ScriptDir
$VenvPython = Join-Path $EngineDir ".venv\Scripts\python.exe"
$LogFile    = Join-Path $EngineDir "scheduler.log"
$TasksJson  = Join-Path $EngineDir "tasks.json"
$TaskPrefix = "AI-MemoryVault-V3"

$ValidTypes     = @( "sync", "daily-review", "weekly-review", "monthly-review", "ai-analysis" )
$ValidSchedules = @( "daily", "weekly", "monthly" )
$ValidDaysOfWeek = @( "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" )
#endregion

#region Helper Functions

## <summary>寫入排程 Log 並輸出至 Console。</summary>
function Write-Log( [string]$iLevel, [string]$iMessage )
{
    $Ts    = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Entry = "[$Ts] [$iLevel] $iMessage"
    Add-Content -Path $LogFile -Value $Entry
    if( $iLevel -eq "ERROR" )    { Write-Host $Entry -ForegroundColor Red }
    elseif( $iLevel -eq "WARN" ) { Write-Host $Entry -ForegroundColor Yellow }
    else                         { Write-Host $Entry }
}

## <summary>讀取 tasks.json，回傳排程物件陣列。</summary>
function Get-Tasks
{
    if( -not (Test-Path $TasksJson) )
    {
        return @()
    }
    $Json = Get-Content $TasksJson -Raw | ConvertFrom-Json
    if( $null -eq $Json.tasks ) { return @() }
    return @( $Json.tasks )
}

## <summary>將排程陣列寫回 tasks.json。</summary>
function Save-Tasks( [array]$iTasks )
{
    $Obj = [PSCustomObject]@{ tasks = $iTasks }
    $Obj | ConvertTo-Json -Depth 5 | Set-Content $TasksJson -Encoding UTF8
}

## <summary>組合 Windows 工作排程器任務名稱。</summary>
function Get-WinTaskName( [string]$iName )
{
    return "$TaskPrefix-$iName"
}

## <summary>依 schedule / day / time 建立 ScheduledTaskTrigger。</summary>
function New-VaultTaskTrigger( [object]$iTask )
{
    switch( $iTask.schedule )
    {
        "daily"
        {
            return New-ScheduledTaskTrigger -Daily -At $iTask.time
        }
        "weekly"
        {
            if( $ValidDaysOfWeek -notcontains $iTask.day )
            {
                throw "weekly 排程的 Day 必須是 Sunday-Saturday，目前值：'$($iTask.day)'"
            }
            return New-ScheduledTaskTrigger -Weekly -DaysOfWeek $iTask.day -At $iTask.time
        }
        "monthly"
        {
            $DayNum = [int]$iTask.day
            if( $DayNum -lt 1 -or $DayNum -gt 28 )
            {
                throw "monthly 排程的 Day 必須是 1-28，目前值：'$($iTask.day)'"
            }
            return New-ScheduledTaskTrigger -Monthly -DaysOfMonth $DayNum -At $iTask.time
        }
        default { throw "不支援的排程頻率：'$($iTask.schedule)'" }
    }
}

## <summary>將單筆排程定義註冊至 Windows 工作排程器。</summary>
function Register-VaultTask( [object]$iTask )
{
    $_Action   = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`" -Task `"$($iTask.name)`""
    $_Trigger  = New-VaultTaskTrigger $iTask
    $_Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

    Register-ScheduledTask `
        -TaskName (Get-WinTaskName $iTask.name) `
        -Action $_Action `
        -Trigger $_Trigger `
        -Settings $_Settings `
        -RunLevel Highest `
        -Force | Out-Null
}

## <summary>呼叫新 venv 的 Python 執行一段程式碼，失敗時寫 Log 並結束。</summary>
function Invoke-Python( [string]$iCode )
{
    $Output   = & $VenvPython -c $iCode 2>&1
    $ExitCode = $LASTEXITCODE
    if( $ExitCode -ne 0 )
    {
        Write-Log "ERROR" "Python 執行失敗：$( $Output -join ' | ' )"
        exit 1
    }
    return $Output
}

#endregion

#region Bootstrap Code（所有 Task 共用）
$BootstrapCode = @"
import sys, os
sys.path.insert(0, r'$EngineDir')
os.chdir(r'$EngineDir')
from config import ConfigManager
from core import embeddings as emb, vectorstore as vs
from services.vault import VaultService
config = ConfigManager.load()
emb.initialize(config.embedding.model)
vs.initialize(
    iChromaDir=config.database.get_chroma_path(),
    iRecordDbUrl=config.database.get_record_db_url(),
    iCollectionName=config.database.collection_name,
)
VaultService.initialize(config)
"@
#endregion

#region Commands

# ── -List ──────────────────────────────────────────────────
if( $List )
{
    $_Tasks = @( Get-Tasks )
    if( $_Tasks.Count -eq 0 )
    {
        Write-Host "`n（tasks.json 為空。使用 -Add 新增排程）`n" -ForegroundColor Yellow
        exit 0
    }

    Write-Host "`n排程清單（共 $($_Tasks.Count) 筆）：" -ForegroundColor Cyan
    Write-Host ( "{0,-28} {1,-18} {2,-10} {3,-10} {4,-7} {5}" -f `
        "Name", "Type", "Schedule", "Day", "Time", "Workspace" )
    Write-Host ( "-" * 95 )

    foreach( $_T in $_Tasks )
    {
        $WsDisplay  = if( $_T.workspace ) { $_T.workspace } else { "-" }
        $DayDisplay = if( $_T.day )       { $_T.day }       else { "-" }
        Write-Host ( "{0,-28} {1,-18} {2,-10} {3,-10} {4,-7} {5}" -f `
            $_T.name, $_T.type, $_T.schedule, $DayDisplay, $_T.time, $WsDisplay )
    }

    Write-Host "`nWindows 工作排程器狀態：" -ForegroundColor Cyan
    foreach( $_T in $_Tasks )
    {
        $WinTask = Get-ScheduledTask -TaskName (Get-WinTaskName $_T.name) -ErrorAction SilentlyContinue
        $Status  = if( $WinTask ) { "✅ 已註冊  State=$($WinTask.State)" } else { "❌ 未註冊（請執行 -Apply）" }
        Write-Host "  $(Get-WinTaskName $_T.name) → $Status"
    }
    Write-Host ""
    exit 0
}

# ── -Add ───────────────────────────────────────────────────
if( $Add )
{
    # 必填驗證
    if( -not $Name )
    {
        Write-Host "❌ 必填：-Name <排程名稱>" -ForegroundColor Red; exit 1
    }
    if( $ValidTypes -notcontains $Type )
    {
        Write-Host "❌ 必填：-Type ($( $ValidTypes -join ' | ' ))" -ForegroundColor Red; exit 1
    }
    if( $ValidSchedules -notcontains $Schedule )
    {
        Write-Host "❌ 必填：-Schedule ($( $ValidSchedules -join ' | ' ))" -ForegroundColor Red; exit 1
    }
    if( -not $Time )
    {
        Write-Host "❌ 必填：-Time HH:MM（24 小時制）" -ForegroundColor Red; exit 1
    }
    if( $Schedule -eq "weekly" -and -not $Day )
    {
        Write-Host "❌ weekly 排程需填 -Day（Sunday / Monday / ... / Saturday）" -ForegroundColor Red; exit 1
    }
    if( $Schedule -eq "monthly" -and -not $Day )
    {
        Write-Host "❌ monthly 排程需填 -Day（1-28，每月第幾日）" -ForegroundColor Red; exit 1
    }
    if( @( "daily-review", "weekly-review", "monthly-review" ) -contains $Type -and -not $Workspace )
    {
        Write-Host "❌ $Type 需填 -Workspace <工作空間名稱>" -ForegroundColor Red; exit 1
    }

    # 名稱重複檢查
    $_Tasks = @( Get-Tasks )
    if( $_Tasks | Where-Object { $_.name -eq $Name } )
    {
        Write-Host "❌ 名稱 '$Name' 已存在，請用不同名稱。" -ForegroundColor Red; exit 1
    }

    # 新增至 tasks.json
    $NewTask = [PSCustomObject]@{
        name      = $Name
        type      = $Type
        workspace = $Workspace
        schedule  = $Schedule
        time      = $Time
        day       = $Day
    }
    $_Tasks = @( @( $_Tasks ) + $NewTask )
    Save-Tasks $_Tasks

    # 立即註冊至 Windows 工作排程器
    Register-VaultTask $NewTask

    $WsInfo   = if( $Workspace ) { " | Workspace: $Workspace" } else { "" }
    $_DayInfo = if( $Day ) { " $Day" } else { "" }
    Write-Host "✅ 已新增排程：$(Get-WinTaskName $Name)" -ForegroundColor Green
    Write-Host "   $Type | $Schedule$_DayInfo $Time$WsInfo" -ForegroundColor Green
    exit 0
}

# ── -Remove ────────────────────────────────────────────────
if( $Remove )
{
    if( -not $Name ) { Write-Host "❌ 必填：-Name <排程名稱>" -ForegroundColor Red; exit 1 }

    $_Tasks = @( Get-Tasks )
    $_Target = $_Tasks | Where-Object { $_.name -eq $Name }
    if( -not $_Target )
    {
        Write-Host "❌ 找不到排程：'$Name'（執行 -List 查看目前清單）" -ForegroundColor Red; exit 1
    }

    # 從 Windows 工作排程器移除
    $WinTaskName = Get-WinTaskName $Name
    if( Get-ScheduledTask -TaskName $WinTaskName -ErrorAction SilentlyContinue )
    {
        Unregister-ScheduledTask -TaskName $WinTaskName -Confirm:$false
        Write-Host "  [Removed] Windows 工作排程器：$WinTaskName" -ForegroundColor Yellow
    }

    # 從 tasks.json 移除
    $_FilteredRaw = $_Tasks | Where-Object { $_.name -ne $Name }
    $_Tasks = if( $_FilteredRaw ) { @( $_FilteredRaw ) } else { @() }
    Save-Tasks $_Tasks

    Write-Host "✅ 已移除排程：$Name" -ForegroundColor Green
    exit 0
}

# ── -Apply ─────────────────────────────────────────────────
if( $Apply )
{
    $_Tasks = @( Get-Tasks )
    if( $_Tasks.Count -eq 0 )
    {
        Write-Host "（tasks.json 為空，無排程需套用）" -ForegroundColor Yellow; exit 0
    }

    Write-Host "[Apply] 將 tasks.json 同步至 Windows 工作排程器..." -ForegroundColor Cyan

    # 先移除全部 V3 任務再重建（確保 trigger 定義同步）
    Get-ScheduledTask -TaskName "$TaskPrefix*" -ErrorAction SilentlyContinue |
        ForEach-Object { Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false }

    foreach( $_T in $_Tasks )
    {
        Register-VaultTask $_T
        $_DayInfo = if( $_T.day ) { " $($_T.day)" } else { "" }
        Write-Host "  [OK] $(Get-WinTaskName $_T.name): $($_T.schedule)$_DayInfo $($_T.time)" -ForegroundColor Green
    }

    Write-Host "[Done] 已套用 $($_Tasks.Count) 個排程。" -ForegroundColor Green
    exit 0
}

# ── -Task（手動執行）──────────────────────────────────────
if( $Task )
{
    $_Tasks   = @( Get-Tasks )
    $TaskDef  = $_Tasks | Where-Object { $_.name -eq $Task }
    if( -not $TaskDef )
    {
        Write-Log "ERROR" "找不到排程：'$Task'（先用 -Add 新增）"
        exit 1
    }

    Write-Log "INFO" "手動執行：$Task (type=$($TaskDef.type))"

    switch( $TaskDef.type )
    {
        "sync"
        {
            $Result  = Invoke-Python ( $BootstrapCode + @"

stats = VaultService.sync()
s = stats['index_stats']
print(f"added={s['num_added']} updated={s['num_updated']} deleted={s['num_deleted']} total={stats['total_chunks']}")
"@ )
            Write-Log "INFO" "Sync complete: $( ($Result | Select-String 'added=' | Select-Object -Last 1).ToString() )"
        }

        "daily-review"
        {
            $Result = Invoke-Python ( $BootstrapCode + @"

from services.scheduler import SchedulerService
sched = SchedulerService(config)
path = sched.generate_daily_summary()
print(f"Generated: {path}")
"@ )
            Write-Log "INFO" ($Result -join " ")
        }

        "weekly-review"
        {
            $Result = Invoke-Python ( $BootstrapCode + @"

from services.scheduler import SchedulerService
sched = SchedulerService(config)
path = sched.generate_weekly_summary()
print(f"Generated: {path}")
"@ )
            Write-Log "INFO" ($Result -join " ")
        }

        "monthly-review"
        {
            $Result = Invoke-Python ( $BootstrapCode + @"

from services.scheduler import SchedulerService
sched = SchedulerService(config)
path = sched.generate_monthly_summary()
print(f"Generated: {path}")
"@ )
            Write-Log "INFO" ($Result -join " ")
        }

        "ai-analysis"
        {
            $Result = Invoke-Python ( $BootstrapCode + @"

from services.scheduler import SchedulerService
sched = SchedulerService(config)
path = sched.generate_ai_monthly_analysis()
print(f"Generated: {path}")
"@ )
            Write-Log "INFO" ($Result -join " ")
        }

        default
        {
            Write-Log "ERROR" "不支援的任務類型：$($TaskDef.type)"
            exit 1
        }
    }
    exit 0
}

#endregion

# ── 無指令時顯示說明 ───────────────────────────────────────
Write-Host @"

AI Memory Vault v3 — 排程管理器

用法：
  -List                           列出所有排程及 Windows 工作排程器狀態
  -Add  -Name    <名稱>           新增排程並立即註冊（名稱不可重複）
        -Type    <類型>           sync | daily-review | weekly-review | monthly-review | ai-analysis
        -Schedule <頻率>          daily | weekly | monthly
        -Time    <時間>           HH:MM（24 小時制，例如 "20:00"）
        [-Day    <日>]            weekly → 星期幾 (Sunday-Saturday)
                                  monthly → 第幾日 (1-28)
        [-Workspace <工作空間>]   review 類任務必填
  -Remove -Name <名稱>            移除排程（tasks.json + Windows 工作排程器）
  -Apply                          將 tasks.json 全部重新套用至 Windows 工作排程器
  -Task   <名稱>                  手動立即執行某個排程

範例：
  .\auto_tasks.ps1 -List
  .\auto_tasks.ps1 -Add -Name vault-sync -Type sync -Schedule daily -Time "20:00"
  .\auto_tasks.ps1 -Add -Name daily-lod  -Type daily-review   -Schedule daily   -Time "18:00" -Workspace lifeofdevelopment
  .\auto_tasks.ps1 -Add -Name weekly-lod -Type weekly-review  -Schedule weekly  -Time "19:00" -Day Sunday -Workspace lifeofdevelopment
  .\auto_tasks.ps1 -Add -Name monthly-lod -Type monthly-review -Schedule monthly -Time "10:00" -Day 1 -Workspace lifeofdevelopment
  .\auto_tasks.ps1 -Remove  -Name vault-sync
  .\auto_tasks.ps1 -Apply
  .\auto_tasks.ps1 -Task    vault-sync

"@ -ForegroundColor Cyan
