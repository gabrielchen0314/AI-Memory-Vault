---
type: dev-progress
project: AIMemoryVault
workspace: LIFEOFDEVELOPMENT
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "AI Memory Vault 分階段開發進度，v2.2 Messaging Gateway 完成，LINE Bot 端到端串接"
tags: [python, rag, langchain, mcp, fastapi, line-bot, dev-progress]
---

# AI Memory Vault — 開發進度

> **公司**：LIFEOFDEVELOPMENT  
> **最後更新**：2026.03.29

---

## 當前狀態

| 項目 | 值 |
|------|-----|
| 版本 | v2.2（Messaging Gateway 完成）|
| 階段 | 第四階段（通用化接入，進行中）|
| MCP Server | ✅ 上線 v2.1，VS Code Copilot 已接入 |
| FastAPI | ✅ v2.2，6 端點（含 /webhook/line）|
| LINE Bot | ✅ Webhook 已驗證，端到端串接完成 |
| Python | 3.12.9 + `.venv` |
| LLM | Ollama llama3.1:8b（Gemini 配額耗盡，待換新 key）|

---

## ✅ 第一階段 — 地基穩定（2026.03.28）

- [x] Gemini API 連線（gemini-2.0-flash-lite）+ Ollama 本地切換（.env LLM_PROVIDER）
- [x] 增量同步（SQLRecordManager + ChromaDB，blake2b Hash）
- [x] Markdown 按標題切塊（MarkdownHeaderTextSplitter）
- [x] 分類標籤自動識別（work / life / knowledge / templates / _system）
- [x] 對話上下文（ChatHistory，MAX_HISTORY_TURNS=10）
- [x] API Key 改用 .env，429 額度提示 + Ctrl+C 退出
- [x] 串流輸出（逐字印出）
- [x] 啟動自動同步 + `sync` 內建指令

---

## ✅ 第二階段 — v2.0 架構重建（2026.03.28）

- [x] 多語言 Embedding（all-MiniLM-L6-v2 → paraphrase-multilingual-MiniLM-L12-v2，50+ 語言）
- [x] Frontmatter YAML 解析 → metadata 注入（type / domain / workspace / severity / tags）
- [x] 模組化重構（單檔 400 行 → 13 模組：config / core / tools / agents / api / cli）
- [x] Agent ABC 介面（BaseAgent）+ AgentRouter（@mention 路由）+ MemoryAgent
- [x] FastAPI REST API（/health, /sync, /search）
- [x] ChromaDB 升級（langchain_community → langchain_chroma）
- [x] blake2b Hash 取代 SHA-1
- [x] 分類標籤擴充（+templates, +_system）
- [x] 向量庫完整重建（379 chunks，28 files，0 未分類）

---

## ✅ 第三階段 — 大腦強化（2026.03.28）

- [x] Session 自動存檔（`save` + `q` / Ctrl+C，存至 `.ai_memory/logs/`）
- [x] Hybrid Search（BM25 40% + Vector 60%，EnsembleRetriever，Source-level dedup）
  - 設定：`USE_HYBRID_SEARCH=True`，`HYBRID_BM25_WEIGHT=0.4`
- [x] 自動化排程（`auto_sync.ps1`，`-RegisterSchedule` 每日 20:00，`-UnregisterSchedule` 移除）
- [x] 記憶分層：
  - Recency Bias：指數衰減重排序（T½=90天，priority: last_updated > date > created）
  - Core Memory：`_system/core-memory.md` 啟動時自動注入 System Prompt
  - 設定：RECENCY_BIAS_ENABLED / RECENCY_DECAY_DAYS / CORE_MEMORY_ENABLED / CORE_MEMORY_PATH
- [~~] 專案索引（跳過：Vault 定位是知識/決策，程式碼由 VS Code Copilot 負責；改以手工 architecture.md 替代）

---

## 🔄 第四階段 — 通用化接入（進行中，2026.03.29）

- [x] MCP Server Pure JSON-RPC 實作（Python 3.9+ 相容，測試通過）
- [x] Python 3.12.9 安裝 + `.venv` 重建（舊 3.9 環境取代）
- [x] MCP Server 升級為官方 FastMCP SDK（`mcp[cli]>=1.0.0`）
  - `mcp_server.py` v2.0：`@mcp.tool()` 裝飾器，4 tools，~100 行
  - `.vscode/mcp.json` 設定完成，VS Code Copilot 原生接入 ✅
  - 啟動：`python main.py --mode mcp`
- [x] VS Code Prompt 入口（10 個 `/斜線指令`，動態載入 Vault Agent 模板）
  - /planner / /architect / /code-reviewer / /tdd-guide / /refactor-cleaner
  - /security-reviewer / /build-error-resolver / /doc-updater / /git-committer / /learn-trigger
- [x] Vault 知識庫架構整理（2026.03.29）
  - 建立 `templates/projects/` 模板系統（python-app / unity-game / vscode-ext）
  - 補齊 `LIFEOFDEVELOPMENT/rules/`（01-python-coding-style / 02-ai-engine-architecture）
  - 補齊 `AIMemoryVault/` 缺少文件（architecture.md / dev-progress.md / module-catalog.md）
  - 更新 AGENTS.md 加入自動偵測/模板流程
  - 更新 Architect Agent 模板
- [x] **Vault 全域模板系統**（2026.03.29）
  - `templates/sections/` — 9 個區域模板
  - `templates/index.md` — 全域主索引（含自動偵測流程）
  - `_system/AGENTS.md` v3 — §4 全域模板檢查規則
  - `templates/agents/architect.md` — 偵測範圍擴展至全 Vault
- [x] **VaultService 重構 — v2.1**（2026.03.29）
  - 新增 `services/vault_service.py` — 統一業務邏輯入口（Single Source of Truth）
  - 重構 `tools/*.py` 為薄封裝，全部委派至 VaultService
  - 重構 `mcp_server.py` v2.1 — 移除直接 core/ 依賴，委派至 VaultService
  - 重構 `api/app.py` v2.1 — 委派至 VaultService + 新增 `/read`、`/write` 端點
  - 更新 `api/schemas.py` — 新增 ReadRequest/ReadResponse、WriteRequest/WriteResponse
  - 修正 `core/retriever.py` — EnsembleRetriever import 從 `langchain_classic.retrievers.ensemble`
  - 全 E2E 測試通過（read / path traversal blocked / .md check / search / search_formatted）

## 🔄 第五階段 — Messaging Gateway（完成，2026.03.29 晚）

- [x] **Messaging Gateway v2.2** — 平台無關接入架構
  - `api/channels/base.py`：BaseChannel ABC（`verify_request` / `parse_messages` / `send_reply`）
  - `api/channels/line.py`：LineChannel — HMAC-SHA256 驗簽 + 訊息解析 + Reply API
    - 額外方法：`send_ack()`（即時確認）、`send_push()`（非同步推播，需付費方案）
  - `api/channels/__init__.py`
  - `api/chat_service.py`：ChatService — per-user 對話歷史 + multi-round 工具呼叫
    - `_strip_markdown()` — 強制移除 Markdown 語法、結構標籤、工具自言自語
    - `_TOOL_LEAK_KEYWORDS` — 偵測並過濾工具名稱/JSON 洩漏
    - `MAX_TOOL_ROUNDS = 10` — 工具呼叫上限
    - `async def _run_agent_turn` — 全面改用 `ainvoke`，避免阻塞 asyncio event loop
    - `logger.error` — 例外不再靜默吞掉
  - `api/app.py v2.2`：新增 `POST /webhook/line`（驗簽 + 解析 + handle + 回覆）
- [x] **System prompt 大幅強化**（`agents/memory_agent.py`）
  - Rules A-G：禁止問使用者工具參數、禁止自言自語、禁止結構標籤、禁止洩漏 JSON
  - Rules 1-10：立即搜尋、「所有」問題多輪搜尋、100% 繁體中文、禁 Markdown、禁追問
- [x] **ngrok 3.37.3 更新**（舊版 3.3.1 authtoken 格式不相容，ERR_NGROK_121）
- [x] **LINE Webhook 端到端驗證** ✅（POST /webhook/line 回應 200，HMAC 驗簽通過）
- [x] **stop.ps1** — 一鍵停止 port 8000/8001 的 Python 程序
- [x] **llm_factory.py 修正**：移除錯誤的 `stream=False`，明確傳入 `google_api_key`
- [x] **PORT 衝突診斷與修正**：系統 Python（無 venv）偷佔 port 8000 → 統一用 `venv/python main.py --mode api`
- [ ] **Gemini API key**：免費配額耗盡（`limit: 0`），需在 Google AI Studio 建立新 project key
- [ ] Telegram Channel（`api/channels/telegram.py`）
- [ ] 雲端部署（多裝置共享）
- [x] **新增規則 03：Project API Map Sync**（2026.03.29）
  - `work/LIFEOFDEVELOPMENT/rules/03-project-api-map-sync.md`
  - 規定：程式專案在 Vault 建立知識結構時，同步建立 `docs/API_MAP.md` 於專案原始碼目錄
  - 首次套用：建立 `_AI_Engine/docs/API_MAP.md`
- [ ] LINE Bot 部署（串接 FastAPI + LINE Messaging API）
- [ ] 雲端部署（向量庫上雲，多裝置共享）

---

## 🐛 已知問題

| 嚴重度 | 問題 | 狀態 |
|--------|------|------|
| ✅ | langchain v1.2.13 EnsembleRetriever import 路徑變更 | 已修正：改用 `langchain_classic.retrievers.ensemble` |
| ⚠️ | Gemini API 429 額度限制（免費版 RPM 低） | 緩解：.env 切換 Ollama |
| ⚠️ | ChromaDB 本地，無法多裝置共享 | 規劃：雲端部署 |
| 💡 | LINE Bot 未實作 | 第四階段待辦 |

---

## 🔧 常用指令

```powershell
cd D:\AI-Memory-Vault\_AI_Engine

python main.py                   # CLI 模式
python main.py --mode api        # FastAPI：http://127.0.0.1:8000
python main.py --mode mcp        # MCP Server（VS Code 自動呼叫）
.\auto_sync.ps1 -RegisterSchedule  # 安裝每日 20:00 自動同步
```
