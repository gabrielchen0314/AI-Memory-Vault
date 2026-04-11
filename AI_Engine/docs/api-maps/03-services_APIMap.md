# Service 層 API Map

> **目錄**：`services/`
> **用途**：業務邏輯層 — VaultService Facade + 8 個獨立服務
> **最後更新**：2026.04.10

---

## 1. 模組概覽

| 模組 | 檔案 | 職責 | 對外方法數 |
|------|------|------|-----------|
| **VaultService** | `services/vault.py` | 業務邏輯 Facade（唯一入口） | 20 |
| BackupService | `services/backup.py` | ChromaDB ZIP 備份 + 清理 | 3 |
| InstinctService | `services/instinct.py` | 直覺卡片 CRUD + 搜尋 + 復盤 | 5 |
| SchedulerService | `services/scheduler.py` | 排程生成（daily/weekly/monthly） | 9 |
| AutoScheduler | `services/auto_scheduler.py` | APScheduler cron 觸發層 | 6 |
| AgentRouter | `services/agent_router.py` | Agent 模板掃描 + 分發 | 4 |
| GitService | `services/git_service.py` | Vault git 自動 commit | 3 |
| KnowledgeExtractor | `services/knowledge_extractor.py` | 對話 → 知識卡片萃取 | 1 |
| SetupService | `services/setup.py` | 首次執行初始化精靈 | 1 |
| TokenCounter | `services/token_counter.py` | 輕量 Token 估算 | 3 |

### 架構說明

```
MCP Tool / CLI / Transport
         │
         ▼
   ┌─────────────┐
   │ VaultService │ ← Facade：唯一業務入口
   │ (classmethod)│
   └──────┬──────┘
          │ 委派至
   ┌──────▼──────┐
   │ _vault/     │ ← 內部實作（note_ops / search_ops / index_ops）
   └─────────────┘
          │ 使用
   ┌──────▼──────┐
   │  Core 層    │ ← indexer / retriever / vectorstore / errors
   └─────────────┘
```

其他服務（Scheduler, Instinct, Backup 等）由 MCP Server lifespan 或 AutoScheduler 直接使用，不經過 VaultService。

---

## 2. VaultService — 業務邏輯 Facade

> **入口檔案**：`services/vault.py`
> **設計模式**：Classmethod API + Facade + Observer (Hook)
> **寫入安全**：所有寫入方法使用 `filelock.FileLock` 跨行程互斥

### 2.1 初始化

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `initialize(iConfig)` | `AppConfig` | `None` | 注入設定，初始化所有依賴（執行緒安全） |

### 2.2 筆記 CRUD

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `read_note(iFilePath)` | rel path | `tuple[str\|None, str\|None]` | 讀取筆記（成功, 錯誤） |
| `write_note(iFilePath, iContent, iMode="overwrite")` | path, content, mode | `tuple[dict\|None, str\|None]` | 寫入 + 自動索引 |
| `batch_write_notes(iNotes)` | `[{path, content, mode}]` | `tuple[list, dict, str\|None]` | 批次寫入 + 統一索引 |
| `edit_note(iFilePath, iOldText, iNewText)` | path, old, new | `tuple[dict\|None, str\|None]` | 精確文字替換（唯一匹配） |
| `delete_note(iFilePath)` | rel path | `tuple[dict\|None, str\|None]` | 刪除 .md + 移除向量 |
| `rename_note(iOldPath, iNewPath)` | old, new | `tuple[dict\|None, str\|None]` | 移動 + 重索引 |
| `list_notes(iPath="", iRecursive=False)` | path, recursive | `tuple[dict\|None, str\|None]` | 列出 .md 檔案 |
| `list_projects()` | — | `tuple[list\|None, str\|None]` | 列出組織/專案 |

**iMode 選項**：`"overwrite"`（覆寫）/ `"append"`（追加）

### 2.3 Todo 操作

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `update_todo(iFilePath, iTodoText, iDone)` | path, text, bool | `tuple[dict\|None, str\|None]` | 切換 checkbox |
| `add_todo(iFilePath, iTodoText, iSection="")` | path, text, section | `tuple[dict\|None, str\|None]` | 新增 todo |
| `remove_todo(iFilePath, iTodoText)` | path, text | `tuple[dict\|None, str\|None]` | 移除 todo 行 |

### 2.4 搜尋

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `search(iQuery, iCategory="", iDocType="", iTopK=None, iMode="")` | 查詢, 過濾器 | `list` | 語意搜尋 |
| `search_formatted(iQuery, iCategory="", iDocType="", iMode="")` | 查詢, 過濾器 | `str` | 格式化搜尋結果 |
| `grep(iPattern, iPath="", iIsRegex=False, iMaxResults=50)` | pattern, flags | `tuple[list\|None, str\|None]` | 文字/正規式搜尋 |

### 2.5 索引管理

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `sync()` | — | `dict` | 全量增量同步 |
| `check_integrity()` | — | `tuple[dict\|None, str\|None]` | 檢查孤立向量 |
| `clean_orphans()` | — | `tuple[dict\|None, str\|None]` | 清除孤立向量 |
| `get_project_status(iOrg, iProject)` | org, project | `tuple[dict\|None, str\|None]` | status.md 結構化讀取 |

### 2.6 Post-Write Hooks

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `register_post_write_hook(iCallback)` | `Callable[[str], None]` | `None` | 註冊寫入後回呼（接收 rel_path） |
| `unregister_post_write_hook(iCallback)` | callback | `None` | 移除回呼 |

**Hook 行為**：
- 寫入成功後自動呼叫所有已註冊的 hook
- 錯誤隔離：單一 hook 例外不影響其他 hook 或主流程
- MCP Server 在 lifespan 中註冊 `_on_vault_write` hook

### 2.7 內部實作（_vault/）

| 檔案 | 匯出函式 | 說明 |
|------|---------|------|
| `note_ops.py` | `read_note, write_note, batch_write_notes, edit_note, delete_note, rename_note, list_notes, list_projects, update_todo, add_todo, remove_todo` | 筆記 CRUD + Todo |
| `search_ops.py` | `search, search_formatted, grep` | 搜尋 |
| `index_ops.py` | `sync, check_integrity, clean_orphans, get_project_status` | 索引 + 狀態 |

> 所有函式第一參數為 `cls`（VaultService class reference），由 Facade classmethod 委派。
> **外部不應直接 import `services._vault`**。

---

## 3. BackupService

> **入口檔案**：`services/backup.py`
> **用途**：ChromaDB 目錄壓縮備份 + 舊備份清理

**常數**：`BACKUP_DIR = DATA_DIR / "backups"`，`DEFAULT_MAX_KEEP = 7`

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `__init__(iConfig)` | AppConfig | — | 初始化 |
| `backup_chromadb()` | — | `tuple[str\|None, str\|None]` | ZIP 壓縮 ChromaDB → `backups/chroma_YYYYMMDD_HHMMSS.zip` |
| `cleanup(iMaxKeep=7)` | 保留數 | `int` | 清理舊備份，回傳刪除數 |
| `list_backups()` | — | `list[dict]` | 列出備份 `[{name, size_mb, created}]` |

---

## 4. InstinctService

> **入口檔案**：`services/instinct.py`
> **用途**：AI 直覺卡片的 CRUD、語意搜尋、信心度管理、月度復盤

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `__init__(iConfig)` | AppConfig | — | 初始化 |
| `create(iId, iTrigger, iDomain, iTitle, iAction, iCorrectPattern="", iEvidence="", iReflection="", iConfidence=0.0, iSource="session-observation")` | 卡片欄位 | `str` | 建立直覺卡片→回傳路徑 |
| `update(iId, iConfidenceDelta=0.0, iNewEvidence="")` | id, delta, evidence | `dict` | 更新信心度/證據→回傳 metadata |
| `list_all(iDomain="")` | domain filter | `list[dict]` | 列出全部卡片摘要 |
| `search(iQuery, iDomain="", iMinConfidence=0.0)` | query, filters | `list[dict]` | 向量搜尋直覺卡片 |
| `generate_retrospective(iMonth="")` | YYYY-MM | `str` | 月度復盤報告→回傳路徑 |

**信心度管理**：

| 閾值 | 意義 |
|------|------|
| ≥ 0.7 | 自動套用（主動提醒） |
| 0.3 ~ 0.69 | 參考（搜尋時顯示） |
| < 0.3 | 淘汰（不再顯示） |

---

## 5. SchedulerService

> **入口檔案**：`services/scheduler.py`
> **用途**：專案進度、總進度（daily/weekly/monthly）、AI 對話紀錄/分析的生成

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `__init__(iConfig)` | AppConfig | — | 初始化 |
| **專案進度** | | | |
| `generate_project_daily(iOrg, iProject, iDate=None)` | org, project, date | `str` | 每日進度模板（冪等） |
| `generate_project_status(iOrg, iProject)` | org, project | `str` | status.md 模板（冪等） |
| **總進度表** | | | |
| `generate_daily_summary(iDate=None, iProjects=None)` | date, projects | `str` | 每日總進度（永遠覆寫） |
| `generate_weekly_summary(iDate=None)` | date | `str` | 每週總進度（永遠覆寫） |
| `generate_monthly_summary(iDate=None)` | date | `str` | 每月總進度（永遠覆寫） |
| **AI 對話** | | | |
| `log_conversation(iOrg, iProject, iSessionName, iContent, iDetail=None)` | org, project, session, content, detail | `str` | 記錄對話 + 結構化詳情 |
| `generate_ai_weekly_analysis(iDate=None)` | date | `str` | AI 對話週報 |
| `generate_ai_monthly_analysis(iDate=None)` | date | `str` | AI 對話月報 |
| **知識萃取** | | | |
| `extract_knowledge(iOrg, iProject, iTopic, iSession=None)` | org, project, topic | `str` | 委派 KnowledgeExtractor |

**冪等 vs 覆寫**：
- `generate_project_daily` / `generate_project_status`：已存在不覆蓋
- `generate_*_summary`：永遠覆寫

**iDetail 結構**（Optional[dict]）：
```python
{
    "topic": str,
    "qa_pairs": [{"question", "analysis", "decision", "alternatives"}],
    "files_changed": [{"path", "action", "summary"}],
    "commands": [{"command", "purpose", "result"}],
    "problems": [{"problem", "cause", "solution"}],
    "learnings": [str],
    "decisions": [{"decision", "options", "chosen", "reason"}]
}
```

---

## 6. AutoScheduler

> **入口檔案**：`services/auto_scheduler.py`
> **用途**：APScheduler 觸發層，定期驅動 SchedulerService

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `__init__(iConfig)` | AppConfig | — | 初始化 |
| `start()` | — | `None` | 啟動背景排程（非阻塞） |
| `stop()` | — | `None` | 停止排程器 |
| `block()` | — | `None` | 阻塞主執行緒（守護進程模式） |
| `run_once(daily_only=False)` | daily_only | `list[tuple]` | 依日期執行一次所有適用任務 |
| `run_task(iTaskId)` | task id | `list[tuple]` | 執行單一任務 |
| `list_tasks()` | — | `list[dict]` | 所有可用任務（classmethod） |
| `job_count()` | — | `int` | 已排入的任務數 |

**排程任務清單（TASK_REGISTRY）**：

| ID | 排程 | 說明 |
|----|------|------|
| `daily-summary` | 每日 23:30 | 每日總進度表 |
| `weekly-summary` | 每週日 23:45 | 每週總進度表 |
| `weekly-ai` | 每週日 23:50 | AI 對話週報 |
| `monthly-summary` | 每月 1 日 00:15 | 每月總進度表 |
| `monthly-ai` | 每月 1 日 00:30 | AI 對話月報 |
| `vector-sync` | 每日 04:00 | 全量向量同步 |
| `morning-brief` | 每日 08:00 | 晨報 |
| `auto-all` | — | 一次性執行所有今日適用任務 |
| `monthly-retrospective` | 每月 1 日 01:00 | 月度復盤（Instinct 系統） |
| `db-backup` | 每日 03:00 | ChromaDB 自動備份 |

---

## 7. AgentRouter

> **入口檔案**：`services/agent_router.py`
> **用途**：掃描 Vault `templates/agents/` 的 Agent 模板，提供查詢/分發

**Dataclass `AgentTemplate`**：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `name` | `str` | Agent 名稱 |
| `trigger` | `str` | 觸發指令（@AgentName） |
| `domain` | `str` | 領域 |
| `summary` | `str` | 摘要 |
| `mcp_tools` | `list[str]` | 使用的 MCP 工具 |
| `related_rules` | `list[str]` | 關聯規則 |
| `workspace` | `str` | 適用工作空間 |
| `body` | `str` | 指令本體 |
| `file_path` | `str` | 檔案路徑 |

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `__init__(iVaultPath, iTemplateDir="templates/agents")` | vault 路徑 | — | 初始化 |
| `list_agents()` | — | `list[dict]` | Agent 摘要清單 |
| `get_agent(iName)` | name | `AgentTemplate\|None` | 以名稱取得 Agent |
| `resolve(iQuery)` | 查詢 | `AgentTemplate\|None` | trigger→domain→name 模糊匹配 |
| `reload()` | — | `int` | 強制重新掃描，回傳數量 |

---

## 8. GitService

> **入口檔案**：`services/git_service.py`
> **設計模式**：Classmethod API

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `ensure_repo(iVaultPath)` | vault 路徑 | `bool` | 確保 Git repo 存在（auto init） |
| `commit(iVaultPath, iRelPath, iMessage, iAuthorName="AI Memory Vault", iAuthorEmail="vault@localhost")` | vault, path, msg | `tuple[bool, str\|None]` | git add + commit |
| `commit_delete(iVaultPath, iRelPath, iAuthorName, iAuthorEmail)` | vault, path | `tuple[bool, str\|None]` | 刪除後 commit |

---

## 9. KnowledgeExtractor

> **入口檔案**：`services/knowledge_extractor.py`
> **用途**：從 conversations/ 掃描對話，萃取知識卡片草稿至 knowledge/

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `__init__(iConfig)` | AppConfig | — | 初始化 |
| `extract(iOrg, iProject, iTopic, iSession=None)` | org, project, topic, session | `tuple[str\|None, str\|None]` | 萃取知識卡片（冪等追加） |

---

## 10. SetupService

> **入口檔案**：`services/setup.py`
> **設計模式**：Classmethod API

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `run_setup(iConfig)` | AppConfig | `dict` | 完整初始化流程 |

**回傳 dict 結構**：
```python
{
    "dirs_created": int,         # 建立的目錄數
    "files_created": int,        # 建立的檔案數
    "db_initialized": bool,      # ChromaDB 初始化
    "chunks_indexed": int,       # 索引的 chunk 數
    "vscode_files_created": int  # VS Code 設定檔數
}
```

---

## 11. TokenCounter

> **入口檔案**：`services/token_counter.py`
> **設計模式**：靜態方法（無需實例化）

**常數**：`CHARS_PER_TOKEN = 4`

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `estimate(iText)` | text | `int` | 估算 token 數（4 字元 ≈ 1 token） |
| `count_file(iAbsPath)` | 絕對路徑 | `int` | 讀檔並估算 |
| `format_k(iTokens)` | token 數 | `str` | 格式化為 K 單位（"2.4k"） |

---

## 12. 設計注意事項

### 12.1 VaultService filelock

所有寫入方法使用 `filelock.FileLock`（`DATA_DIR / ".vault_write.lock"`）確保跨行程互斥。新增寫入邏輯需在 `with self._lock:` 內執行。

### 12.2 Post-Write Hook 生命週期

Hook 在 MCP Server `_lifespan` 中註冊/解除，確保與 Server 生命週期對齊。目前註冊的 hook：
- `_on_vault_write`：偵測 conversations/ 寫入→觸發 auto-learn pipeline

### 12.3 SchedulerService 單例

MCP Server 在 lifespan 中建立單一 SchedulerService 實例，透過 `_get_scheduler()` 閉包提供給 MCP Tool。不可在 tool 內自行建立新實例。
