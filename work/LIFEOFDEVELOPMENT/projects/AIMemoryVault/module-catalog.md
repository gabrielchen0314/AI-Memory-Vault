---
type: module-catalog
project: AIMemoryVault
workspace: LIFEOFDEVELOPMENT
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "AI Memory Vault _AI_Engine v2.1 全模組目錄（含 VaultService 業務邏輯層），14 模組，對外 API 與依賴關係"
tags: [python, langchain, module-catalog, LIFEOFDEVELOPMENT]
---

# AI Memory Vault — 模組目錄

> **公司**：LIFEOFDEVELOPMENT  
> **引擎版本**：`_AI_Engine` v2.1（14 模組）  
> **最後更新**：2026.03.29

---

## 1. 模組清單總覽

| 層次 | 模組 | 檔案 | 主要對外 API |
|:----:|------|------|-------------|
| 基礎 | `config` | `config.py` | `VAULT_ROOT`, `LLM_PROVIDER`, `USE_HYBRID_SEARCH`, `HYBRID_BM25_WEIGHT`, `RECENCY_BIAS_ENABLED`, `CORE_MEMORY_PATH` 等常數 |
| 入口 | `main` | `main.py` | CLI 啟動：`python main.py`；API：`--mode api`；MCP：`--mode mcp` |
| 記憶加工 | `embeddings` | `core/embeddings.py` | `get_embedding_function()` → HuggingFaceEmbeddings |
| 記憶加工 | `llm_factory` | `core/llm_factory.py` | `get_llm()` → ChatOllama \| ChatGoogleGenerativeAI |
| 記憶加工 | `vectorstore` | `core/vectorstore.py` | `get_vectorstore()` → Chroma；`get_record_manager()` → SQLRecordManager |
| 記憶加工 | `indexer` | `core/indexer.py` | `VaultIndexer().sync()` → dict；`VaultIndexer().sync_single(iAbsPath)` → dict |
| 記憶加工 | `retriever` | `core/retriever.py` | `VaultRetriever().search(iQuery, iCategory, iDocType)` → list；`VaultRetriever().search_formatted(...)` → str |
| **業務邏輯** | **`vault_service`** | **`services/vault_service.py`** | **`VaultService.read_note(iFilePath)` → (content, error)；`.write_note(iFilePath, iContent, iMode)` → (stats, error)；`.search(iQuery, ...)` → list；`.search_formatted(...)` → str；`.sync()` → dict** |
| 工具層 | `sync` | `tools/sync.py` | `@tool sync_notes()` → str（委派 VaultService.sync） |
| 工具層 | `search` | `tools/search.py` | `@tool search_notes(iQuery, iCategory, iDocType)` → str（委派 VaultService.search_formatted） |
| 工具層 | `read` | `tools/read.py` | `@tool read_note(iFilePath)` → str（委派 VaultService.read_note） |
| 工具層 | `write` | `tools/write.py` | `@tool write_note(iFilePath, iContent, iMode)` → str（委派 VaultService.write_note） |
| Agent 層 | `base` | `agents/base.py` | `class BaseAgent(ABC)`：`run(iInput) → str` |
| Agent 層 | `memory_agent` | `agents/memory_agent.py` | `class MemoryAgent(BaseAgent)`：`run(iInput) → str` |
| Agent 層 | `router` | `agents/router.py` | `class AgentRouter`：`route(iInput) → BaseAgent`；`run(iInput) → str` |
| 接入層 | `app` | `api/app.py` | GET `/health`；POST `/sync`；POST `/search`；POST `/read`；POST `/write` |
| 接入層 | `schemas` | `api/schemas.py` | `SearchRequest`, `SearchResponse`, `SyncResponse`, `ReadRequest`, `ReadResponse`, `WriteRequest`, `WriteResponse` |
| 接入層 | `mcp_server` | `mcp_server.py` | `search_vault(query, category, doc_type)`；`sync_vault()`；`read_note(file_path)`；`write_note(file_path, content)` |
| 接入層 | `repl` | `cli/repl.py` | `run_repl()` → 啟動互動終端（內建指令：sync / save / q） |

---

## 2. 依賴關係圖

```
main.py
├── cli/repl.py        → agents/router.py → agents/memory_agent.py
│                                              └── tools/* → VaultService
├── api/app.py         → VaultService（直接呼叫，不透過 tools/）
└── mcp_server.py      → VaultService（直接呼叫，不透過 tools/）

VaultService (services/vault_service.py)
├── config.py（VAULT_ROOT）
├── core/indexer.py（lazy import，sync / sync_single）
└── core/retriever.py（lazy import，search / search_formatted）

core/indexer.py        → core/vectorstore.py + core/embeddings.py
core/retriever.py      → core/vectorstore.py + core/embeddings.py + core/llm_factory.py（可選）
core/vectorstore.py    → config.py（VECTOR_DB_PATH）
core/embeddings.py     → config.py（EMBEDDING_MODEL）
core/llm_factory.py    → config.py（LLM_PROVIDER / GEMINI_API_KEY / OLLAMA_BASE_URL）
```

---

## 3. 各模組簡述

### services/vault_service.py ⭐（v2.1 新增）
- **責任**：統一業務邏輯入口（Single Source of Truth），所有路徑驗證、檔案讀寫、搜尋、同步都集中於此
- **重要方法**：
  - `read_note(iFilePath)` → `(content, error)`：路徑驗證→讀取→回傳
  - `write_note(iFilePath, iContent, iMode)` → `(stats_dict, error)`：路徑驗證+.md 檢查→寫入→自動 sync_single 索引
  - `search(iQuery, iCategory, iDocType, iTopK)` → `list[dict]`
  - `search_formatted(iQuery, iCategory, iDocType)` → `str`
  - `sync()` → `dict`
- **安全**：`_validate_path()` 防路徑穿越，`_validate_write_path()` 限 .md 寫入
- **設計決策**：core/ lazy import，避免啟動時載入重型模型

### config.py
- **責任**：唯一的全域設定來源，Pydantic BaseSettings，從 `.env` 自動載入
- **重要設定**：
  - `VAULT_ROOT`：Vault 根目錄絕對路徑
  - `LLM_PROVIDER`：`ollama` | `gemini`
  - `USE_HYBRID_SEARCH`：True/False
  - `RECENCY_BIAS_ENABLED`：True/False（指數衰減重排序）
  - `CORE_MEMORY_PATH`：`_system/core-memory.md`

### core/indexer.py
- **責任**：掃描 Vault 所有 `.md` → Frontmatter 解析 → MarkdownHeaderTextSplitter 切塊 → 增量同步至 ChromaDB
- **重要方法**：`sync()` 全量增量；`sync_single(iAbsPath)` 單檔即時索引
- **例外處理**：跳過 EXCLUDE_DIRS（chroma_db, .venv, .ai_memory 等）

### core/retriever.py
- **責任**：Hybrid Search（BM25 + Vector）+ Metadata 過濾 + Recency Bias 重排序
- **Recency Bias**：指數衰減，T½=90天，優先排序 last_updated > date > created
- **回傳格式**：`search_formatted()` 返回 Markdown 格式字串（每筆含 source + score）
- **注意**：EnsembleRetriever 從 `langchain_classic.retrievers.ensemble` 匯入（langchain v1.2.13）

### agents/memory_agent.py
- **責任**：預設記憶 Agent，整合 4 工具 + ChatHistory + Core Memory
- **Core Memory**：啟動時讀取 `_system/core-memory.md` 注入 System Prompt（去除 Frontmatter）
- **ChatHistory**：保留最近 MAX_HISTORY_TURNS（預設 10）輪

### mcp_server.py
- **責任**：MCP Server v2.1，以官方 FastMCP SDK 封裝 4 個 MCP tools，全部委派至 VaultService
- **安全**：`_StdoutToStderr` 防止 stdout 污染 JSON-RPC 通道

---

## 4. 設定檔索引

| 檔案 | 用途 |
|------|------|
| `_AI_Engine/.env` | LLM_PROVIDER / API Key / 各種開關（不 commit） |
| `_AI_Engine/requirements.txt` | Python 依賴清單 |
| `.vscode/mcp.json` | VS Code Copilot MCP Server 設定 |
| `_AI_Engine/auto_sync.ps1` | Windows 工作排程腳本（每日 20:00） |
| `_AI_Engine/docs/API_MAP.md` | 模組公開 API 速查手冊（Rule 03 規範） |
