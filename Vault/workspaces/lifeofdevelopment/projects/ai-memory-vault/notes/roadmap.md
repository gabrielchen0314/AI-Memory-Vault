---
type: roadmap
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
created: 2026.04.04
last_updated: 2026.04.10
---

# 專案 Roadmap — AI Memory Vault

## 專案定位

AI-powered Vault 知識管理系統，以 MCP Server 形式整合至 VS Code / Claude Desktop，
提供 AI 對話記憶、工作進度追蹤、Vault 寫入/讀取/搜尋工具。

---

## 已完成階段

### Phase 1–8（基礎建設）
- ChromaDB 向量儲存 + Obsidian Vault 雙軌架構
- FastMCP Server（read/write/search/sync 四大工具）
- LLM Factory（多 provider 支援：OpenAI, Ollama, Gemini）
- CLI REPL + API（FastAPI）
- Discord / LINE channel adapter
- 全域 `config.json` + dataclass 設定層

### Phase 9–10（穩定性）
- `_sync_write()` 修正（Scheduler 同步至 ChromaDB）
- MCP Server stdout 污染修正（all print() → stderr）
- MCP lifespan hook + Org skeleton 自動建立
- MCP Server instructions 注入（Vault nav 內容）

### Phase 11（Single Source of Truth）
- `VaultPaths` dataclass — 統一所有路徑邏輯

### Phase 12（多組織 + UX 提升）
- `organizations: list` 取代 `organization: str`（含 migration shim）
- `main.py` 重構：`--setup-section {vault,user,org,llm}` + `--reconfigure`
- 組織管理 wizard + 低門檻操作入口

### Phase 13（Vault 架構重構）
- per-project `status.md`（工作脈絡 + 待辦 + 決策）
- `_config/handoff.md` 輕量跨專案索引
- End-of-day SOP 確立

### Phase 14（驗證 + 工具補齊）✅
- `--setup` 首次初始化流程驗證 ✅
- 新增 MCP tool：`generate_project_status`、`list_projects` ✅

### Phase 15（品質 + 穩健性）✅
- E2E 35/35 全通過 ✅
- `check_vault_integrity`、`batch_write_notes`、`update_todo` MCP tool ✅
- `generate_*_review` 冪等修正（永遠覆寫）✅
- Coding 規則 3 層架構建立 ✅

### Phase 16（工具補齊 + 規則整合）✅
- `delete_note` MCP tool（VaultIndexer + VaultService + server v3.5）✅
- `get_project_status` MCP tool（status.md 結構化讀取）✅
- `setup_regression_test.py`（22/22 PASS）✅
- E2E 擴充 Step 10–11（get_project_status + delete_note）✅
- 全規則合併至 `_global/rules/`（01–14），刪除 org 舊規則 ✅
- `vault-coding-rules.instructions.md` 重構為動態規則發現 ✅
- `global-prompts-maintenance.instructions.md` SOP 建立 ✅
- sync_vault 清理孤立向量（Deleted=22）✅

### Phase 17（VS Code 整合）✅
- `AppConfig.vscode_user_path` 欄位 ✅
- `SetupService` Step 6：自動生成 VS Code instructions 檔（冪等）✅
  - `vault-coding-rules.instructions.md`（動態發現，永不過期）
  - `VaultWriteConventions.instructions.md`
- E2E Step 12（vscode integration，46/46 PASS）✅

### Phase 18（Scheduler 增強）✅
- Weekly/monthly 自動觸發（APScheduler，週一/月初自動生成）✅
- Daily note AI 彙整（`_scan_today_conversations()` + daily template 加入「今日 AI 對話」區塊）✅
- `auto_tasks.ps1` 修正 3 個舊方法名 ✅
- Embedding 策略評估（chunk_size=500 / overlap=50 已設定可調）✅
- 混合搜尋模式預設（BM25 0.4 / Vector 0.6）+ keyword/semantic 指定模式 ✅

### Phase 19（功能補齊 + 技術負債清除）✅
- [x] `generate_project_daily` 內容預填充（從 status.md 待辦事項自動填入「今日計畫」）
- [x] CLI REPL 實作（`cli/repl.py` — 13 個指令，直接呼叫 VaultService / SchedulerService，E2E Step 16 89/89 PASS）
- [x] Scheduler 單元測試（`tests/test_scheduler.py` 42 個測試，conftest.py stub VaultService，E2E Step 17 90/90 PASS）
- [x] CLI REPL 對齊 MCP 工具（新增 `review` / `genstatus` / `log` / `aiweekly` / `aimonthly` 和別名，E2E Step 18 106/106 PASS）
- [x] CLI 自動化同步（`tools/registry.py` 宣告式登記表，repl.py 自動橋接，E2E Step 19 166/166 PASS）

### Phase 20（版本控制 + 知識萃取）✅
- [x] `services/git_service.py`（GitService：ensure_repo, commit, commit_delete）
- [x] `config.py` 新增 `GitConfig`（auto_commit: bool, author_name, author_email）
- [x] `VaultService.write_note()` / `delete_note()` / `batch_write_notes()` 鉤入 git commit
- [x] E2E Step 20（Git 整合，17 checks，183/183 PASS）
- [x] `extract_knowledge` MCP tool + `KnowledgeExtractor` 服務

### Phase 21（架構重整 — server 拆分 + 工具強化）✅
- [x] MCP Server 由單一 server.py（730 行）拆分為 7 個工具模組（mcp_app/tools/）
- [x] SchedulerService + InstinctService 改為 lifespan 單例（消除 C-2 問題）
- [x] `edit_note` 局部編輯 MCP tool（old_text → new_text 替換）
- [x] `rename_note` 筆記移動 + ChromaDB 向量再索引
- [x] `grep_vault` 精確文字 / 正規表達式搜尋
- [x] `add_todo` / `remove_todo` 新增/移除 todo 項目
- [x] `check_index_status` / `reindex_vault` / `clean_orphans` 索引管理 3 工具
- [x] `token_counter.py` 服務 + AI 週報 Token 欄位
- [x] Logging 全模組統一（core/logger.py + logging 取代散落 print）
- [x] `log_ai_conversation` 強化：`detail` 參數（Optional[dict]）支援結構化詳細紀錄
- [x] API Map 規則整備：02 修正 + 15 新增（api-map-writing-guide.md）
- [x] VS Code prompts 架構重構（vault-bridge 唯一橋接入口原則）

### Phase 22（Agent + Skill + Instinct 系統）✅
- [x] `AgentRouter` 服務（services/agent_router.py）— 讀取 templates/agents/*.md
- [x] `dispatch_agent` / `list_agents` MCP tools（agent_tools.py）
- [x] `list_skills` / `load_skill` MCP tools（從 workspaces/_global/skills/ 載入）
- [x] 10 個 Agent 模板建立（Architect / CodeReviewer / Planner / Refactor-Cleaner / DocUpdater / GitCommitter / BuildErrorResolver / SecurityReviewer / TddGuide / LearnTrigger）
- [x] `InstinctService`（services/instinct.py）— 直覺卡片 CRUD + 語意搜尋
- [x] `create_instinct` / `update_instinct` / `search_instincts` / `list_instincts` MCP tools
- [x] `generate_retrospective` 月度復盤報告 MCP tool

---

## 進行中

### Phase 23（Skills 知識包建立 + 收尾）

- [ ] 建立 `workspaces/_global/skills/` 目錄 + 首批 Skill 知識包
- [ ] 驗證 `detail` 參數 FastMCP 相容性（MCP 重啟後測試）
- [ ] PyInstaller rebuild（打包至 v3.6.0）
- [ ] 安裝包版本號更新（v3.5.0 → v3.6.0）

---

## 長期展望（Phase 24+）

| 方向 | 說明 |
|------|------|
| v3 UI | Tauri + React 聊天介面 + 搜尋 + 設定面板 |
| Web UI | 輕量 Next.js dashboard |
| 多使用者 | team Vault 支援 |
| Mobile | Obsidian Mobile + MCP 遠端連線 |
| 統一錯誤模型 | VaultError 基礎異常 + VaultResult 資料類別 |
| 動態 Task 管理 | create / get / update / stop 任務 |

---

## 技術負債

| 負債項目 | 嚴重度 | 說明 |
|---------|------|------|
| VaultError 統一錯誤模型 | 中 | 目前 4 層各有不同錯誤格式 |
| CLI 手動 dispatch 未完全遷移 | 低 | ~10 個工具尚未納入 TOOL_REGISTRY |
| ChromaDB migration 機制 | 中 | Schema 變更時無 migration 路徑 |

---

## MCP Tools 清單（39 個，v3.6）

### Vault 筆記操作（vault_tools.py）

| Tool | 版本加入 | 說明 |
|------|----------|------|
| `search_vault` | v1 | BM25 + 向量混合搜尋 |
| `sync_vault` | v1 | 增量同步 .md → ChromaDB |
| `read_note` | v1 | 讀取 Vault 筆記原始內容 |
| `write_note` | v1 | 寫入/更新 Vault 筆記 + 索引 |
| `edit_note` | v3.6 | 局部文字替換（old→new，不全覆蓋） |
| `delete_note` | v3.5 | 刪除 .md 並移除 ChromaDB 向量 |
| `rename_note` | v3.6 | 移動筆記 + 向量再索引 |
| `list_notes` | v3.3 | 列出指定目錄下所有 .md |
| `batch_write_notes` | v3.3 | 批次寫入多筆，單次索引 |
| `grep_vault` | v3.6 | 精確文字 / 正規表達式搜尋 |

### 排程生成工具（scheduler_tools.py）

| Tool | 版本加入 | 說明 |
|------|----------|------|
| `generate_project_daily` | v3 | 專案每日進度模板（冪等） |
| `generate_daily_review` | v3 | 每日總進度表（永遠覆寫） |
| `generate_weekly_review` | v3 | 每週總進度表（永遠覆寫） |
| `generate_monthly_review` | v3 | 每月總進度表（永遠覆寫） |
| `log_ai_conversation` | v3 | 記錄 AI 對話 + 可選 detail 結構化紀錄 |
| `generate_ai_weekly_analysis` | v3 | AI 對話週報分析模板 |
| `generate_ai_monthly_analysis` | v3 | AI 對話月報分析模板 |
| `generate_project_status` | v3.2 | status.md 模板生成（冪等） |
| `list_scheduled_tasks` | v3.5 | 列出排程任務清單 |
| `run_scheduled_task` | v3.5 | 手動觸發排程任務 |

### 專案與知識管理（project_tools.py）

| Tool | 版本加入 | 說明 |
|------|----------|------|
| `list_projects` | v3.2 | 列出所有組織及專案 |
| `get_project_status` | v3.4 | status.md 結構化讀取 |
| `extract_knowledge` | v3.5 | conversations/ → knowledge/ 萃取 |

### Todo 管理（todo_tools.py）

| Tool | 版本加入 | 說明 |
|------|----------|------|
| `update_todo` | v3.3 | todo checkbox toggle |
| `add_todo` | v3.6 | 新增 todo 項目（指定 section） |
| `remove_todo` | v3.6 | 整行刪除 todo 項目 |

### 向量索引管理（index_tools.py）

| Tool | 版本加入 | 說明 |
|------|----------|------|
| `check_vault_integrity` | v3.3 | 孤立向量偵測 |
| `clean_orphans` | v3.6 | 外科手術清除孤立向量 |
| `check_index_status` | v3.6 | 索引設定比對（是否需重建） |
| `reindex_vault` | v3.6 | 清除並重建索引 |

### Agent 與 Skill 管理（agent_tools.py）

| Tool | 版本加入 | 說明 |
|------|----------|------|
| `list_agents` | v3.6 | 列出所有 Agent 模板 |
| `dispatch_agent` | v3.6 | 載入指定 Agent 完整指令 |
| `list_skills` | v3.6 | 列出 skills/ 知識包 |
| `load_skill` | v3.6 | 讀取 Skill 知識包完整內容 |

### 直覺記憶工具（instinct_tools.py）

| Tool | 版本加入 | 說明 |
|------|----------|------|
| `create_instinct` | v3.6 | 建立直覺卡片 |
| `update_instinct` | v3.6 | 更新信心度 / 新增證據 |
| `search_instincts` | v3.6 | 語意搜尋直覺卡片 |
| `list_instincts` | v3.6 | 列出所有卡片（依信心度排序） |
| `generate_retrospective` | v3.6 | 月度復盤報告生成 |
