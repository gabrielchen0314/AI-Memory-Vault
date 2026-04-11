# AI Memory Vault

> 一個由 AI 驅動的個人知識管理系統，結合 RAG 技術實現智慧搜尋與記憶。
> 透過 **MCP（Model Context Protocol）** 讓 VS Code Copilot / Claude Desktop / Cursor 直接操作你的 Vault。

**v3.7.0** — 40 個 MCP 工具 · 247 個測試 · 三種部署模式 · AI 自主學習管道

---

## 目錄

- [三種部署模式](#三種部署模式)
- [模式一：開發模式（Python venv）](#模式一開發模式python-venv)
- [模式二：安裝包模式（exe）](#模式二安裝包模式exe)
- [模式三：Docker 容器模式](#模式三docker-容器模式)
- [專案結構](#專案結構)
- [MCP 工具一覽（40 個）](#mcp-工具一覽40-個)
- [CLI 指令](#cli-指令)
- [搜尋架構](#搜尋架構)
- [設定檔說明](#設定檔說明configjson)
- [開發流程：修改程式後的更新步驟](#開發流程修改程式後的更新步驟)
- [進階操作](#進階操作)
- [開發路線圖](#開發路線圖)

---

## 三種部署模式

| 模式 | 適用對象 | Transport | 需要安裝 |
|------|---------|-----------|---------|
| **開發模式** | 開發者 | stdio（本機 VS Code 直連） | Python 3.10+ / venv |
| **安裝包模式** | 一般使用者 | stdio（本機 exe） | 無（Installer 一鍵安裝） |
| **Docker 模式** | 伺服器 / 遠端部署 | SSE（HTTP 長連線，port 8765） | Docker / Docker Compose |

三種模式功能完全相同（40 個 MCP 工具），差別只在部署方式與連線協定。

---

## 模式一：開發模式（Python venv）

> 適合開發者日常使用，直接用 Python 執行，修改程式碼後立即生效。

### 1. 建立環境

```powershell
cd AI_Engine
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate          # macOS / Linux
pip install -r requirements.txt
```

### 2. 首次初始化

```powershell
python main.py --setup
```

互動式引導會設定：
- Vault 路徑（預設 `../Vault`）
- 使用者名稱 / 組織
- LLM 供應商（Ollama 本地 / Gemini）
- 自動建立 Vault 目錄結構 + 初始化 ChromaDB

> 設定儲存於 `AI_Engine/config.json`；API Key 放 `.env`（參考 `.env.example`）。

### 3. 設定 VS Code MCP

專案已預設 `.vscode/mcp.json`：

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

在 VS Code 按 **Ctrl+Shift+P → MCP: Start Server → ai-memory-vault** 即可啟動。

### 4. 其他啟動方式

```powershell
python main.py --mode cli        # 互動式 CLI
python main.py --mode mcp        # MCP stdio Server
python main.py --mode api        # MCP SSE Server（HTTP port 8765）
python main.py --scheduler       # APScheduler 守護（背景排程）
python main.py --once             # 一次性排程（Windows 工作排程器整合）
python main.py --reindex          # 重建向量索引
python main.py --setup-section org  # 僅設定組織
```

---

## 模式二：安裝包模式（exe）

> 適合沒有 Python 環境的使用者，下載安裝包即可使用。

### 1. 安裝

從 [Releases](../../releases) 下載 `AI-Memory-Vault-Setup-v3.7.0.exe`，執行安裝精靈。

### 2. 首次設定

桌面點擊 **AI Memory Vault CLI** → 自動觸發 Setup Wizard。

### 3. 設定 VS Code MCP

**安裝包安裝後**（預設安裝路徑）：

```json
{
  "servers": {
    "ai-memory-vault": {
      "type": "stdio",
      "command": "C:/Program Files/AI Memory Vault/vault-mcp.exe",
      "args": [],
      "cwd": "C:/Program Files/AI Memory Vault"
    }
  }
}
```

> ⚠️ 若安裝時更改了目錄，請將路徑改為實際安裝位置。
>
> **不需要安裝，直接使用打包後的 exe（dist 模式）**：
>
> ```json
> {
>   "servers": {
>     "ai-memory-vault": {
>       "type": "stdio",
>       "command": "D:/AI-Memory-Vault/AI_Engine/dist/vault-ai/vault-mcp.exe",
>       "args": [],
>       "cwd": "D:/AI-Memory-Vault/AI_Engine/dist/vault-ai"
>     }
>   }
> }
> ```

### 4. 產出的執行檔

| 執行檔 | 用途 |
|--------|------|
| `vault-cli.exe` | 互動式 CLI（雙擊啟動） |
| `vault-mcp.exe` | MCP stdio Server（VS Code / Claude Desktop 設定用） |
| `vault-scheduler.exe` | APScheduler 排程守護 |

---

## 模式三：Docker 容器模式

> 適合將 Vault 部署到 NAS / 雲端 VPS，本機透過 SSE 遠端連線。

### 1. 建置與啟動

```bash
# 啟動全部服務（MCP SSE + Scheduler）
docker compose up -d

# 僅啟動 MCP SSE Server
docker compose up -d mcp-sse

# 查看即時日誌
docker compose logs -f
```

### 2. 服務架構

| 容器 | 模式 | Port | 說明 |
|------|------|------|------|
| `vault-mcp-sse` | `--mode api` | 8765 | MCP SSE Server（HTTP 長連線） |
| `vault-scheduler` | `--scheduler` | — | APScheduler 排程守護（自動日報/週報/備份） |

### 3. Volume 掛載

| Volume | 容器路徑 | 說明 |
|--------|---------|------|
| `vault-data` | `/vault` | Vault 知識庫（.md 檔案） |
| `engine-data` | `/data` | ChromaDB + 備份 + config.json |

### 4. 遠端 VS Code MCP 連線（SSE）

在本機 VS Code 的 `mcp.json` 設定：

```json
{
  "servers": {
    "ai-memory-vault": {
      "url": "http://your-server-ip:8765/sse"
    }
  }
}
```

### 5. 環境變數

| 變數 | 預設 | 說明 |
|------|------|------|
| `VAULT_PORT` | `8765` | SSE Server 監聽 port |
| `VAULT_DATA_DIR` | `/data` | 可寫資料目錄 |
| `VAULT_HOST` | `0.0.0.0` | SSE Server 監聽 host |

---

## 專案結構

```
AI-Memory-Vault/
├── AI_Engine/                → Python RAG 引擎（v3.7）
│   ├── core/                 → 核心模組（embeddings / vectorstore / indexer / retriever / migration / frontmatter）
│   ├── services/             → 業務邏輯（vault / scheduler / instinct / backup / agent_router / ...）
│   │   └── _vault/           → VaultService 內部拆分（note_ops / search_ops / index_ops）
│   ├── mcp_app/              → MCP Server（FastMCP stdio + SSE，40 個工具）
│   │   └── tools/            → 工具模組（vault / scheduler / project / todo / index / agent / instinct）
│   ├── cli/                  → 互動式 CLI（REPL + 選單模式）
│   ├── packaging/            → 打包腳本（build.spec / build.ps1 / installer.iss）
│   │   └── shortcuts/        → 安裝捷徑 .bat
│   ├── scripts/              → 開發者腳本（auto_tasks / scheduler-menu / setup-menu）
│   ├── tests/                → 單元 + 整合測試（247 PASS）
│   ├── docs/                 → 專案文件
│   │   └── api-maps/         → API Map 分層文件（5 層）
│   ├── config.py             → 設定管理（config.json + .env；frozen/dev 路徑自動分離）
│   ├── main.py               → 入口點（三模式 + 排程 + 設定）
│   └── requirements.txt      → Python 依賴
│
├── Vault/                    → 知識庫內容
│   ├── _config/              → AI 系統設定（nav / handoff / agents — inject:true 自動注入）
│   ├── workspaces/           → 工作空間（依組織分）
│   │   └── _global/          → 全域共用（rules / skills）
│   ├── personal/             → 個人空間（reviews / goals / instincts）
│   ├── knowledge/            → 永久知識卡片
│   └── templates/            → 模板系統
│
├── Dockerfile                → Docker 映像設定
└── docker-compose.yml        → Docker Compose 編排（mcp-sse + scheduler）
```

---

## MCP 工具一覽（40 個）

### Vault 筆記操作（10 個）

| 工具 | 參數 | 說明 |
|------|------|------|
| `search_vault` | `query`, `category?`, `doc_type?`, `mode?` | BM25 + 向量語意混合搜尋 |
| `sync_vault` | — | 增量同步 .md → ChromaDB |
| `read_note` | `file_path` | 讀取指定筆記原始內容 |
| `write_note` | `file_path`, `content`, `mode?` | 寫入/覆蓋或追加筆記，自動索引 |
| `edit_note` | `file_path`, `old_text`, `new_text` | 局部文字替換（不全覆蓋） |
| `delete_note` | `file_path` | 刪除筆記 + 移除向量 |
| `rename_note` | `old_path`, `new_path` | 移動/重命名 + 向量再索引 |
| `list_notes` | `path?`, `recursive?`, `max_results?` | 列出目錄下所有 .md |
| `batch_write_notes` | `notes` (list) | 批次寫入，單次索引 |
| `grep_vault` | `pattern`, `path?`, `is_regex?`, `max_results?` | 精確文字 / 正規表達式搜尋 |

### 排程生成（10 個）

| 工具 | 參數 | 說明 |
|------|------|------|
| `generate_project_daily` | `organization`, `project`, `date?` | 專案每日進度模板（冪等） |
| `generate_daily_review` | `date?`, `projects?` | 每日總進度表（永遠覆寫） |
| `generate_weekly_review` | `date?` | 每週總進度表 |
| `generate_monthly_review` | `date?` | 每月總進度表 |
| `log_ai_conversation` | `organization`, `project`, `session_name`, `content`, `detail?` | 對話摘要 + 結構化 detail + auto-learn |
| `generate_ai_weekly_analysis` | `date?` | AI 對話週報 |
| `generate_ai_monthly_analysis` | `date?` | AI 對話月報 |
| `generate_project_status` | `organization`, `project` | status.md 模板（冪等） |
| `list_scheduled_tasks` | — | 列出所有排程任務 |
| `run_scheduled_task` | `task_id` | 手動觸發排程任務 |

### 專案與知識（3 個）

| 工具 | 參數 | 說明 |
|------|------|------|
| `list_projects` | — | 列出所有組織與專案 |
| `get_project_status` | `organization`, `project` | 結構化讀取 status.md |
| `extract_knowledge` | `organization`, `project`, `topic`, `session?` | conversations → knowledge 萃取 |

### Todo 管理（3 個）

| 工具 | 參數 | 說明 |
|------|------|------|
| `update_todo` | `file_path`, `todo_text`, `done` | toggle checkbox |
| `add_todo` | `file_path`, `todo_text`, `section?` | 新增 todo 項目 |
| `remove_todo` | `file_path`, `todo_text` | 刪除 todo 項目 |

### 向量索引管理（5 個）

| 工具 | 參數 | 說明 |
|------|------|------|
| `check_vault_integrity` | — | 偵測孤立向量 |
| `clean_orphans` | — | 清除孤立向量 |
| `check_index_status` | — | 比對索引設定是否變更 |
| `reindex_vault` | — | 清除並重建索引 |
| `backup_chromadb` | — | 備份 ChromaDB 為 zip |

### Agent / Skill 管理（4 個）

| 工具 | 參數 | 說明 |
|------|------|------|
| `list_agents` | — | 列出 Agent 模板 |
| `dispatch_agent` | `agent_name` | 載入 Agent 完整行為指令 |
| `list_skills` | — | 列出 Skill 知識包 |
| `load_skill` | `skill_name` | 讀取 Skill 完整內容 |

### 直覺記憶（5 個）

| 工具 | 參數 | 說明 |
|------|------|------|
| `create_instinct` | `id`, `trigger`, `domain`, `title`, `action`, ... | 建立直覺卡片 |
| `update_instinct` | `id`, `confidence_delta?`, `new_evidence?` | 更新信心度 / 新增證據 |
| `search_instincts` | `query`, `domain?`, `min_confidence?` | 語意搜尋直覺卡片 |
| `list_instincts` | `domain?` | 列出所有卡片 |
| `generate_retrospective` | `month?` | 月度復盤報告 |

---

## CLI 指令

透過 `python main.py --mode cli` 或 `vault-cli.exe` 啟動，輸入 `--menu` 切換方向鍵選單模式。

```
搜尋與檔案
  search <query> [--cat C] [--type T] [--mode M]   搜尋記憶庫     (別名: s)
  read   <path>                                      讀取筆記       (別名: r)
  write  <path>                                      寫入筆記       (別名: w)
  delete <path>                                      刪除筆記       (別名: d)
  rename <old_path> <new_path>                       移動/重命名    (別名: mv)
  list   [<path>] [-r]                               列出 .md 檔案 (別名: ls)
  sync                                               同步 ChromaDB  (別名: sy)

專案管理
  status    <org> <proj>                             讀取專案狀態    (別名: st)
  todo      <path> <text> [done|undone]              切換 Todo      (別名: t)
  projects                                           列出所有專案    (別名: p)
  genstatus <org> <proj>                             生成 status.md (別名: gs)

進度表
  daily   <org> <proj> [<date>]                      專案每日進度    (別名: da)
  review  [<date>]                                   每日總進度表    (別名: rv)
  weekly                                             每週總結       (別名: wk)
  monthly                                            每月總結       (別名: mo)

AI 對話
  log      <org> <proj> <session>                    記錄 AI 對話   (別名: la)
  aiweekly [<date>]                                  AI 對話週報    (別名: aw)
  aimonthly [<date>]                                 AI 對話月報    (別名: am)
  extract  <org> <proj> <topic>                      萃取知識卡片    (別名: ex)

索引維護
  integrity                                          孤立向量檢查    (別名: ig)
  clean                                              清除孤立向量    (別名: cl)
  checkindex                                         索引狀態檢查    (別名: ci)
  reindex                                            重建向量索引    (別名: ri)

  help / q / exit
```

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
    "embedding": {
        "model": "paraphrase-multilingual-MiniLM-L12-v2",
        "device": "cpu",
        "chunk_size": 500,
        "chunk_overlap": 50
    },
    "search": {
        "top_k": 5,
        "use_hybrid": true,
        "bm25_weight": 0.4,
        "vector_weight": 0.6,
        "recency_bias_enabled": true,
        "recency_decay_days": 90
    },
    "database": {
        "chroma_dir": "chroma_db",
        "collection_name": "vault_main"
    }
}
```

敏感資訊放 `.env`：

```env
GOOGLE_API_KEY=your_key_here   # Gemini 使用
```

---

## 開發流程：修改程式後的更新步驟

> 以下為開發模式下，修改程式碼後需要執行的完整更新流程。

### 日常開發（修改 Python 程式碼）

修改程式碼後無需任何額外步驟，MCP Server 重啟即自動載入新程式碼：

```powershell
# VS Code：Ctrl+Shift+P → MCP: Restart Server
# 或手動重啟：
python main.py --mode mcp
```

### 新增 / 修改 MCP 工具

1. **編輯對應工具檔案**：`mcp_app/tools/{category}_tools.py`
2. **在 `register()` 函式中註冊新工具**（若為新增）
3. **加上 `@suppress_stdout` 裝飾器**（必要，保護 JSON-RPC 通道）
4. **撰寫測試**：`tests/test_{feature}.py`
5. **執行測試**：

```powershell
cd AI_Engine
.venv\Scripts\Activate.ps1
python -m pytest tests/ -q          # 快速驗證
python -m pytest tests/ -v          # 詳細輸出
python -m pytest tests/test_xxx.py  # 單一檔案
```

### 版本升版流程

修改核心功能後需同步更新三處版本號：

```powershell
# 1. 主版本號
#    AI_Engine/config.py → __version__ = "x.y.z"

# 2. pyproject.toml
#    AI_Engine/pyproject.toml → version = "x.y.z"

# 3. 安裝包版本
#    AI_Engine/packaging/installer.iss → #define AppVersion "x.y.z"
```

### PyInstaller 重新打包

```powershell
cd AI_Engine/packaging
.\build.ps1              # 僅 PyInstaller → dist/vault-ai/
.\build.ps1 -Clean       # 清除舊 build/dist 後重新打包
.\build-all.ps1          # PyInstaller + Inno Setup（需已安裝 Inno Setup 6.x）
```

重建前注意事項：
- 新增 Python 模組 → 在 `packaging/build.spec` 的 `HIDDEN_IMPORTS` 補上
- 新增 pip 套件 → 在 `requirements.txt` 加入，打包時會自動收集

### 打包後驗證

```powershell
# 確認 exe 可啟動
dist\vault-ai\vault-cli.exe --help

# 確認 Inno Setup 安裝包
dir dist\AI-Memory-Vault-Setup-v*.exe
```

### 更新 API Map 文件

修改公開 API 後，對應的 API Map 文件也需更新：

```
AI_Engine/docs/api-maps/
├── README.md              ← 主索引（架構圖 + 模組總覽）
├── 01-config_APIMap.md    ← Config 層
├── 02-core_APIMap.md      ← Core 層
├── 03-services_APIMap.md  ← Service 層
├── 04-mcp-tools_APIMap.md ← MCP 工具層
└── 05-transport_APIMap.md ← Transport 層
```

### 完整更新清單（Checklist）

修改程式碼後依需求執行：

- [ ] 程式碼修改完成
- [ ] `python -m pytest tests/ -q` — 247 測試全數通過
- [ ] 版本號同步（config.py / pyproject.toml / installer.iss）
- [ ] `build.spec` HIDDEN_IMPORTS 更新（如有新模組）
- [ ] `.\build.ps1` — PyInstaller 重新打包
- [ ] ISCC 建置安裝包（如需發佈）
- [ ] `docs/api-maps/` 對應文件更新（如有 API 變更）
- [ ] README.md 更新（如有新功能 / 新工具）

---

## 進階操作

### 重建向量索引

當更換 embedding 模型或調整 chunk_size 時：

```powershell
python main.py --reindex

# 或在 CLI 內
vault> checkindex   # 先確認是否需要重建
vault> reindex      # 互動式確認後重建
```

### 部分重新設定

```powershell
python main.py --setup-section vault    # 僅修改 Vault 路徑
python main.py --setup-section user     # 僅修改使用者資訊
python main.py --setup-section org      # 組織管理（新增/移除）
python main.py --setup-section llm      # 僅修改 LLM 設定
python main.py --reconfigure            # 全部重新設定（保留 DB）
```

### APScheduler 排程

```powershell
python main.py --scheduler       # 守護模式（持續執行）
python main.py --once             # 一次性執行（搭配 Windows 工作排程器）
python main.py --list-tasks       # 列出排程任務（JSON 格式）
python main.py --headless --task daily-review  # 執行特定任務
```

內建 8 個 cron 排程任務：每日專案進度、每日總結、每週總結、每月總結、AI 週報、AI 月報、知識萃取、ChromaDB 備份（03:00）。

---

## 已知注意事項

- `mcp_app/` 目錄（舊名 `mcp/`）因與 pip 套件 `mcp` 同名改名，避免 import 衝突
- Windows exe 的中文顯示需終端機支援 UTF-8（`chcp 65001`）
- `write_note` 的 `mode` 參數：`"overwrite"`（預設）或 `"append"`
- MCP 工具的 `Optional[dict]` 參數：必須用 `Optional[dict] = None`（FastMCP 限制）
- 所有 VaultService 寫入方法已加 filelock，新增寫入邏輯需 `with self._lock:`

---

## 開發路線圖

| 階段 | 狀態 | 內容 |
|------|------|------|
| **Phase 1-3** | ✅ 完成 | RAG 核心 + ChromaDB + MCP Server + Scheduler + 打包基建 + 測試 |
| **Phase 4** | ✅ 完成 | PyInstaller 打包 → `vault-cli.exe` / `vault-mcp.exe` / `vault-scheduler.exe` |
| **Phase 5** | ✅ 完成 | Inno Setup 安裝精靈 → `AI-Memory-Vault-Setup-v3.7.0.exe` |
| **v3.6** | ✅ 完成 | Agent / Skill / Instinct 系統 + Post-write hook + Auto-learn pipeline |
| **v3.7** | ✅ 完成 | filelock + ChromaDB 備份 + SSE Transport + Docker 容器化 + 247 測試 |
| **Phase 6** | 📋 計畫中 | Tauri + React GUI → 完整桌面應用程式 |
