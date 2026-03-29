# AI Memory Vault - 專案進度與架構 (v2.3)

> ⚠️ 每次新對話開始、有進度更新、或架構變更後，必須同步更新此檔案與 Copilot Repo Memory（`/memories/repo/ai-memory-vault-progress.md`）。
> ⚠️ 當 AI-Memory-Vault 路徑下的檔案有必要更新時（如 `_system/AGENTS.md`、`templates/agents/*.md`、`work/LIFEOFDEVELOPMENT/projects/AIMemoryVault/project-overview.md` 等），必須同步一起更新，確保 Vault 內各檔案資訊一致。反之亦然。

---

## Vault 結構
```
D:\AI-Memory-Vault\
├── _AI_Engine/                → Python RAG 引擎 v2.3（15 模組）
│   ├── config.py              → 全域設定（Pydantic BaseSettings，從 .env 載入）
│   ├── main.py                → 入口（--mode cli | api | mcp），三模式皆呼叫 check_mode_prerequisites
│   ├── env_setup.py           → .env 精靈 v1.2 + 模式預檢系統（套件/Ollama/ngrok）
│   ├── requirements.txt       → 依賴清單
│   ├── .env                   → API Key + LLM_PROVIDER 設定
│   ├── .venv/                 → Python 3.12.9 虛擬環境
│   ├── .req_hash              → requirements.txt MD5 快取（變動偵測用）
│   ├── docs/
│   │   └── API_MAP.md         → 模組公開 API 速查手冊（Rule 03）
│   ├── services/              ← ⭐ v2.1 新增：業務邏輯統一入口
│   │   └── vault_service.py   → 路徑驗證 + read/write/search/sync（Single Source of Truth）
│   ├── core/                  → 核心引擎層
│   │   ├── embeddings.py      → 多語言向量模型（multilingual-MiniLM-L12-v2）
│   │   ├── llm_factory.py     → LLM 工廠（Ollama / Gemini 可插拔）
│   │   ├── vectorstore.py     → ChromaDB + RecordManager
│   │   ├── indexer.py         → 掃描 → Frontmatter 解析 → 切塊 → 增量同步
│   │   └── retriever.py       → Hybrid Search + Recency Bias
│   ├── tools/                 → LangChain Tool 薄封裝（全部委派 VaultService）
│   │   ├── sync.py, search.py, read.py, write.py
│   ├── agents/                → Agent 抽象層
│   │   ├── base.py            → ABC 介面
│   │   ├── memory_agent.py    → 預設記憶 Agent（4 工具 + Core Memory 注入）
│   │   └── router.py          → 意圖路由器
│   ├── api/                   → FastAPI REST API v2.2
│   │   ├── app.py             → /health, /sync, /search, /read, /write, /webhook/line
│   │   ├── schemas.py         → Pydantic Request/Response
│   │   ├── chat_service.py    → 平台無關對話邏輯（per-user 歷史 + async ainvoke）
│   │   └── channels/          → Messaging Gateway 層
│   │       ├── base.py        → BaseChannel ABC
│   │       └── line.py        → LineChannel（HMAC-SHA256 + Reply/Push API）
│   ├── mcp_server.py          → MCP Server v2.1（FastMCP SDK，4 tools）
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
- **模式預檢系統**（v2.3）：`check_mode_prerequisites()` 在三模式啟動時自動檢查套件/Ollama/ngrok
- **ngrok 自動啟動**（v2.3）：API 模式啟動時若 authtoken 已設定，自動背景啟動 ngrok 並印出 Public URL
- **VaultService 業務邏輯層**（v2.1）：統一路徑驗證 + CRUD（Single Source of Truth）
- **模組化架構**：15 個模組，單一職責
- **多語言 Embedding**：`paraphrase-multilingual-MiniLM-L12-v2`（50+ 語言，384 維）
- **Hybrid Search**：BM25 40% + Vector 60%，EnsembleRetriever，Source-level dedup
- **三模式入口**：`python main.py`（CLI）/ `--mode api`（FastAPI）/ `--mode mcp`（MCP Server）
- **安全集中**：路徑穿越防護 + .md 限制，統一在 VaultService

---

## 第一 ~ 第三階段 ✅
（見 dev-progress.md 詳細記錄）

## 第四階段（進行中）

### v2.0 ~ v2.2 完成項目（2026.03.29）
（見 dev-progress.md 詳細記錄）

### v2.3 完成項目 (2026.03.30) — 啟動穩定化 + 預檢系統 ⭐
- [x] **ngrok 自動啟動**：`_launch_ngrok()` 新增 — 查詢 localhost:4040，無則 Popen 背景啟動，輪詢等待 Public URL
- [x] **模式預檢系統 v1.2**（`env_setup.py`）：
  - `_BASE_PACKAGES`、`_LLM_PACKAGES`、`_MODE_EXTRA_PACKAGES` 常數定義
  - `check_mode_prerequisites(iMode, iPort)` —— 統一入口，依模式組合檢查套件清單
  - `_check_packages()` —— `importlib.util.find_spec` 逐一確認，缺少者詢問是否自動 `pip install`
  - `_check_ollama_service()` —— 連線測試 `/api/tags`，失敗顯示安裝/啟動說明
- [x] **main.py 三模式全面接入**：cli / api / mcp 皆呼叫 `check_mode_prerequisites()`
- [x] **port 衝突根因確認**：系統 Python（非 venv）定期干擾；確立使用 `venv/python main.py` 的標準做法
- [ ] Gemini API key 更換（新 project）
- [ ] Telegram Channel
- [ ] 雲端部署

---

## 同步規則
此檔案與 Copilot Repo Memory（`/memories/repo/ai-memory-vault-progress.md`）為**同一份資料的雙向鏡像**，任一方更新時必須同步對方。

## 願景
寫一次 API，所有 AI 工具都能無縫接入記憶庫，不受工具綁定。
