---
project: ai-memory-vault
org: lifeofdevelopment
date: 2026-04-08
session: scheduler-bugfix
type: conversation
---

# 對話紀錄 — 2026-04-08（排程任務名稱 Bug 修正）

## 對話主題

排程新增成功但查詢看不到 → 診斷根因 → 修正 + 清理殘留 + 重建 Installer

## 問題與解法

| 問題 | 解法 |
|------|------|
| 新增排程顯示 OK，但查詢清單是空的 | 查詢用 `TaskName -match "AI-MemoryVault"` 但名稱是自訂的 "Test Daily" 不符過濾 |
| 驗證邏輯用 `Get-ScheduledTask -TaskName $taskName` 仍找得到 | 所以顯示「建立成功」，但清單掃描是 regex 過濾，不一致 |
| 測試殘留 `Test Daily`、`Test` 兩個任務 | 以管理員身份 `Unregister-ScheduledTask` 清除 |

## 修改的檔案

- `packaging/shortcuts/vault-menu.ps1` — 改為輸入後綴，強制加 `AI-MemoryVault-` 前綴，防止重複
- `C:\Program Files (x86)\AI Memory Vault\vault-menu.ps1` — 同步更新
- `dist/AI-Memory-Vault-Setup-v3.5.0.exe` — 重建（只跑 Inno Setup，未重跑 PyInstaller）

## 診斷過程

1. 查詢 `Get-ScheduledTask | Where-Object { $_.TaskPath -eq "\" }` → 看到 "Test Daily"
2. 確認是 `vault-scheduler.exe` 建的（Action.Execute 符合）
3. 確認根目錄下名稱含 vault/memory/test 等關鍵字 → 只剩 "Test"（無 --task 參數版本）
4. 修正輸入邏輯 → 重建 Installer
