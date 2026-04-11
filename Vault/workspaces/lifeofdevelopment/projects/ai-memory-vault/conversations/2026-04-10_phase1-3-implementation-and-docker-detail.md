---
type: conversation-detail
date: 2026-04-10
session: phase1-3-implementation-and-docker
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
tags: [conversation, detail]
---

# 2026-04-10 phase1-3-implementation-and-docker — 詳細對話紀錄

## 對話概要
- **主題**：Phase 1-3 Roadmap 完整實作 + Docker 容器化 + 文件同步

## 修改的檔案清單

| 檔案 | 操作 | 摘要 |
|------|------|------|
| `mcp_app/server.py` | 修改 | 新增 _on_vault_write hook + _register/_unregister_write_hooks + lifespan 整合 |
| `tests/test_backup.py` | 新增 | BackupService 11 個測試（zip、cleanup、list） |
| `tests/test_auto_learn_hooks.py` | 新增 | Auto-learn 8 個 + post-write hook 6 個測試 |
| `Dockerfile` | 新增 | python:3.12-slim 容器，SSE 模式，healthcheck |
| `docker-compose.yml` | 新增 | mcp-sse + scheduler 雙服務，shared volumes |
| `.dockerignore` | 新增 | 排除 .venv、__pycache__、chroma_db、tests |
| `config.py` | 修改 | 新增 VAULT_DATA_DIR 環境變數覆蓋 DATA_DIR |
| `services/vault.py` | 修改 | filelock + post-write hook 基礎建設 |
| `services/backup.py` | 新增 | BackupService（backup_chromadb、cleanup、list_backups） |
| `services/auto_scheduler.py` | 修改 | db-backup cron + handlers |
| `services/scheduler.py` | 修改 | _auto_learn_instincts pipeline |
| `mcp_app/tools/index_tools.py` | 修改 | backup_chromadb MCP 工具 |
| `main.py` | 修改 | _start_api SSE 整合 |
| `requirements.txt` | 修改 | ~= 釘選 + filelock~=3.25 |

## 遇到的問題與解決

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| monkeypatch 目標錯誤：InstinctService lazy import | _auto_learn_instincts 內部用 from services.instinct import InstinctService，monkeypatch services.scheduler.InstinctService 無效 | 改 monkeypatch 目標為 services.instinct.InstinctService |
| BackupService 測試 DATA_DIR 洩漏 | get_chroma_path() 使用全域 DATA_DIR，不受 tmp_path 影響 | monkeypatch DatabaseConfig 實例的 get_chroma_path 方法 |
| post-write hooks 定義但未註冊 | VaultService 有 hook 基礎建設但無實際 hook 被 register | 在 mcp_app/server.py 新增 _on_vault_write 並在 lifespan 註冊 |

## 學到的知識

- FastMCP 原生支援 SSE，透過 sse_app() 取得 Starlette app 再由 uvicorn 承載
- filelock 在 Windows/Linux 跨平台有效，適合 MCP+scheduler 雙行程場景
- lazy import 的 monkeypatch 需 patch 模組來源而非使用處
- Docker compose 可用 named volumes 在服務間共享資料

## 決策記錄

| 決策 | 選項 | 最終選擇 | 理由 |
|------|------|---------|------|
| hook 在 MCP lifespan 註冊而非模組級 | 模組級 / server lifespan / VaultService 初始化時 | server lifespan | 生命週期對齊、shutdown 時自動解除 |
| BackupService 獨立為 services/backup.py | 放在 vault.py / 獨立檔案 / 放在 auto_scheduler.py | 獨立檔案 | 單一職責、可獨立測試 |
| VAULT_DATA_DIR 環境變數覆蓋 | 命令列參數 / 環境變數 / 設定檔 | 環境變數 | Docker 最自然的配置方式 |
