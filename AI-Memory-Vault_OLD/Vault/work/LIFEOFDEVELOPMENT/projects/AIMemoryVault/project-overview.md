---
type: project
workspace: LIFEOFDEVELOPMENT
domain: ai-infrastructure
status: phase4-in-progress
created: 2026.03.28
last_updated: 2026.03.29
ai_summary: "AI 第二大腦：個人知識中樞，RAG + MCP + Agent 架構，讓任何 AI 工具無縫接入記憶庫"
---

# AI Memory Vault — 專案總覽

> **公司**：LIFEOFDEVELOPMENT  
> **作者**：gabrielchen  
> **版本**：v2.2（Messaging Gateway）  
> **最後更新**：2026.03.29

---

## 🎯 專案願景

建立一個具備「長期記憶」與「主動執行能力」的個人知識中樞。  
**寫一次 API，讓任何 AI 工具（Copilot、ChatGPT、Claude、Cursor…）都能無縫接入記憶庫，不受工具綁定。**

---

## 🏗️ 核心架構：四層過濾模型

### 1. 資料採集層 (Data Source Layer)
- **Obsidian Vault**：核心知識庫（work / life / knowledge 分層）
- **外部輸入**：透過 write_note 工具手動寫入

### 2. 記憶加工層 (Memory & Indexing Layer)
- **多語言向量模型**：`paraphrase-multilingual-MiniLM-L12-v2`（50+ 語言，384 維）
- **增量同步**：`SQLRecordManager` + `blake2b` Hash，只計算有變動的檔案
- **Markdown 切塊**：依 `#`/`##`/`###` 標題分段（MarkdownHeaderTextSplitter）
- **Frontmatter 解析**：YAML 自動解析，type/domain/workspace/severity/tags 注入 metadata
- **向量資料庫**：ChromaDB 儲存語意座標
- **Hybrid Search**：BM25 40% + Vector 60%（EnsembleRetriever），Source-level dedup

### 3. 邏輯大腦層 (Agent & Logic Layer)
- **BaseAgent ABC**：可插拔介面，所有 Agent 繼承
- **AgentRouter**：@mention 關鍵字路由
- **MemoryAgent**：預設記憶 Agent，4 工具（sync/search/read/write）
- **對話上下文**：ChatHistory（MAX_HISTORY_TURNS=10）
- **Recency Bias**：指數衰減重排序（T½=90天）
- **Core Memory**：`_system/core-memory.md` 啟動時自動注入 System Prompt

### 4. 接入介面層 (Interface Layer)
| 介面 | 狀態 | 說明 |
|------|------|------|
| CLI | ✅ 已上線 | `python main.py`，互動終端，串流輸出 |
| FastAPI REST | ✅ 已上線 | `python main.py --mode api`，6 端點（含 /webhook/line）|
| MCP Server | ✅ 已上線 | `python main.py --mode mcp`，VS Code Copilot 原生接入 |
| VS Code Prompts | ✅ 已上線 | 10 個 `/斜線指令`，動態載入 Agent 模板 |
| LINE Bot | ✅ 已上線 | Webhook 驗證通過，llama3.1:8b 回應（Gemini key 待更換）|
| Telegram Bot | 🔲 規劃中 | 串接 Messaging Gateway |
| 雲端部署 | 🔲 規劃中 | 多裝置共享 |

---

## 📁 模組架構

```
_AI_Engine/ (v2.2)
├── config.py              → 全域設定（Pydantic BaseSettings，.env 載入）
├── main.py                → 入口（--mode cli | api | mcp）
├── mcp_server.py          → MCP Server（FastMCP SDK，4 tools）
├── stop.ps1               → 一鍵停止 port 8000/8001
├── auto_sync.ps1          → Windows 排程腳本（每日 20:00 自動同步）
├── requirements.txt       → 依賴清單
├── .env                   → API Key + LLM_PROVIDER
├── .venv/                 → Python 3.12.9 虛擬環境
├── core/
│   ├── embeddings.py      → 多語言向量模型
│   ├── llm_factory.py     → LLM 工廠（Ollama / Gemini 可插拔）
│   ├── vectorstore.py     → ChromaDB + RecordManager
│   ├── indexer.py         → 掃描 → Frontmatter 解析 → 切塊 → 增量同步
│   └── retriever.py       → Hybrid Search + 多維度 Metadata 過濾
├── tools/                 → LangChain Tool 薄封裝
│   ├── sync.py            → sync_notes
│   ├── search.py          → search_notes
│   ├── read.py            → read_note
│   └── write.py           → write_note
├── agents/
│   ├── base.py            → ABC 介面
│   ├── memory_agent.py    → 預設記憶 Agent
│   └── router.py          → 意圖路由器
├── api/
│   ├── app.py             → FastAPI v2.2（/health, /sync, /search, /read, /write, /webhook/line）
│   ├── schemas.py         → Pydantic Request/Response
│   ├── chat_service.py    → 平台無關對話服務（per-user 歷史 + 工具呼叫 + markdown 清除）
│   └── channels/
│       ├── base.py        → BaseChannel ABC（platform-agnostic）
│       └── line.py        → LineChannel（HMAC-SHA256 驗簽 + Reply/Push API）
└── cli/
    └── repl.py            → 互動終端（串流 + 工具呼叫 + 自動存檔）
```

---

## 🗺️ 執行進度 (Roadmap)

### 第一階段 ✅ 已完成 (2026.03.28)
- [x] Gemini API 連線（gemini-2.0-flash-lite）+ Ollama 本地切換
- [x] 增量同步（SQLRecordManager + ChromaDB）
- [x] Markdown 按標題切塊（MarkdownHeaderTextSplitter）
- [x] 分類標籤自動識別（work/life/knowledge/templates/_system）
- [x] 對話上下文（ChatHistory，MAX_HISTORY_TURNS=10）
- [x] 安全 .env（API Key + 429 提示 + Ctrl+C 退出）
- [x] 串流輸出（逐字印出）
- [x] 啟動自動同步 + `sync` 內建指令

### 第二階段 ✅ v2.0 架構重建 (2026.03.28)
- [x] 多語言 Embedding（all-MiniLM-L6-v2 → multilingual-MiniLM-L12-v2）
- [x] Frontmatter YAML 解析 → metadata 注入
- [x] 模組化重構（單檔 400 行 → 13 模組）
- [x] Agent ABC 介面 + AgentRouter + MemoryAgent
- [x] FastAPI REST API（/health, /sync, /search）
- [x] blake2b Hash 取代 SHA-1
- [x] 向量庫完整重建（379 chunks，28 files，0 未分類）

### 第三階段 ✅ 大腦強化 (2026.03.28)
- [x] Session 自動存檔（`save` + `q` / Ctrl+C，存至 `.ai_memory/logs/`）
- [x] Hybrid Search（BM25 40% + Vector 60%，EnsembleRetriever，Source-level dedup）
- [x] 自動化排程（`auto_sync.ps1`，`-RegisterSchedule` 每日 20:00）
- [x] 記憶分層（Recency Bias T½=90天 + Core Memory 注入 System Prompt）
- [~~] 專案索引（跳過：改以手工 api-map.md / project-overview.md 摘要替代）

### 第四階段 ✅ 通用化接入 (2026.03.29)
- [x] MCP Server Pure JSON-RPC 實作（Python 3.9+ 相容）
- [x] Python 3.12.9 安裝 + `.venv` 重建
- [x] **MCP Server 升級為官方 FastMCP SDK**（`mcp[cli]>=1.0.0`）
- [x] **VS Code Prompt 入口**（10 個 `/斜線指令`）
- [x] VaultService 重構（services/vault_service.py，Single Source of Truth）

### 第五階段 ✅ Messaging Gateway (2026.03.29 晚)
- [x] **Messaging Gateway v2.2** — 平台無關 Channel 架構
  - `api/channels/base.py`：BaseChannel ABC
  - `api/channels/line.py`：LINE HMAC-SHA256 驗簽 + Reply/Push API
  - `api/chat_service.py`：per-user 對話歷史、工具呼叫、markdown 清除
  - `api/app.py v2.2`：新增 `POST /webhook/line`
- [x] LINE Bot Webhook 端到端驗證 ✅
- [x] System prompt 強化（繁中強制、禁 Markdown、禁自言自語）
- [x] stop.ps1、ngrok 3.37.3、PORT 衝突修正
- [ ] **Gemini API key 更換**（免費配額耗盡，新 project key）← 待處理
- [ ] Telegram Bot（Messaging Gateway 擴充）
- [ ] 雲端部署（向量庫上雲，多裝置共享）

---

## 🛠️ 常用指令

```powershell
# 啟動 CLI 模式
cd D:\AI-Memory-Vault\_AI_Engine
python main.py

# 啟動 API 模式
python main.py --mode api        # http://127.0.0.1:8000

# 啟動 MCP Server（VS Code 自動呼叫）
python main.py --mode mcp

# 安裝每日自動同步排程
.\auto_sync.ps1 -RegisterSchedule
```

---

## 🔧 核心設計原則
- **介面不綁定工具**：API 優先、MCP 協定標準化
- **增量同步**：只計算有變動的檔案，效能最佳
- **安全第一**：路徑穿越防護、.env 管理 API Key
- **模組化**：單一職責，可插拔 Agent + LLM
