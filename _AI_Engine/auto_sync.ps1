# auto_sync.ps1 - AI Memory Vault auto-sync script
# Called by Windows Task Scheduler to keep ChromaDB index up to date.
#
# Usage:
#   Manual run:   powershell -ExecutionPolicy Bypass -File "D:\AI-Memory-Vault\_AI_Engine\auto_sync.ps1"
#   Install task: Run with -RegisterSchedule flag (requires Admin)
#
# @author gabrielchen
# @version 1.1
# @since AI-Memory-Vault 2.0
# @date 2026.03.28

param(
    [switch]$RegisterSchedule,    # Install Windows Task Scheduler job
    [switch]$UnregisterSchedule   # Remove Windows Task Scheduler job
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$VaultRoot   = Split-Path -Parent $ScriptDir
$VenvPython  = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$LogFile     = Join-Path $ScriptDir "auto_sync.log"
$TaskName    = "AI-MemoryVault-AutoSync"

# ── Register task ────────────────────────────────────────
if( $RegisterSchedule )
{
    Write-Host "[Schedule] Registering task: $TaskName"

    $Action  = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`""

    # Daily at 20:00; StartWhenAvailable catches missed runs after shutdown
    $Trigger = New-ScheduledTaskTrigger -Daily -At "20:00"

    $Settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -RunLevel Highest `
        -Force | Out-Null

    Write-Host "[Done] Task registered: daily at 20:00" -ForegroundColor Green
    Write-Host "       Task name : $TaskName"
    Write-Host "       Verify    : Get-ScheduledTask -TaskName '$TaskName'"
    exit
}

# ── Unregister task ──────────────────────────────────────
if( $UnregisterSchedule )
{
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[Done] Task removed: $TaskName" -ForegroundColor Yellow
    exit
}

# ── Main sync logic (called by the scheduled task) ──────
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$LogEntry  = "[$Timestamp]"

try
{
    if( -not (Test-Path $VenvPython) )
    {
        throw "Python venv not found: $VenvPython"
    }

    # Run VaultIndexer().sync() via subprocess
    $SyncScript = @"
import sys, os
sys.path.insert(0, r'$ScriptDir')
os.chdir(r'$ScriptDir')
from core.indexer import VaultIndexer
result = VaultIndexer().sync()
stats = result['index_stats']
print(f"added={stats['num_added']} updated={stats['num_updated']} deleted={stats['num_deleted']} total={result['total_chunks']}")
"@

    $Output = & $VenvPython -c $SyncScript 2>&1
    $ExitCode = $LASTEXITCODE

    if( $ExitCode -eq 0 )
    {
        $Summary = $Output | Select-String "added=" | Select-Object -Last 1
        Add-Content -Path $LogFile -Value "$LogEntry SUCCESS $Summary"
        Write-Host "$LogEntry [OK] $Summary"
    }
    else
    {
        $ErrorMsg = $Output -join " | "
        Add-Content -Path $LogFile -Value "$LogEntry ERROR $ErrorMsg"
        Write-Host "$LogEntry [FAIL] $ErrorMsg" -ForegroundColor Red
        exit 1
    }
}
catch
{
    $ErrorMsg = $_.Exception.Message
    Add-Content -Path $LogFile -Value "$LogEntry EXCEPTION $ErrorMsg"
    Write-Host "$LogEntry [EXCEPTION] $ErrorMsg" -ForegroundColor Red
    exit 1
}
