# AI Memory Vault

> 一個由 AI 驅動的個人知識管理系統，結合 RAG 技術實現智慧搜尋與記憶。  
> 透過 **MCP（Model Context Protocol）** 讓 VS Code Copilot / Claude Desktop / Cursor 直接操作你的 Vault。

---

## 專案結構

```
AI-Memory-Vault/
├── AI_Engine/              → Python RAG 引擎（v3）
│   ├── core/               → 核心模組（embeddings / vectorstore / indexer / retriever / llm）
│   ├── services/           → 業務邏輯（vault / setup / scheduler）
│   ├── mcp_app/            → MCP Server（FastMCP stdio）
│   ├── config.py           → 設定管理（config.json + .env）
│   ├── main.py             → 入口點（setup / cli / api / mcp 四模式）
│   ├── requirements.txt    → Python 依賴
│   └── .env.example        → 環境變數範本（API Keys）
│
└── Vault/                  → 知識庫內容（v3 結構）
    ├── .config/            → AI Session 系統設定（nav / handoff / todos）
    ├── workspaces/         → 工作空間（依公司/組織分）
    │   └── _global/        → 跨工作空間共用（snippets / tech-notes）
    ├── personal/           → 個人空間（journal / learning / goals / ai-conversations）
    ├── knowledge/          → 永久知識卡片
    ├── templates/          → 建立新內容的模板
    └── attachments/        → 圖片 / PDF 等附件
```

---

## Phase 1：環境建置與 MCP 啟用

### 1. 建立虛擬環境並安裝依賴

```powershell
cd AI_Engine
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate          # macOS / Linux
pip install -r requirements.txt
```

### 2. 首次初始化（Setup Wizard）

```powershell
python main.py --setup
```

互動式引導會：
- 設定 Vault 路徑（預設 `../vault`）
- 填入使用者名稱 / 組織
- 選擇 LLM 供應商（Ollama 本地 / Gemini）
- 自動建立 Vault 目錄結構 + 初始化 ChromaDB

> 設定儲存於 `AI_Engine/config.json`；API Key 等敏感資訊放 `.env`（參考 `.env.example`）。

### 3. 啟用 VS Code MCP 整合

專案已預設 `.vscode/mcp.json`，直接使用新建的 venv：

```json
{
  "servers": {
    "ai-memory-vault": {
      "command": "${workspaceFolder}/AI_Engine/.venv/Scripts/python.exe",
      "args": ["main.py", "--mode", "mcp"],
      "cwd": "${workspaceFolder}/AI_Engine"
    }
  }
}
```

在 VS Code 中按 **Ctrl+Shift+P → MCP: Start Server → ai-memory-vault** 即可啟動。

> **macOS / Linux**：將 `Scripts/python.exe` 改為 `bin/python`。

### 4. 手動啟動 MCP Server（CLI 驗證用）

```powershell
cd AI_Engine
.venv\Scripts\Activate.ps1
python main.py --mode mcp
```

---

## MCP 工具（Phase 1，共 9 個）

### 核心工具

| 工具 | 參數 | 說明 |
|------|------|------|
| `search_vault` | `query`, `category?`, `doc_type?` | BM25 + 向量混合搜尋（Recency Bias 排序） |
| `read_note` | `file_path` | 讀取 Vault 中指定 `.md` 的完整內容 |
| `write_note` | `file_path`, `content` | 寫入/覆蓋筆記，並立即索引至 ChromaDB |
| `sync_vault` | — | 掃描全部 `.md`，增量更新向量庫 |

**`search_vault` 過濾參數：**

| `category` 值 | 對應目錄 |
|---------------|---------|
| `workspaces` | `Vault/workspaces/` |
| `personal` | `Vault/personal/` |
| `knowledge` | `Vault/knowledge/` |
| `templates` | `Vault/templates/` |
| `config` | `Vault/.config/` |

### 排程 / 回顧工具

| 工具 | 參數 | 說明 |
|------|------|------|
| `generate_daily_review` | `workspace`, `date?` | 生成每日工作整理模板 |
| `generate_weekly_review` | `workspace`, `date?` | 生成每週進度整理（自動計算 ISO 週） |
| `generate_monthly_review` | `workspace`, `date?` | 生成每月進度整理模板 |
| `log_ai_conversation` | `session_name`, `content` | 將 AI 對話摘要記錄至 `personal/ai-conversations/` |
| `generate_ai_analysis` | `date?` | 生成 AI 月度效率分析（自動掃描對話紀錄） |

> `date` 格式為 `YYYY-MM-DD`，預設使用今天。  
> `workspace` 為工作空間名稱，例如 `chinesegamer` 或 `lifeofdevelopment`。

---

## 搜尋架構

```
查詢字串
  │
  ├── BM25（關鍵字，權重 40%）
  │
  └── 向量語意搜尋（權重 60%）
        │
        └── Recency Bias 重排（90 天半衰期）
                │
                └── Top-K 結果回傳
```

- 嵌入模型：`paraphrase-multilingual-MiniLM-L12-v2`（本地，支援中英文）
- 向量庫：ChromaDB（儲存於 `AI_Engine/chroma_db/`）
- 增量索引：SQLRecordManager 追蹤已索引檔案

---

## 設定檔說明（config.json）

```json
{
    "version": "3.0",
    "vault_path": "D:/AI-Memory-Vault/vault",
    "user": { "name": "yourname", "organization": "YourOrg" },
    "llm": { "provider": "ollama", "ollama_base_url": "http://localhost:11434" },
    "embedding": { "model": "paraphrase-multilingual-MiniLM-L12-v2", "device": "cpu" },
    "search": {
        "top_k": 5,
        "use_hybrid": true,
        "bm25_weight": 0.4,
        "vector_weight": 0.6,
        "recency_bias_enabled": true,
        "recency_decay_days": 90
    },
    "database": { "chroma_dir": "chroma_db", "collection_name": "vault_main" }
}
```

敏感資訊（API Key）放 `.env`：

```env
GOOGLE_API_KEY=your_key_here   # Gemini 使用
```

---

## 已知命名注意事項

本地 `mcp_app/` 目錄（舊名 `mcp/`）因與 pip 套件 `mcp` 同名會產生 import 衝突，已統一改名為 `mcp_app/`。

---

## 開發路線圖

| 階段 | 狀態 | 內容 |
|------|------|------|
| **Phase 1** | ✅ 完成 | RAG 核心 + ChromaDB + 9 個 MCP 工具 + SchedulerService |
| **Phase 2** | 🔧 進行中 | LangChain Agent + ChatService + FastAPI + CLI REPL |
| **Phase 3** | 📋 計畫中 | Tauri UI + GitHub Copilot SDK 整合 |
| **Phase 4** | 📋 計畫中 | 打包發布（.msi / .dmg） |

---

## 文件

- [V3 架構設計](AI-Memory-Vault_OLD/docs/VAULT-V3-ARCHITECTURE.md)
- [重構方案](AI-Memory-Vault_OLD/docs/ARCHITECTURE-REFACTOR.md)
