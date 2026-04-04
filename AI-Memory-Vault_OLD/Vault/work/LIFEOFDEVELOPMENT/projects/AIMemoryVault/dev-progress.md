---
type: dev-progress
project: AIMemoryVault
workspace: LIFEOFDEVELOPMENT
created: 2026.03.29
last_updated: 2026.03.30
ai_summary: "AI Memory Vault 分階段開發進度，v2.3 啟動穩定化：模式預檢系統 + ngrok 自動啟動"
tags: [python, rag, langchain, mcp, fastapi, line-bot, dev-progress]
---

# AI Memory Vault — 開發進度

> **公司**：LIFEOFDEVELOPMENT  
> **最後更新**：2026.03.30

---

## 當前狀態

| 項目 | 值 |
|------|-----|
| 版本 | v2.3（啟動穩定化 + 預檢系統）|
| 階段 | 第四階段（通用化接入，進行中）|
| MCP Server | ✅ 上線 v2.1，VS Code Copilot 已接入 |
| FastAPI | ✅ v2.2，6 端點（含 /webhook/line）|
| LINE Bot | ✅ Webhook 已驗證，端到端串接完成 |
| ngrok | ✅ API 模式啟動時自動背景啟動，Public URL 自動印出 |
| 預檢系統 | ✅ v1.2：三模式皆檢查套件/Ollama/ngrok |
| Python | 3.12.9 + `.venv` |
| LLM | Ollama llama3.1:8b（Gemini 配額耗盡，待換新 key）|

---

## ✅ 第一階段 — 地基穩定（2026.03.28）

- [x] Gemini API 連線 + Ollama 本地切換（.env LLM_PROVIDER）
- [x] 增量同步（SQLRecordManager + ChromaDB，blake2b Hash）
- [x] Markdown 按標題切塊（MarkdownHeaderTextSplitter）
- [x] 分類標籤自動識別（work / life / knowledge / templates / _system）
- [x] 對話上下文（ChatHistory，MAX_HISTORY_TURNS=10）
- [x] 啟動自動同步 + `sync` 內建指令

---

## ✅ 第二階段 — v2.0 架構重建（2026.03.28）

- [x] 多語言 Embedding（paraphrase-multilingual-MiniLM-L12-v2）
- [x] Frontmatter YAML 解析 → metadata 注入
- [x] 模組化重構（13 模組）
- [x] Agent ABC 介面 + AgentRouter + MemoryAgent
- [x] FastAPI REST API
- [x] ChromaDB 升級（langchain_chroma）

---

## ✅ 第三階段 — 大腦強化（2026.03.28）

- [x] Hybrid Search（BM25 40% + Vector 60%）
- [x] 自動化排程（auto_sync.ps1，每日 20:00）
- [x] Recency Bias + Core Memory 系統
- [x] Session 自動存檔

---

## 🔄 第四階段 — 通用化接入（進行中，2026.03.29+）

- [x] MCP Server v2.1（FastMCP SDK，4 tools，VS Code 接入）
- [x] VS Code Prompt 入口（10 個 `/斜線指令`）
- [x] Vault 全域模板系統（templates/sections/ 9 個區域模板）
- [x] **VaultService 重構 v2.1** — 統一業務邏輯入口（Single Source of Truth）
- [x] **Rule 03**：Project API Map Sync（`_AI_Engine/docs/API_MAP.md`）

---

## ✅ 第五階段 — Messaging Gateway（完成，2026.03.29 晚）

- [x] **Messaging Gateway v2.2** — 平台無關接入架構
  - `api/channels/base.py`：BaseChannel ABC
  - `api/channels/line.py`：LineChannel（HMAC-SHA256 + Reply/Push API）
  - `api/chat_service.py`：ChatService（per-user 歷史 + async ainvoke + markdown 清除）
  - `api/app.py v2.2`：新增 `POST /webhook/line`
- [x] **System prompt 大幅強化**（memory_agent.py）：Rules A-G + 1-10
- [x] **ngrok 3.37.x 更新**（ERR_NGROK_121 修正）
- [x] **LINE Webhook 端到端驗證** ✅
- [x] **stop.ps1** — 一鍵停止 port 8000/8001
- [x] **llm_factory.py 修正**：移除錯誤的 `stream=False`
- [x] **chat_service.py async 修正**：`_run_agent_turn` 全用 `ainvoke`
- [x] **LLM 切換**：Gemini 配額耗盡 → Ollama llama3.1:8b

---

## ✅ 第六階段 — 啟動穩定化（完成，2026.03.30）

- [x] **ngrok 自動啟動**（`env_setup.py` 新增 `_launch_ngrok()`）
  - 先查 `localhost:4040/api/tunnels`，已在執行直接印 URL
  - 否則 `Popen` 背景啟動，輪詢等待（最多 5 秒）取得 Public URL
  - authtoken 未設定時仍顯示警告與設定說明
- [x] **模式預檢系統 v1.2**（`env_setup.py`）
  - 新增 `_BASE_PACKAGES`（基礎共用）、`_LLM_PACKAGES`（gemini/ollama）、`_MODE_EXTRA_PACKAGES`（cli/api/mcp）常數
  - 新增 `check_mode_prerequisites(iMode, iPort)` — 統一 pre-flight 入口
  - 新增 `_check_packages(iPackages)` — 逐一 `importlib.util.find_spec` 確認，缺少者詢問是否自動 `pip install`，逐個回報安裝結果
  - 新增 `_check_ollama_service(iBaseUrl)` — 連線測試 `/api/tags`，失敗顯示安裝/啟動說明
- [x] **main.py 三模式全面接入**：cli / api / mcp 皆呼叫 `check_mode_prerequisites()`
- [x] **port 衝突標準做法確立**：系統 Python 定期干擾 port 8000，標準啟動指令固定為 `venv/python main.py --mode api`
- [ ] **Gemini API key** 更換（新 Google AI Studio project）
- [ ] Telegram Channel（`api/channels/telegram.py`）
- [ ] 雲端部署（多裝置共享）

---

## 🐛 已知問題

| 嚴重度 | 問題 | 狀態 |
|--------|------|------|
| ✅ | EnsembleRetriever import 路徑變更 | 已修正 |
| ✅ | ngrok 需手動啟動 | 已修正：API 模式自動啟動 |
| ✅ | 三模式無套件/服務檢查 | 已修正：模式預檢系統 v1.2 |
| ⚠️ | Gemini API 配額耗盡 | 緩解：使用 Ollama llama3.1:8b |
| ⚠️ | ChromaDB 本地，無法多裝置共享 | 規劃：雲端部署 |

---

## 🔧 常用指令

```powershell
cd D:\AI-Memory-Vault\_AI_Engine

# 必須用 venv Python（避免系統 Python 搶 port）
.\.venv\Scripts\python.exe main.py                   # CLI 模式
.\.venv\Scripts\python.exe main.py --mode api        # FastAPI + 自動啟動 ngrok
.\.venv\Scripts\python.exe main.py --mode mcp        # MCP Server

.\stop.ps1                                            # 停止 port 8000/8001
.\auto_sync.ps1 -RegisterSchedule                    # 安裝每日 20:00 自動同步
```
