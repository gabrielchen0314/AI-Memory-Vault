# API Map — AI Memory Vault Engine

> 模組公開 API 速查手冊，依 `services/vault_service.py` 重構後架構（v2.1）

---

## 架構總覽

```
main.py --mode=
  ├── cli  → MemoryAgent → LangChain @tool → ┐
  ├── api  → FastAPI endpoints ──────────────→├── VaultService → core/*
  └── mcp  → FastMCP @mcp.tool() ───────────→┘
```

---

## 模組總覽

| 模組 | 職責 | 入口檔案 | 對外方法數 |
|------|------|---------|-----------|
| services | 業務邏輯統一入口 | `services/vault_service.py` | 5 |
| tools | LangChain @tool 薄封裝 | `tools/__init__.py` | 4 |
| mcp_server | MCP stdio server | `mcp_server.py` | 4 |
| api | FastAPI REST 端點 | `api/app.py` | 5 |
| agents | LLM Agent 基底 + 路由 | `agents/memory_agent.py` | 3 |
| core | 底層引擎（嵌入/索引/搜尋/向量庫） | `core/` | 6 |
| config | 全域設定 | `config.py` | 2 |
| cli | 互動終端 | `cli/repl.py` | 1 |

---

## services/vault_service.py

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `read_note` | `iFilePath: str` | `(content, error)` | 讀取筆記（含路徑驗證） |
| `write_note` | `iFilePath, iContent, iMode="overwrite"` | `(stats_dict, error)` | 寫入+自動索引（含 .md 檢查） |
| `search` | `iQuery, iCategory="", iDocType="", iTopK=None` | `list[dict]` | 語意搜尋（Hybrid/Pure） |
| `search_formatted` | `iQuery, iCategory="", iDocType=""` | `str` | 搜尋 + 格式化文字 |
| `sync` | — | `dict` | 全量增量同步 |

---

## tools/ （LangChain @tool）

| 工具名稱 | 對應 VaultService 方法 | LLM 用途描述 |
|----------|----------------------|-------------|
| `sync_notes` | `VaultService.sync()` | 同步筆記 |
| `search_notes` | `VaultService.search_formatted()` | 搜尋記憶庫 |
| `read_note` | `VaultService.read_note()` | 讀取檔案 |
| `write_note` | `VaultService.write_note()` | 寫入/更新檔案 |

---

## mcp_server.py （MCP @mcp.tool）

| 工具名稱 | 對應 VaultService 方法 | 說明 |
|----------|----------------------|------|
| `search_vault` | `VaultService.search_formatted()` | Hybrid 搜尋 |
| `sync_vault` | `VaultService.sync()` | 增量同步 |
| `read_note` | `VaultService.read_note()` | 讀取筆記 |
| `write_note` | `VaultService.write_note()` | 寫入+索引 |

---

## api/app.py （FastAPI REST）

| 端點 | Method | 對應 VaultService 方法 | Request Model | Response Model |
|------|--------|----------------------|---------------|----------------|
| `/health` | GET | — | — | `{status, version}` |
| `/sync` | POST | `VaultService.sync()` | — | `SyncResponse` |
| `/search` | POST | `VaultService.search()` | `SearchRequest` | `SearchResponse` |
| `/read` | POST | `VaultService.read_note()` | `ReadRequest` | `ReadResponse` |
| `/write` | POST | `VaultService.write_note()` | `WriteRequest` | `WriteResponse` |

---

## core/

| 模組 | 類別/函式 | 主要方法 | 說明 |
|------|----------|---------|------|
| `config.py` | `Settings` | `.LLM_PROVIDER`, `.SEARCH_TOP_K`, ... | Pydantic BaseSettings |
| `config.py` | `VAULT_ROOT` | — | 路徑常數 |
| `embeddings.py` | `get_embeddings()` | — | multilingual-MiniLM-L12-v2 singleton |
| `vectorstore.py` | `get_vectorstore()` | — | ChromaDB singleton |
| `vectorstore.py` | `get_record_manager()` | — | SQL RecordManager singleton |
| `indexer.py` | `VaultIndexer` | `.sync()`, `.sync_single()` | 掃描+切塊+增量寫入 |
| `retriever.py` | `VaultRetriever` | `.search()`, `.search_formatted()` | Hybrid/Vector+Recency |
| `llm_factory.py` | `create_llm()` | — | Gemini/Ollama 工廠 |

---

## agents/

| 類別 | 方法/屬性 | 說明 |
|------|----------|------|
| `BaseAgent` (ABC) | `._define_system_prompt()`, `._define_tools()` | 抽象介面 |
| `BaseAgent` | `.llm_with_tools`, `.system_message`, `.tools` | 屬性 |
| `MemoryAgent` | `._load_core_memory()` | 注入 core-memory.md 至 System Prompt |
| `AgentRouter` | `.register()`, `.route()` | @mention 路由 |

---

*最後更新：2026.03.29 — VaultService 重構後*
