# AI Memory Vault v3 - 主選單
# 以 PowerShell 執行，完整 Unicode 支援，不受 CMD 中文 Byte 解析問題影響

$ErrorActionPreference = "Stop"
trap {
    $LogPath = Join-Path $env:TEMP "ai-memory-vault-error.log"
    $msg = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: $_`r`n$($_.ScriptStackTrace)"
    Add-Content -Path $LogPath -Value $msg
    Write-Host ""
    Write-Host "  [錯誤] $_" -ForegroundColor Red
    Write-Host "  Log 已儲存至：$LogPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "按任意鍵關閉..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = $MyInvocation.MyCommand.Path
$isAdmin    = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Set-Location $ScriptDir

$ConfigPath = Join-Path $env:APPDATA "AI-Memory-Vault\config.json"

# ══════════════════════════════════════════════════════
#  Sub-menu functions
# ══════════════════════════════════════════════════════

function Show-EnvSettingsMenu {
    :envMenu while ($true) {
        Clear-Host
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host "  AI Memory Vault v3 - 環境設定" -ForegroundColor Cyan
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  1. 修改 Vault 路徑"
        Write-Host "  2. 修改使用者資訊"
        Write-Host "  3. 管理組織"
        Write-Host "  4. 修改 LLM 設定"
        Write-Host "  5. 完整重設（依序引導，Enter 保留原值）"
        Write-Host "  6. 返回主選單"
        Write-Host ""
        $sub = Read-Host "請選擇 [1-6]"
        switch ($sub) {
            "1" { Write-Host ""; & "$ScriptDir\vault-cli.exe" --setup-section vault; Write-Host ""; Write-Host "按任意鍵繼續..."; $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
            "2" { Write-Host ""; & "$ScriptDir\vault-cli.exe" --setup-section user;  Write-Host ""; Write-Host "按任意鍵繼續..."; $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
            "3" { Write-Host ""; & "$ScriptDir\vault-cli.exe" --setup-section org;   Write-Host ""; Write-Host "按任意鍵繼續..."; $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
            "4" { Write-Host ""; & "$ScriptDir\vault-cli.exe" --setup-section llm;   Write-Host ""; Write-Host "按任意鍵繼續..."; $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
            "5" { Write-Host ""; & "$ScriptDir\vault-cli.exe" --reconfigure;         Write-Host ""; Write-Host "按任意鍵繼續..."; $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
            "6" { break envMenu }
            default { Write-Host "  [!] 無效選項" -ForegroundColor Red; Start-Sleep -Seconds 1 }
        }
    }
}

function Show-SchedulerMenu {
    :schedMenu while ($true) {
        Clear-Host
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host "  AI Memory Vault v3 - 排程管理" -ForegroundColor Cyan
        if ($isAdmin) {
            Write-Host "  [管理員模式]" -ForegroundColor Green
        } else {
            Write-Host "  [一般使用者 - 新增/刪除需要管理員]" -ForegroundColor Yellow
        }
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  1. 查看排程任務清單"
        if ($isAdmin) {
            Write-Host "  2. 新增排程任務"
            Write-Host "  3. 刪除排程任務"
        } else {
            Write-Host "  2. 新增排程任務  [需要管理員]" -ForegroundColor DarkGray
            Write-Host "  3. 刪除排程任務  [需要管理員]" -ForegroundColor DarkGray
        }
        Write-Host "  4. 立即執行一次"
        Write-Host "  5. 查看 Log"
        Write-Host "  6. 診斷排程問題"
        Write-Host "  7. 返回主選單"
        Write-Host ""
        $sub = Read-Host "請選擇 [1-7]"
        switch ($sub) {
            "1" {
                Write-Host ""
                Write-Host "  ── AI Memory Vault 排程任務清單 ───────────" -ForegroundColor Cyan
                Write-Host ""
                $tasks = Get-ScheduledTask | Where-Object { $_.TaskName -match "AI-MemoryVault" } -ErrorAction SilentlyContinue
                if ($tasks) {
                    $tasks | ForEach-Object {
                        $info = $_ | Get-ScheduledTaskInfo
                        $trigger = $_.Triggers | Select-Object -First 1
                        $timeStr = if ($trigger -and $trigger.StartBoundary) { ([datetime]$trigger.StartBoundary).ToString("HH:mm") } else { "未知" }
                        $neverRun = $info.LastRunTime -lt (Get-Date "2000-01-01")
                        if ($neverRun) {
                            $lastResult = "尚未執行"
                        } elseif ($info.LastTaskResult -eq 0) {
                            $lastResult = "上次成功 " + $info.LastRunTime.ToString("MM/dd HH:mm")
                        } else {
                            $lastResult = "上次失敗 " + $info.LastRunTime.ToString("MM/dd HH:mm")
                        }
                        $color = if ($_.State -eq "Ready") { "Green" } else { "Yellow" }
                        Write-Host ("  [" + $_.State + "] " + $_.TaskName) -ForegroundColor $color
                        Write-Host ("          每天 $timeStr | $lastResult | 下次：" + $info.NextRunTime.ToString("MM/dd HH:mm")) -ForegroundColor DarkGray
                    }
                } else {
                    Write-Host "  [i] 尚無排程任務" -ForegroundColor Yellow
                }
                Write-Host ""
                Write-Host "按任意鍵返回..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "2" {
                if (-not $isAdmin) {
                    Write-Host ""
                    Write-Host "  [!] 此操作需要系統管理員權限" -ForegroundColor Red
                    Write-Host ""
                    $ans = Read-Host "  以系統管理員身份重新開啟選單？[Y/N]"
                    if ($ans -match "^[Yy]") {
                        Start-Process "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -Verb RunAs
                        exit
                    }
                    continue schedMenu
                }
                Write-Host ""
                Write-Host "  ── 新增排程任務 ────────────────────────────" -ForegroundColor Cyan
                Write-Host ""
                try {
                    $jsonRaw = & "$ScriptDir\vault-scheduler.exe" --list-tasks 2>&1
                    $taskList = $jsonRaw | ConvertFrom-Json
                } catch {
                    Write-Host "  [!] 無法讀取任務清單：$_" -ForegroundColor Red
                    Write-Host ""
                    Write-Host "按任意鍵返回..."
                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                    continue schedMenu
                }
                Write-Host "  選擇任務功能："
                Write-Host ""
                for ($i = 0; $i -lt $taskList.Count; $i++) {
                    $t = $taskList[$i]
                    Write-Host ("    " + ($i+1) + ". " + $t.name) -NoNewline
                    Write-Host ("  " + $t.description) -ForegroundColor DarkGray
                    Write-Host ("       建議排程：" + $t.schedule) -ForegroundColor DarkGray
                }
                Write-Host ""
                Write-Host ("    " + ($taskList.Count + 1) + ". 取消")
                Write-Host ""
                $modeInput = Read-Host "  請選擇 [1-$($taskList.Count + 1)]"
                $modeIdx = 0
                if ($modeInput -match "^\d+$") { $modeIdx = [int]$modeInput }
                if ($modeIdx -lt 1 -or $modeIdx -gt $taskList.Count) { continue schedMenu }
                $selectedTask = $taskList[$modeIdx - 1]
                $taskId = $selectedTask.id
                $taskArg = "--task $taskId --headless"
                $defaultName = "AI-MemoryVault-" + ($taskId -replace "-","")
                Write-Host ""
                Write-Host "  任務名稱後綴（預設：$($taskId -replace '-','')，Enter 使用預設）" -ForegroundColor DarkGray
                Write-Host "  ⚠ 前綴 'AI-MemoryVault-' 會自動加上" -ForegroundColor DarkGray
                $suffix = Read-Host "  後綴"
                if (-not $suffix) { $suffix = $taskId -replace '-','' }
                # 清除使用者可能自己加的前綴，避免重複
                $suffix = $suffix -replace '^AI-MemoryVault-', ''
                $taskName = "AI-MemoryVault-$suffix"
                $timeInput = Read-Host "  每天執行時間（HH:MM，如：22:00）"
                if ($timeInput -notmatch "^\d{1,2}:\d{2}$") {
                    Write-Host "  [!] 時間格式錯誤，請輸入 HH:MM" -ForegroundColor Red
                    Start-Sleep -Seconds 2
                    continue schedMenu
                }
                $h = [int]($timeInput.Split(":")[0])
                $m = [int]($timeInput.Split(":")[1])
                try {
                    $action   = New-ScheduledTaskAction -Execute "`"$ScriptDir\vault-scheduler.exe`"" -Argument $taskArg
                    $trigger  = New-ScheduledTaskTrigger -Daily -At ("{0}:{1:D2}" -f $h, $m)
                    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
                    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null
                    $verify = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
                    if ($verify) {
                        $verifyInfo = $verify | Get-ScheduledTaskInfo
                        $nextRun = $verifyInfo.NextRunTime.ToString("yyyy/MM/dd HH:mm")
                        Write-Host ""
                        Write-Host "  [OK] 已建立並驗證成功" -ForegroundColor Green
                        Write-Host "    名稱：$taskName" -ForegroundColor Green
                        Write-Host "    功能：$($selectedTask.name)" -ForegroundColor Green
                        Write-Host "    每天：$timeInput"
                        Write-Host "    下次執行：$nextRun" -ForegroundColor Cyan
                        Write-Host "    執行：vault-scheduler.exe $taskArg" -ForegroundColor DarkGray
                    } else {
                        Write-Host "  [!] 呼叫未回報錯誤，但任務不存在，請檢查權限" -ForegroundColor Red
                    }
                } catch {
                    Write-Host "  [!] 建立失敗：$_" -ForegroundColor Red
                }
                Write-Host ""
                Write-Host "按任意鍵返回..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "3" {
                if (-not $isAdmin) {
                    Write-Host ""
                    Write-Host "  [!] 此操作需要系統管理員權限" -ForegroundColor Red
                    Write-Host ""
                    $ans = Read-Host "  以系統管理員身份重新開啟選單？[Y/N]"
                    if ($ans -match "^[Yy]") {
                        Start-Process "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -Verb RunAs
                        exit
                    }
                    continue schedMenu
                }
                Write-Host ""
                Write-Host "  ── 刪除排程任務 ────────────────────────────" -ForegroundColor Cyan
                Write-Host ""
                $tasks = @(Get-ScheduledTask | Where-Object { $_.TaskName -match "AI-MemoryVault" } -ErrorAction SilentlyContinue)
                if ($tasks.Count -eq 0) {
                    Write-Host "  [i] 尚無排程任務" -ForegroundColor Yellow
                } else {
                    for ($i = 0; $i -lt $tasks.Count; $i++) {
                        Write-Host ("  " + ($i+1) + ". " + $tasks[$i].TaskName)
                    }
                    Write-Host ""
                    $sel = Read-Host "  選擇要刪除的編號（Enter 取消）"
                    if ($sel -match "^\d+$") {
                        $idx = [int]$sel - 1
                        if ($idx -ge 0 -and $idx -lt $tasks.Count) {
                            $name = $tasks[$idx].TaskName
                            try {
                                Unregister-ScheduledTask -TaskName $name -Confirm:$false
                                Write-Host "  [OK] 已刪除：$name" -ForegroundColor Green
                            } catch {
                                Write-Host "  [!] 刪除失敗：$_" -ForegroundColor Red
                            }
                        }
                    }
                }
                Write-Host ""
                Write-Host "按任意鍵返回..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "4" {
                Write-Host ""
                Write-Host "  ── 立即執行一次 ────────────────────────────" -ForegroundColor Cyan
                Write-Host ""
                try {
                    $jsonRaw = & "$ScriptDir\vault-scheduler.exe" --list-tasks 2>&1
                    $taskList = $jsonRaw | ConvertFrom-Json
                } catch {
                    Write-Host "  [!] 無法讀取任務清單：$_" -ForegroundColor Red
                    Write-Host ""
                    Write-Host "按任意鍵返回..."
                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                    continue schedMenu
                }
                Write-Host "  選擇要立即執行的任務："
                Write-Host ""
                for ($i = 0; $i -lt $taskList.Count; $i++) {
                    $t = $taskList[$i]
                    Write-Host ("    " + ($i+1) + ". " + $t.name) -NoNewline
                    Write-Host ("  " + $t.description) -ForegroundColor DarkGray
                }
                Write-Host ""
                Write-Host ("    " + ($taskList.Count + 1) + ". 取消")
                Write-Host ""
                $modeInput = Read-Host "  請選擇 [1-$($taskList.Count + 1)]"
                $modeIdx = 0
                if ($modeInput -match "^\d+$") { $modeIdx = [int]$modeInput }
                if ($modeIdx -lt 1 -or $modeIdx -gt $taskList.Count) { continue schedMenu }
                $selectedTask = $taskList[$modeIdx - 1]
                Write-Host ""
                $startTime = Get-Date
                Write-Host "  [i] 執行「$($selectedTask.name)」中，請稍候..." -ForegroundColor Yellow
                Write-Host "  [i] 開始時間：$($startTime.ToString('yyyy/MM/dd HH:mm:ss'))" -ForegroundColor DarkGray
                Write-Host ""
                & "$ScriptDir\vault-scheduler.exe" --task $selectedTask.id
                $endTime = Get-Date
                $elapsed = ($endTime - $startTime).TotalSeconds
                Write-Host ""
                Write-Host "  [OK] 完成時間：$($endTime.ToString('yyyy/MM/dd HH:mm:ss'))（耗時 $([math]::Round($elapsed, 1)) 秒）" -ForegroundColor Green
                Write-Host ""
                Write-Host "按任意鍵返回..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "5" {
                $LogPath = Join-Path $env:APPDATA "AI-Memory-Vault\scheduler.log"
                Write-Host ""
                if (Test-Path $LogPath) {
                    Write-Host "  ── 排程 Log（最後 40 行）──────────────────" -ForegroundColor Cyan
                    Write-Host "  路徑：$LogPath" -ForegroundColor DarkGray
                    Write-Host ""
                    Get-Content $LogPath -Tail 40 | ForEach-Object {
                        if ($_ -match "\[ERROR\]") {
                            Write-Host $_ -ForegroundColor Red
                        } elseif ($_ -match "\[WARN\]") {
                            Write-Host $_ -ForegroundColor Yellow
                        } else {
                            Write-Host $_
                        }
                    }
                } else {
                    Write-Host "  [i] 尚無 Log（排程從未執行過）" -ForegroundColor Yellow
                    Write-Host "  路徑：$LogPath"
                }
                Write-Host ""
                Write-Host "按任意鍵返回..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "6" {
                Write-Host ""
                Write-Host "  ── 排程診斷 ────────────────────────────────────────────" -ForegroundColor Cyan
                Write-Host ""
                $exeOk = Test-Path "$ScriptDir\vault-scheduler.exe"
                Write-Host ("  vault-scheduler.exe：" + (if ($exeOk) { "✅ 存在" } else { "❌ 找不到！" })) -ForegroundColor (if ($exeOk) { "Green" } else { "Red" })
                if (-not $exeOk) { Write-Host "    路徑：$ScriptDir\vault-scheduler.exe" -ForegroundColor DarkGray }
                Write-Host ""
                $tasks = @(Get-ScheduledTask | Where-Object { $_.TaskName -match "AI-MemoryVault" } -ErrorAction SilentlyContinue)
                if ($tasks.Count -eq 0) {
                    Write-Host "  [!] 尚無排程任務（請先新增）" -ForegroundColor Yellow
                } else {
                    foreach ($t in $tasks) {
                        $info    = $t | Get-ScheduledTaskInfo
                        $result  = $info.LastTaskResult
                        $exeArg  = ($t.Actions | Select-Object -First 1).Execute
                        $exeExists = Test-Path ($exeArg -replace '"', '')
                        Write-Host ("  [" + $t.TaskName + "]") -ForegroundColor Cyan
                        Write-Host ("    狀態      ：" + $t.State)
                        Write-Host ("    上次執行  ：" + $info.LastRunTime)
                        $resultColor = if ($result -eq 0) { "Green" } else { "Red" }
                        $resultStr   = if ($result -eq 0) { "成功 (0x0)" } else { "失敗 (0x{0:X8})" -f $result }
                        Write-Host ("    上次結果  ：" + $resultStr) -ForegroundColor $resultColor
                        Write-Host ("    指向 EXE  ：" + $exeArg) -ForegroundColor DarkGray
                        Write-Host ("    EXE 存在  ：" + (if ($exeExists) { "✅" } else { "❌ 路徑錯誤！" })) -ForegroundColor (if ($exeExists) { "Green" } else { "Red" })
                        if (-not $exeExists) {
                            Write-Host "    → 建議：刪除此任務並重新新增" -ForegroundColor Yellow
                        }
                        Write-Host ""
                    }
                }
                $LogPath = Join-Path $env:APPDATA "AI-Memory-Vault\scheduler.log"
                if (Test-Path $LogPath) {
                    Write-Host "  ── Log 最後 5 行 ──────────────────────────────────" -ForegroundColor DarkGray
                    Get-Content $LogPath -Tail 5 | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor DarkGray }
                }
                Write-Host ""
                Write-Host "按任意鍵返回..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
            "7" { break schedMenu }
            default { Write-Host "  [!] 無效選項" -ForegroundColor Red; Start-Sleep -Seconds 1 }
        }
    }
}

# ══════════════════════════════════════════════════════
#  初始化檢查 + 主選單
# ══════════════════════════════════════════════════════

# ── 若尚未初始化 → 執行設定精靈 ──
while (-not (Test-Path $ConfigPath)) {
    Clear-Host
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  AI Memory Vault v3" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [!] 尚未初始化，啟動設定精靈..." -ForegroundColor Yellow
    Write-Host ""
    & "$ScriptDir\vault-cli.exe" --setup
    Write-Host ""
    Write-Host "按任意鍵繼續..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# ── 主選單迴圈 ──
while ($true) {
    Clear-Host
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  AI Memory Vault v3 - 主選單" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. 環境設定"
    Write-Host "  2. 排程管理"
    Write-Host "  3. CLI 互動模式" -NoNewline; Write-Host "  [開發中]" -ForegroundColor DarkGray
    Write-Host "  4. 離開"
    Write-Host ""
    $choice = Read-Host "請選擇 [1-4]"

    switch ($choice) {
        "1" { Show-EnvSettingsMenu }
        "2" { Show-SchedulerMenu }
        "3" {
            Write-Host ""
            Write-Host "  [i] CLI 互動模式尚在開發中，敬請期待" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "按任意鍵返回..."
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        "4" { exit 0 }
        default {
            Write-Host ""
            Write-Host "  [!] 無效選項，請重新選擇" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}