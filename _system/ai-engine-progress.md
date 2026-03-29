# AI Memory Vault - 專案進度與架構 (v2.2)

> ⚠️ 每次新對話開始、有進度更新、或架構變更後，必須同步更新此檔案與 Copilot Repo Memory（`/memories/repo/ai-memory-vault-progress.md`）。
> ⚠️ 當 AI-Memory-Vault 路徑下的檔案有必要更新時（如 `_system/AGENTS.md`、`templates/agents/*.md`、`work/LIFEOFDEVELOPMENT/projects/AIMemoryVault/project-overview.md` 等），必須同步一起更新，確保 Vault 內各檔案資訊一致。反之亦然。

---

## Vault 結構
```
D:\AI-Memory-Vault\
├── _AI_Engine/                → Python RAG 引擎 v2.1（14 模組，含 services/）
│   ├── config.py              → 全域設定（Pydantic BaseSettings，從 .env 載入）
│   ├── main.py                → 入口（--mode cli | api | mcp）
│   ├── requirements.txt       → 依賴清單
│   ├── .env                   → API Key + LLM_PROVIDER 設定
│   ├── .venv/                 → Python 3.12.9 虛擬環境
│   ├── docs/
│   │   └── API_MAP.md         → 模組公開 API 速查手冊（Rule 03）
│   ├── services/              ← ⭐ v2.1 新增：業務邏輯統一入口
│   │   └── vault_service.py   → 路徑驗證 + read/write/search/sync（Single Source of Truth）
│   ├── core/                  → 核心引擎層
│   │   ├── embeddings.py      → 多語言向量模型（multilingual-MiniLM-L12-v2）
│   │   ├── llm_factory.py     → LLM 工廠（Ollama / Gemini 可插拔）
│   │   ├── vectorstore.py     → ChromaDB + RecordManager
│   │   ├── indexer.py         → 掃描 → Frontmatter 解析 → 切塊 → 增量同步
│   │   └── retriever.py       → Hybrid Search + Recency Bias（EnsembleRetriever from langchain_classic）
│   ├── tools/                 → LangChain Tool 薄封裝（全部委派 VaultService）
│   │   ├── sync.py, search.py, read.py, write.py
│   ├── agents/                → Agent 抽象層
│   │   ├── base.py            → ABC 介面
│   │   ├── memory_agent.py    → 預設記憶 Agent（4 工具 + Core Memory 注入）
│   │   └── router.py          → 意圖路由器
│   ├── api/                   → FastAPI REST API v2.1
│   │   ├── app.py             → /health, /sync, /search, /read, /write 端點
│   │   └── schemas.py         → Pydantic Request/Response（含 Read/Write 模型）
│   ├── mcp_server.py          → MCP Server v2.1（FastMCP SDK，4 tools → VaultService）
│   └── cli/
│       └── repl.py            → 互動終端（串流 + 工具呼叫）
├── .github/prompts/           → VS Code Prompt 入口（10 個 .prompt.md，/斜線指令）
├── _system/                   → Vault 導航
├── templates/agents/          → Copilot Agent 模板（10 個 .md，唯一真相來源）
├── work/                      → 工作域
├── life/                      → 生活域
└── knowledge/                 → 永久知識庫
```

---

## 核心設計決策
- **VaultService 業務邏輯層**（v2.1）：抽離所有路徑驗證 + CRUD 至 `services/vault_service.py`（Single Source of Truth）
- **模組化架構**：14 個模組，單一職責（v2.0 為 13 模組）
- **多語言 Embedding**：`paraphrase-multilingual-MiniLM-L12-v2`（50+ 語言，384 維）
- **Frontmatter 解析**：YAML 自動解析，type/domain/workspace/severity/tags 寫入 metadata
- **Hybrid Search**：BM25 40% + Vector 60%，EnsembleRetriever（`langchain_classic.retrievers.ensemble`），Source-level dedup
- **Agent ABC 介面**：可插拔式 Agent 設計（BaseAgent → MemoryAgent）
- **三模式入口**：`python main.py`（CLI）/ `--mode api`（FastAPI）/ `--mode mcp`（MCP Server）
- **安全集中**：路徑穿越防護 + .md 限制，統一在 VaultService，不再各自重複

---

## 第一階段 ✅ (2026.03.28)
（略，見 v2.0 記錄）

## 第二階段 ✅ v2.0 架構重建 (2026.03.28)
（略，見 v2.0 記錄）

## 第三階段 ✅ 大腦強化 (2026.03.28)
（略，見 v2.0 記錄）

## 第四階段（進行中）

### v2.0 完成項目 (2026.03.29)
- [x] MCP Server 官方 FastMCP SDK（`mcp[cli]>=1.0.0`，4 tools，VS Code 接入）
- [x] VS Code Prompt 入口（10 個 `/斜線指令`）
- [x] Vault 知識庫架構整理（templates/projects/、LIFEOFDEVELOPMENT/rules/、AIMemoryVault 文件補齊）
- [x] Vault 全域模板系統（templates/sections/ 9 個區域模板、AGENTS.md v3 §4 全域規則）

### v2.1 完成項目 (2026.03.29) ⭐
- [x] **VaultService 重構**：新增 `services/vault_service.py`，統一業務邏輯入口
  - tools/、api/、mcp_server 全部改為委派至 VaultService
  - 路徑驗證、.md 限制統一集中管理
- [x] **API v2.1**：FastAPI 新增 `POST /read`、`POST /write` 端點（含 schemas）
- [x] **MCP v2.1**：mcp_server.py 改用 VaultService，移除直接 core/ 依賴
- [x] **Bug 修正**：`core/retriever.py` EnsembleRetriever 改從 `langchain_classic.retrievers.ensemble` 匯入
- [x] **Rule 03**：新增 `LIFEOFDEVELOPMENT/rules/03-project-api-map-sync.md`
  - 規定程式專案建立 Vault 知識結構時，同步在原始碼 `docs/API_MAP.md` 建立 API 速查手冊
  - 首次套用：建立 `_AI_Engine/docs/API_MAP.md`
- [x] **Vault 文件同步**：architecture.md / module-catalog.md / dev-progress.md / AGENTS.md v3.1 全部更新至 v2.1
- [x] LINE Bot 部署（串接 FastAPI）→ **v2.2 完成**
- [ ] 雲端部署（多裝置共享）

### v2.2 完成項目 (2026.03.29) — Messaging Gateway ⭐
- [x] **Messaging Gateway 架構**：新增 `api/channels/` 層，平台無關接入設計
  - `api/channels/base.py`：BaseChannel ABC（verify_request / parse_messages / send_reply）
  - `api/channels/line.py`：LineChannel 實作（HMAC-SHA256 驗簽 + Reply/Push API）
  - `api/channels/__init__.py`
- [x] **ChatService** (`api/chat_service.py`)：平台無關對話邏輯，含 per-user 對話歷史
  - `_strip_markdown()`：移除 Markdown 語法，確保 LINE 純文字顯示
  - `_TOOL_LEAK_KEYWORDS`：偵測並過濾工具名稱洩漏
  - `MAX_TOOL_ROUNDS=10`：多輪工具呼叫上限
  - `async def _run_agent_turn`：全面改為 `ainvoke`，避免阻塞 asyncio event loop
  - 正確錯誤 logging（`logger.error` + `exc_info=True`）
- [x] **FastAPI v2.2**：新增 `POST /webhook/line`（HMAC 驗簽 + 訊息處理 + 回覆）
- [x] **System prompt 強化**（memory_agent.py）：A-G + 1-10 規則集
  - 禁止向使用者詢問工具參數、禁止自言自語/結構標籤、繁體中文強制、禁 Markdown
- [x] **stop.ps1**：一鍵停止 port 8000/8001 的 Python 程序
- [x] **ngrok 3.37.3** 更新（舊 3.3.1 不支援現行 authtoken 格式）
- [x] **LLM 切換**：llm_factory.py 修正 Gemini 初始化（移除 `stream=False`，明確傳入 `google_api_key`）
- [x] **PORT 衝突修正**：系統 Python（無 venv）佔用 port 8000 問題，統一改用 venv python + `main.py --mode api`
- [ ] 雲端部署（多裝置共享）

---

## 同步規則
此檔案與 Copilot Repo Memory（`/memories/repo/ai-memory-vault-progress.md`）為**同一份資料的雙向鏡像**，任一方更新時必須同步對方。

## 願景
寫一次 API，所有 AI 工具都能無縫接入記憶庫，不受工具綁定。
