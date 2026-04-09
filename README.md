# AI Memory Vault

> 一個由 AI 驅動的個人知識管理系統，結合 RAG 技術實現智慧搜尋與記憶。  
> 透過 **MCP（Model Context Protocol）** 讓 VS Code Copilot / Claude Desktop / Cursor 直接操作你的 Vault。

---

## 快速開始（開發者）

```powershell
cd AI_Engine
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py --setup        # 首次初始化精靈
python main.py --mode cli     # 啟動 CLI
```

## 快速開始（一般使用者）

從 [Releases](../../releases) 下載 `AI-Memory-Vault-Setup-vX.Y.Z.exe`，執行後：

1. 依安裝精靈設定 Vault 路徑 / 組織 / API Key
2. 桌面點擊 **AI Memory Vault CLI** 捷徑啟動 CLI
3. 在 VS Code 設定 MCP Server 指向 `dist/vault-ai/vault-mcp.exe`

---

## 專案結構

```
AI-Memory-Vault/
├── AI_Engine/              → Python RAG 引擎（v3）
│   ├── core/               → 核心模組（embeddings / vectorstore / indexer / retriever / migration）
│   ├── services/           → 業務邏輯（vault / setup / scheduler / git_service / token_counter）
│   ├── mcp_app/            → MCP Server（FastMCP stdio，24 個工具）
│   ├── cli/                → 互動式 CLI（REPL + 選單模式）
│   ├── tools/              → 工具登記表（TOOL_REGISTRY，CLI↔MCP 自動橋接）
│   ├── packaging/          → 打包腳本（build.spec / build.ps1 / installer.iss）
│   │   └── shortcuts/      → 安裝捷徑 .bat（環境設定 / 排程管理）
│   ├── scripts/            → 開發者腳本（auto_tasks / scheduler-menu / setup-menu）
│   ├── tests/              → 單元測試（212/212 PASS）
│   ├── config.py           → 設定管理（config.json + .env；frozen/dev 路徑自動分離）
│   ├── main.py             → 入口點（--setup / --mode cli|mcp|scheduler / --reindex）
│   ├── requirements.txt    → Python 依賴
│   └── .env.example        → 環境變數範本（API Keys）
│
└── Vault/                  → 知識庫內容（v3 結構）
    ├── _config/            → AI Session 系統設定（nav / handoff / agents）
    ├── workspaces/         → 工作空間（依組織分）
    │   └── _global/        → 跨工作空間共用（rules / snippets / tech-notes）
    ├── personal/           → 個人空間（journal / reviews / goals / ideas）
    ├── knowledge/          → 永久知識卡片
    ├── templates/          → 建立新內容的模板
    └── attachments/        → 圖片 / PDF 等附件
```

---

## Phase 1：環境建置與 MCP 啟用（開發者）

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
- 設定 Vault 路徑（預設 `../Vault`）
- 填入使用者名稱 / 組織
- 選擇 LLM 供應商（Ollama 本地 / Gemini）
- 自動建立 Vault 目錄結構 + 初始化 ChromaDB

> 設定儲存於 `AI_Engine/config.json`；API Key 等敏感資訊放 `.env`（參考 `.env.example`）。

### 3. 啟用 VS Code MCP 整合（開發模式）

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

### 4. 啟用 VS Code MCP 整合（exe 打包版）

```json
{
  "servers": {
    "ai-memory-vault": {
      "command": "C:/AI-Memory-Vault/dist/vault-ai/vault-mcp.exe",
      "args": [],
      "cwd": "C:/AI-Memory-Vault/dist/vault-ai"
    }
  }
}
```

在 VS Code 中按 **Ctrl+Shift+P → MCP: Start Server → ai-memory-vault** 即可啟動。

### 5. 手動啟動 MCP Server（CLI 驗證用）

```powershell
cd AI_Engine
.venv\Scripts\Activate.ps1
python main.py --mode mcp
```

---

## MCP 工具（v3.5，共 24 個）

### 核心工具

| 工具 | 參數 | 說明 |
|------|------|------|
| `search_vault` | `query`, `category?`, `doc_type?`, `mode?` | BM25 + 向量混合搜尋（Recency Bias 排序） |
| `read_note` | `file_path` | 讀取 Vault 中指定 `.md` 的完整內容 |
| `write_note` | `file_path`, `content`, `mode?` | 寫入/覆蓋或追加筆記，並立即索引至 ChromaDB |
| `batch_write_notes` | `notes` | 批次寫入多筆，單次 ChromaDB 索引 |
| `sync_vault` | — | 掃描全部 `.md`，增量更新向量庫 |
| `delete_note` | `file_path` | 刪除筆記並移除 DB 向量 |
| `rename_note` | `old_path`, `new_path` | 移動或重命名 .md，同步向量索引 |
| `list_notes` | `path?`, `recursive?` | 列出目錄下所有 .md（支援遞迴，方便 AI 探索結構） |
| `check_vault_integrity` | — | 找出孤立向量（DB 有但檔案已刪） || `clean_orphans` | — | 只删除孤立向量，比 reindex 更軽量 || `check_index_status` | — | 檢查向量索引是否因設定變更需要重建 |
| `reindex_vault` | — | 清除並從頭重建 ChromaDB 向量索引 |

> `write_note` 的 `mode` 參數：`"overwrite"`（預設，全覆蓋）或 `"append"`（追加到檔尾）。

**`search_vault` 過濾參數：**

| `category` 值 | 對應目錄 |
|---------------|---------|
| `workspaces` | `Vault/workspaces/` |
| `personal` | `Vault/personal/` |
| `knowledge` | `Vault/knowledge/` |
| `templates` | `Vault/templates/` |
| `config` | `Vault/_config/` |

### 排程 / 回顧工具

| 工具 | 參數 | 說明 |
|------|------|------|
| `generate_project_daily` | `organization`, `project`, `date?` | 生成專案每日詳細進度模板 |
| `generate_project_status` | `organization`, `project` | 生成/取得專案 status.md 模板 |
| `get_project_status` | `organization`, `project` | 讀取專案 status.md 結構化待辦 |
| `generate_daily_review` | `date?`, `projects?` | 生成每日總進度表（跨專案摘要） |
| `generate_weekly_review` | `date?` | 生成每週進度整理（自動計算 ISO 週） |
| `generate_monthly_review` | `date?` | 生成每月進度整理模板 |
| `log_ai_conversation` | `organization`, `project`, `session_name`, `content` | 記錄 AI 對話至 `conversations/` |
| `generate_ai_weekly_analysis` | `date?` | 生成 AI 對話週報分析 |
| `generate_ai_monthly_analysis` | `date?` | 生成 AI 對話月報分析 |

### 知識管理工具

| 工具 | 參數 | 說明 |
|------|------|------|
| `list_projects` | — | 列出所有組織與專案清單 |
| `extract_knowledge` | `organization`, `project`, `topic`, `session?` | 從對話萃取知識卡片 |
| `update_todo` | `file_path`, `todo_text`, `done` | 更新 status.md 中的 todo 勾選狀態 |

> `date` 格式為 `YYYY-MM-DD`，預設使用今天。

---

## CLI 指令（vault-cli.exe / python main.py --mode cli）

```
搜尋與檔案操作
  search <query> [--cat C] [--type T] [--mode M]   搜尋記憶庫
  read   <path>                                      讀取筆記
  write  <path>                                      寫入/覆蓋筆記（多行輸入）
  delete <path>                                      刪除筆記
  rename <old_path> <new_path>                       移動或重命名（別名: mv）
  list   [<path>] [-r]                               列出目錄下 .md 檔案（別名: ls）

同步
  sync          增量同步 .md → ChromaDB
  checkindex    檢查向量索引是否需要重建       (別名: ci)
  reindex       清除並重建 ChromaDB 向量索引   (別名: ri)
  clean         清除孤立向量（比 reindex 輕量）   (別名: cl)
  integrity     檢查孤立向量

專案管理
  genstatus <org> <proj>              生成 status.md 模板  (別名: gs)

進度表
  daily   <org> <proj> [<date>]       生成專案每日進度     (別名: da)
  review  [<date>]                    生成每日總進度表     (別名: rv)
  weekly                              生成每週總進度表     (別名: wk)
  monthly                             生成每月總進度表     (別名: mo)

AI 對話
  log      <org> <proj> <session>     記錄 AI 對話        (別名: la)
  aiweekly [<date>]                   生成 AI 對話週報    (別名: aw)
  aimonthly [<date>]                  生成 AI 對話月報    (別名: am)
  extract  <org> <proj> <topic>       萃取知識卡片        (別名: ex)

其他
  status   <org> <proj>               讀取專案狀態        (別名: st)
  todo     <path> <text> [done|undone] 切換 todo 狀態     (別名: t)
  projects                            列出所有組織與專案   (別名: p)
  help / q / exit
```

在 CLI 中輸入 `--menu` 切換為方向鍵選單模式。

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
- 向量庫：ChromaDB（開發模式 → `AI_Engine/chroma_db/`；安裝版 → `%APPDATA%\AI-Memory-Vault\`）
- 增量索引：SQLRecordManager 追蹤已索引檔案
- 索引遷移：`MigrationManager` 偵測 embedding/chunk 設定變更，自動提示 `--reindex`

---

## 設定檔說明（config.json）

```json
{
    "version": "3.0",
    "vault_path": "D:/AI-Memory-Vault/Vault",
    "user": { "name": "yourname", "organizations": ["YourOrg"] },
    "llm": { "provider": "ollama", "ollama_base_url": "http://localhost:11434" },
    "embedding": { "model": "paraphrase-multilingual-MiniLM-L12-v2", "device": "cpu",
                   "chunk_size": 500, "chunk_overlap": 50 },
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

## 進階操作

### 重建向量索引

當更換 embedding 模型或調整 chunk_size 時，需重建索引：

```powershell
# CLI 方式
python main.py --reindex

# 在 CLI/REPL 內
vault> checkindex   # 先確認是否需要重建
vault> reindex      # 互動式確認後重建

# MCP 工具方式（AI 可自動觸發）
check_index_status()   # 確認狀態
reindex_vault()        # 重建
```

### 開發者打包

```powershell
cd AI_Engine/packaging
.\build.ps1             # 僅 PyInstaller
.\build-all.ps1         # PyInstaller + Inno Setup（需已安裝 Inno Setup 6.x）
.\build.ps1 -Clean      # 清除舊 build/ dist/ 後重新打包
```

---

## 已知命名注意事項

本地 `mcp_app/` 目錄（舊名 `mcp/`）因與 pip 套件 `mcp` 同名會產生 import 衝突，已統一改名為 `mcp_app/`。

---

## 開發路線圖

| 階段 | 狀態 | 內容 |
|------|------|------|
| **Phase 1** | ✅ 完成 | RAG 核心 + ChromaDB + MCP Server（21 工具） |
| **Phase 2** | ✅ 完成 | SchedulerService + AutoScheduler + KnowledgeExtractor + TokenCounter |
| **Phase 3** | ✅ 完成 | 打包基建 + 安全加固 + logging + 單元測試（184/184 PASS） |
| **Phase 4** | ✅ 完成 | PyInstaller 打包 → `vault-cli.exe` / `vault-mcp.exe` / `vault-scheduler.exe` |
| **Phase 5** | ✅ 完成 | Inno Setup 安裝精靈 → `AI-Memory-Vault-Setup-vX.Y.Z.exe` |
| **Phase 6** | 📋 計畫中 | Tauri + React GUI → 完整桌面應用程式（搜尋 / 編輯 / 排程 UI） |
