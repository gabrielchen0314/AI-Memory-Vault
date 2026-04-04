---
type: architecture
project: AIMemoryVault
workspace: LIFEOFDEVELOPMENT
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "AI Memory Vault 各模組的責任邊界、資料流與關鍵設計決策（v2.2 Messaging Gateway 完成）"
tags: [python, langchain, fastapi, mcp, architecture]
---

# AI Memory Vault — 架構文件

> **公司**：LIFEOFDEVELOPMENT  
> **版本**：v2.2  
> **最後更新**：2026.03.29

---

## 1. 模組責任表

| 模組 | 檔案 | 層次 | 職責 | 主要依賴 |
|------|------|:----:|------|----------|
| `config` | `config.py` | 基礎 | 全域設定（Pydantic BaseSettings，從 .env 載入） | pydantic-settings |
| `embeddings` | `core/embeddings.py` | 記憶加工層 | 初始化多語言向量模型（multilingual-MiniLM-L12-v2） | sentence-transformers |
| `llm_factory` | `core/llm_factory.py` | 邏輯大腦層 | LLM 可插拔初始化（Ollama / Gemini，由 .env 切換） | langchain-google-genai / langchain-ollama |
| `vectorstore` | `core/vectorstore.py` | 記憶加工層 | ChromaDB + SQLRecordManager 初始化 | chromadb, langchain-chroma |
| `indexer` | `core/indexer.py` | 記憶加工層 | 掃描 Vault → Frontmatter 解析 → 切塊 → 增量同步 | langchain, chromadb |
| `retriever` | `core/retriever.py` | 記憶加工層 | Hybrid Search（BM25+Vector）+ 多維度 Metadata 過濾 + Recency Bias | langchain, rank_bm25 |
| **`vault_service`** | **`services/vault_service.py`** | **業務邏輯層** | **統一入口：路徑驗證 + read/write/search/sync（Single Source of Truth）** | **config, core/indexer, core/retriever** |
| `sync` | `tools/sync.py` | 工具層 | LangChain Tool 薄封裝：sync_notes → VaultService.sync() | services/vault_service |
| `search` | `tools/search.py` | 工具層 | LangChain Tool 薄封裝：search_notes → VaultService.search_formatted() | services/vault_service |
| `read` | `tools/read.py` | 工具層 | LangChain Tool 薄封裝：read_note → VaultService.read_note() | services/vault_service |
| `write` | `tools/write.py` | 工具層 | LangChain Tool 薄封裝：write_note → VaultService.write_note() | services/vault_service |
| `base` | `agents/base.py` | Agent 層 | BaseAgent ABC 介面 | abc |
| `memory_agent` | `agents/memory_agent.py` | Agent 層 | 預設記憶 Agent（4 工具 + ChatHistory + Core Memory 注入） | langchain, tools/* |
| `router` | `agents/router.py` | Agent 層 | @mention 關鍵字路由器 | agents/* |
| `app` | `api/app.py` | 接入介面層 | FastAPI REST v2.2（/health, /sync, /search, /read, /write, /webhook/line）→ VaultService + LineChannel | fastapi, services/vault_service, api/channels |
| `schemas` | `api/schemas.py` | 接入介面層 | Pydantic Request / Response 模型 | pydantic |
| **`chat_service`** | **`api/chat_service.py`** | **接入介面層** | **平台無關對話服務（per-user 歷史 + multi-round 工具呼叫 + markdown 清除）** | **agents/memory_agent, tools/\*** |
| **`base_channel`** | **`api/channels/base.py`** | **接入介面層** | **BaseChannel ABC（platform-agnostic）** | **abc** |
| **`line_channel`** | **`api/channels/line.py`** | **接入介面層** | **LINE 驗簽（HMAC-SHA256）+ 訊息解析 + Reply/Push API** | **httpx, api/channels/base** |
| `mcp_server` | `mcp_server.py` | 接入介面層 | MCP Server v2.1（FastMCP SDK，4 tools）→ VaultService | mcp[cli], services/vault_service |
| `repl` | `cli/repl.py` | 接入介面層 | 互動終端（串流輸出 + 工具呼叫 + 自動存檔） | agents/router |
| `main` | `main.py` | 入口 | 模式分發（--mode cli \| api \| mcp） | all |

---

## 2. 資料流

### 2.1 v2.2 架構總覽（Messaging Gateway 加入）

```
main.py --mode=
  ├── cli  → MemoryAgent → LangChain @tool → ┐
  ├── api  → FastAPI endpoints (含 /webhook/line) →├── VaultService → core/*
  └── mcp  → FastMCP @mcp.tool() →────────────────┘

/webhook/line 资料流詳細：
  LINE 平台 → ngrok tunnel → POST /webhook/line
    └→ LineChannel.verify_request() [HMAC-SHA256]
    └→ LineChannel.parse_messages()
    └→ ChatService.handle_message()
          └→ MemoryAgent._run_agent_turn() [ainvoke]
                └→ tools/* → VaultService
    └→ LineChannel.send_reply()
```

### 2.2 寫入流（write_note）

```
使用者輸入 file_path + content
        ↓
任意接入層（tools/write | api/write | mcp/write_note）
        ↓
VaultService.write_note()
  ├── _validate_write_path()  →  路徑防護 + .md 驗證
  ├── os.write()  →  寫入 .md 至 Vault
  └── VaultIndexer.sync_single()  →  單檔增量索引至 ChromaDB
        ↓
回傳：(stats_dict, error)
  stats_dict = {file_path, chars, total_chunks, added, updated}
```

### 2.3 搜尋流（search_vault）

```
使用者 query + 可選 category / doc_type
        ↓
任意接入層 → VaultService.search() / search_formatted()
        ↓
core/retriever.search_formatted()
        ↓
Hybrid Search：BM25 40% + Vector 60%
        ↓
Recency Bias 重排序（指數衰減 T½=90天）
        ↓
Source-level dedup  →  格式化輸出
```

### 2.4 CLI Agent 流

```
User Input → cli/repl.py
                ↓
        agents/router.py → 識別 @mention 或使用預設
                ↓
        agents/memory_agent.py
        ├── System Prompt = Core Memory + 工具說明
        ├── ChatHistory（最近 10 輪）
        └── LangChain Agent Executor
                ↓
        tools（sync / search / read / write）
                ↓
        VaultService → core/（indexer / retriever / ...）
                ↓
        ChromaDB + Vault .md 檔案
```

---

## 3. 關鍵設計決策（ADR）

### ADR-001：多語言 Embedding 選型

**決策**：使用 `paraphrase-multilingual-MiniLM-L12-v2`  
**理由**：50+ 語言支援（含繁中），384 維度，在記憶體與精準度間取得平衡  
**替代方案**：`all-MiniLM-L6-v2`（純英文，速度較快但不支援繁中語意）  
**狀態**：已接受 ✅

### ADR-002：Hybrid Search（BM25 + Vector）

**決策**：BM25 40% + Vector 60%，EnsembleRetriever，Source-level dedup  
**理由**：純向量搜尋對精確關鍵字（如函式名、API 端點）效果差；BM25 補足精確匹配  
**設定**：`USE_HYBRID_SEARCH=True`，`HYBRID_BM25_WEIGHT=0.4`  
**狀態**：已接受 ✅

### ADR-003：不索引原始程式碼（.py / .cs / .lua）

**決策**：Vault 定位為知識/決策層，程式碼理解由 VS Code Copilot 負責  
**替代方案**：索引 .py 檔案（會大幅增加 chunks 並降低 Markdown 文件的搜尋排名）  
**補償**：以手工 `architecture.md` / `module-catalog.md` / `docs/API_MAP.md` 摘要替代  
**狀態**：已接受 ✅

### ADR-004：MCP Server 用官方 FastMCP SDK

**決策**：`mcp[cli]>=1.0.0`，`@mcp.tool()` 裝飾器  
**理由**：官方 SDK 維護穩定，與 VS Code Copilot 原生相容；自製 JSON-RPC 維護成本高  
**狀態**：已接受 ✅，上線（.vscode/mcp.json）

### ADR-005：抽離 VaultService 業務邏輯層

**決策**：建立 `services/vault_service.py` 作為唯一業務邏輯入口（Single Source of Truth）  
**理由**：  
- v2.0 時路徑驗證在 4 個模組中重複實作（tools/read, tools/write, mcp_server, api/app）  
- MCP 缺少 .md 副檔名檢查，CLI write 缺少自動索引，API 缺少 read/write 端點  
- 三條接入路徑（CLI/API/MCP）的回傳格式不一致  
**影響**：tools/、api/、mcp_server 全部改為薄封裝，委派至 VaultService；安全規則集中管理  
**狀態**：已接受 ✅，v2.1 實作完成

---

## 4. 安全設計

| 類型 | 實作 |
|------|------|
| 路徑穿越防護 | `VaultService._validate_path()` — `os.path.realpath()` 比對 VAULT_ROOT（唯一實作點） |
| 只允許 .md 寫入 | `VaultService._validate_write_path()` — 驗證 `.md` 副檔名 |
| API Key 保護 | `.env` 管理，不 commit，支援 429 自動提示 |
| stdout 污染防護 | MCP Server 工具執行期間用 `_StdoutToStderr` 導向 |

---

## 5. 效能特性

| 指標 | 值 |
|------|-----|
| 向量維度 | 384 |
| 索引文件數（2026.03.29） | ~35 files |
| 向量 Chunks 數 | ~500 chunks |
| 典型搜尋延遲（本地 Ollama） | < 2s |
| 典型搜尋延遲（Gemini API） | < 1s |
| 增量同步（無變動） | < 0.5s |
