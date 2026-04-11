---
type: conversation-detail
date: 2026-04-11
session: vault-data-dir-configurable
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
tags: [conversation, detail]
---

# 2026-04-11 vault-data-dir-configurable — 詳細對話紀錄

## 對話概要
- **主題**：VAULT_DATA_DIR 可設定支援 + vault-menu.ps1 資料目錄管理 GUI

## 修改的檔案清單

| 檔案 | 操作 | 摘要 |
|------|------|------|
| `README.md` | 重寫 | v3.7.0 完整重寫：3 種部署模式、40 MCP 工具表格、22 CLI 指令、開發流程章節 |
| `AI_Engine/config.py` | 修改 | 所有模式（dev/frozen/Docker）優先讀取 VAULT_DATA_DIR 環境變數，frozen 不再硬編碼 APPDATA |
| `AI_Engine/packaging/shortcuts/vault-menu.ps1` | 修改 | 新增 Show-DataDirMenu 函式、擴充 Show-EnvSettingsMenu 至 7 選項、所有路徑改為 VAULT_DATA_DIR-aware |
| `AI_Engine/config.json` | 還原 | 從 .bak 還原，修正被 pytest 污染的 test_user/TEST_ORG 路徑 |
| `%APPDATA%/AI-Memory-Vault/config.json` | 建立/修正 | vault_path 修正為 D:\AI-Memory-Vault\Vault，正確 org 設定 |

## 執行的命令

| 命令 | 目的 | 結果 |
|------|------|------|
| `cd AI_Engine/packaging; .\build.ps1 -Clean` | 重建三個 exe | 成功，756.9 MB，235 秒 |
| `ISCC installer.iss` | 打包 Setup.exe | AI-Memory-Vault-Setup-v3.7.0.exe 成功 |
| `pip install -r requirements.txt` | 修復遺失套件（filelock, uvicorn, mcp） | 成功 |
| `python -m pytest tests/ -q` | 驗證測試 | 247 passed |

## 遇到的問題與解決

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| venv 遺失 filelock/uvicorn/mcp 套件 | 某次操作後 venv 套件不完整 | pip install -r requirements.txt 重新安裝 |
| config.json 被 pytest 污染（test_user/TEST_ORG 路徑） | 測試沒有妥善 teardown | 從 config.json.bak 還原 |
| APPDATA config.json vault_path 指向 C:\ | 初次複製時用了錯誤值 | 手動更新為 D:\AI-Memory-Vault\Vault |
| vault-menu.ps1 變更目錄流程語義錯誤（先設環境變數再複製） | 初版設計順序有誤 | 改為：展示計畫→確認→搬移→成功後才設環境變數，搬移失敗則停止 |

## 學到的知識

- config.py 用 getattr(sys, 'frozen', False) 判斷是否為 PyInstaller exe 模式
- PowerShell Copy-Item 需加 -ErrorAction Stop 才能被 try/catch 捕捉錯誤
- pytest 缺乏 teardown fixture 會污染正式 config.json，應永遠使用 tmp_path fixture 隔離測試資料
- Installer 模式下 DATA_DIR 原先硬編碼 APPDATA，新增 VAULT_DATA_DIR 環境變數可覆蓋任何模式

## 決策記錄

| 決策 | 選項 | 最終選擇 | 理由 |
|------|------|---------|------|
| VAULT_DATA_DIR 在 if/else block 之前提取 | A: 在 frozen branch 內處理 / B: 在 block 前統一提取 | B | 統一邏輯，避免在兩個 branch 重複，且讓 dev 模式也能使用同一變數覆蓋 |
| 搬移語義：copy+delete vs robocopy vs Move-Item | Copy-Item+Remove-Item / Move-Item / Robocopy | Copy-Item+Remove-Item | 跨磁碟搬移 Move-Item 可能失敗；Copy 後確認再刪除原始更安全；錯誤可控 |
