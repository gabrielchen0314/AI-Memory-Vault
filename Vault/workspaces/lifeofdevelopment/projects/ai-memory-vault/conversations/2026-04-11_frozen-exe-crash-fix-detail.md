---
type: conversation-detail
date: 2026-04-11
session: frozen-exe-crash-fix
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
tags: [conversation, detail]
---

# 2026-04-11 frozen-exe-crash-fix — 詳細對話紀錄

## 對話概要
- **主題**：Frozen exe MCP 模式崩潰修復 + DATA_DIR 統一 + 清理

## 關鍵問答紀錄

### Q1: frozen exe 為何崩潰？
- **AI 分析**：透過逐步 DIAG stderr 診斷，定位到 from langchain_text_splitters import ... 觸發 C-level STATUS_STACK_BUFFER_OVERRUN。__init__.py 載入 spacy/nltk/konlpy 等子模組，某些在 PyInstaller frozen 環境下的 C extension 會崩潰
- **決策**：用 importlib 預註冊空 package 在 sys.modules，繞過 __init__.py
- **替代方案**：1. 排除整個 langchain_text_splitters（不可行，核心依賴）2. 加 collect_all 到 build.spec（可能打包更多不需要的東西）3. 降版 langchain_text_splitters（治標不治本）

### Q2: 為什麼 dev 和 exe 設定不同步？
- **AI 分析**：dev DATA_DIR = AI_Engine/，frozen DATA_DIR = %APPDATA%\AI-Memory-Vault\，兩邊各自維護 config.json / vault_meta.json / chroma_db
- **決策**：統一 DATA_DIR 到 %APPDATA%\AI-Memory-Vault\，dev 和 frozen 共用
- **替代方案**：用 symlink（Windows 權限問題）、用環境變數指定（額外設定負擔）

## 修改的檔案清單

| 檔案 | 操作 | 摘要 |
|------|------|------|
| `AI_Engine/core/indexer.py` | 修改 | _get_splitters() 用 importlib 繞過 __init__.py 全量匯入 |
| `AI_Engine/core/retriever.py` | 修改 | BM25/Ensemble 延遲匯入（先前步驟） |
| `AI_Engine/config.py` | 修改 | 統一 DATA_DIR 到 %APPDATA%\AI-Memory-Vault\ |
| `AI_Engine/main.py` | 修改 | 移除所有 DIAG stderr 輸出 |
| `AI_Engine/services/vault.py` | 修改 | 移除所有 DIAG stderr 輸出 |

## 遇到的問題與解決

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| frozen exe 在 from langchain_text_splitters import ... 時 C-level crash (0xC0000409) | __init__.py 載入所有子模組（含 spacy/nltk/konlpy），某些 C extension 在 frozen 環境觸發 stack buffer overrun | importlib 預註冊空 package 繞過 __init__.py |
| dev 和 exe 的 vault_meta.json / config.json / chroma_db 不同步 | DATA_DIR 分離：dev = AI_Engine/，frozen = %APPDATA% | 統一 DATA_DIR 到 %APPDATA%\AI-Memory-Vault\ |

## 學到的知識

- langchain_text_splitters v1.1.1 的 __init__.py 會 import ALL 子模組（包括 spacy/nltk/konlpy），在 PyInstaller frozen 環境可能觸發 C-level crash
- PyInstaller frozen 環境下 C-level crash (STATUS_STACK_BUFFER_OVERRUN) 無法被 Python try-except 捕獲
- importlib.util.find_spec() 可以取得 package 的 submodule_search_locations 而不執行 __init__.py
- dev 和 frozen 共用 DATA_DIR 可以避免設定不同步的根本問題

## 決策記錄

| 決策 | 選項 | 最終選擇 | 理由 |
|------|------|---------|------|
| 統一 DATA_DIR 到 %APPDATA% | A. 統一到 AppData / B. 保持分離用 env var | A | 消除兩份設定不同步的根本原因，dev 改設定 exe 也馬上看到 |
