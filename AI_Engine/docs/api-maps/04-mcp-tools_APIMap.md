# MCP Tool 層 API Map

> **目錄**：`mcp_app/tools/`
> **用途**：40 個 MCP 工具的對外接口定義（7 個模組）
> **最後更新**：2026.04.10

---

## 1. 模組概覽

| 模組 | 檔案 | 工具數 | 註冊方式 |
|------|------|--------|---------|
| Vault 筆記 | `vault_tools.py` | 10 | `register(mcp)` |
| 排程生成 | `scheduler_tools.py` | 10 | `register(mcp, get_sched)` |
| 專案管理 | `project_tools.py` | 3 | `register(mcp)` |
| Todo 管理 | `todo_tools.py` | 3 | `register(mcp)` |
| 索引管理 | `index_tools.py` | 5 | `register(mcp)` |
| Agent/Skill | `agent_tools.py` | 4 | `register(mcp)` |
| 直覺記憶 | `instinct_tools.py` | 5 | `register(mcp, get_instinct)` |

### 架構說明

每個 tool 模組都有 `register(mcp, ...)` 函式，在 `mcp_app/server.py` 的 lifespan 中呼叫。Tool 函式用 `@mcp.tool()` 裝飾器註冊，並由 `@suppress_stdout` 包裝以保護 MCP JSON-RPC 通訊。

```
server.py → lifespan
    ├── vault_tools.register(mcp)
    ├── scheduler_tools.register(mcp, get_sched)
    ├── project_tools.register(mcp)
    ├── todo_tools.register(mcp)
    ├── index_tools.register(mcp)
    ├── agent_tools.register(mcp)
    └── instinct_tools.register(mcp, get_instinct)
```

### 共通回傳格式

所有 MCP 工具回傳 `str`（繁體中文），格式化為 AI 可直接解析的結構化文字。錯誤以 `Error:` 前綴回傳。

---

## 2. Vault 筆記操作（10 個）

> **檔案**：`mcp_app/tools/vault_tools.py`
> **委派**：`VaultService.*`

| MCP 工具 | 參數 | 說明 |
|----------|------|------|
| `search_vault` | `query: str, category: str="", doc_type: str="", mode: str=""` | BM25 + 向量混合搜尋 |
| `sync_vault` | — | 全量增量同步 .md → ChromaDB |
| `read_note` | `file_path: str` | 讀取指定筆記原始內容 |
| `write_note` | `file_path: str, content: str, mode: str="overwrite"` | 寫入/更新筆記 + 自動索引 |
| `edit_note` | `file_path: str, old_text: str, new_text: str` | 精確文字替換（必須唯一匹配） |
| `delete_note` | `file_path: str` | 刪除 .md + 移除 ChromaDB 向量 |
| `rename_note` | `old_path: str, new_path: str` | 移動筆記 + 向量重索引 |
| `list_notes` | `path: str="", recursive: bool=False, max_results: int=50` | 列出指定目錄下所有 .md |
| `batch_write_notes` | `notes: list[dict]` | 批次寫入多筆，單次索引 |
| `grep_vault` | `pattern: str, path: str="", is_regex: bool=False, max_results: int=50` | 精確文字 / 正規表達式搜尋 |

### 使用範例

```
search_vault(query="filelock 併發", mode="keyword")
write_note(file_path="knowledge/my-note.md", content="# 筆記\n\n內容")
edit_note(file_path="status.md", old_text="- [ ] 待辦", new_text="- [x] 完成")
```

---

## 3. 排程生成（10 個）

> **檔案**：`mcp_app/tools/scheduler_tools.py`
> **委派**：`SchedulerService.*`（透過 `get_sched()` 閉包）

| MCP 工具 | 參數 | 說明 |
|----------|------|------|
| `generate_project_daily` | `organization: str, project: str, date: str=""` | 專案每日進度模板（冪等） |
| `generate_daily_review` | `date: str="", projects: list=[]` | 每日總進度表（永遠覆寫） |
| `generate_weekly_review` | `date: str=""` | 每週總進度表（永遠覆寫） |
| `generate_monthly_review` | `date: str=""` | 每月總進度表（永遠覆寫） |
| `log_ai_conversation` | `organization: str, project: str, session_name: str, content: str, detail: Optional[dict]=None` | 對話摘要 + 可選結構化紀錄 |
| `generate_ai_weekly_analysis` | `date: str=""` | AI 對話週報（準確率/Token） |
| `generate_ai_monthly_analysis` | `date: str=""` | AI 對話月報（趨勢/評分） |
| `generate_project_status` | `organization: str, project: str` | status.md 模板生成（冪等） |
| `list_scheduled_tasks` | — | 列出排程任務清單 |
| `run_scheduled_task` | `task_id: str` | 手動觸發排程任務 |

---

## 4. 專案管理（3 個）

> **檔案**：`mcp_app/tools/project_tools.py`
> **委派**：`VaultService.*` + `SchedulerService.extract_knowledge`

| MCP 工具 | 參數 | 說明 |
|----------|------|------|
| `list_projects` | — | 列出所有組織及專案 |
| `get_project_status` | `organization: str, project: str` | status.md 結構化讀取（待辦 + 脈絡） |
| `extract_knowledge` | `organization: str, project: str, topic: str, session: str=""` | conversations/ → knowledge/ 萃取 |

---

## 5. Todo 管理（3 個）

> **檔案**：`mcp_app/tools/todo_tools.py`
> **委派**：`VaultService.*`

| MCP 工具 | 參數 | 說明 |
|----------|------|------|
| `update_todo` | `file_path: str, todo_text: str, done: bool` | todo checkbox toggle（不全覆蓋） |
| `add_todo` | `file_path: str, todo_text: str, section: str=""` | 新增 todo 項目（指定 section） |
| `remove_todo` | `file_path: str, todo_text: str` | 整行刪除 todo 項目 |

---

## 6. 向量索引管理（5 個）

> **檔案**：`mcp_app/tools/index_tools.py`
> **委派**：`VaultService.*` + `BackupService.backup_chromadb`

| MCP 工具 | 參數 | 說明 |
|----------|------|------|
| `check_vault_integrity` | — | 孤立 ChromaDB 向量偵測 |
| `clean_orphans` | — | 外科手術清除孤立向量 |
| `check_index_status` | — | 索引設定比對（是否需重建） |
| `reindex_vault` | — | 清除並重建索引 |
| `backup_chromadb` | — | ChromaDB ZIP 備份（含自動清理保留 7 份） |

---

## 7. Agent 與 Skill 管理（4 個）

> **檔案**：`mcp_app/tools/agent_tools.py`
> **委派**：`AgentRouter.*` + `VaultService.read_note/list_notes`

| MCP 工具 | 參數 | 說明 |
|----------|------|------|
| `list_agents` | — | 列出所有 Agent 模板（templates/agents/） |
| `dispatch_agent` | `agent_name: str` | 以 name/trigger/domain 載入 Agent 完整行為指令 |
| `list_skills` | — | 列出 workspaces/_global/skills/ 知識包 |
| `load_skill` | `skill_name: str` | 讀取 Skill 知識包完整內容 |

---

## 8. 直覺記憶（5 個）

> **檔案**：`mcp_app/tools/instinct_tools.py`
> **委派**：`InstinctService.*`（透過 `get_instinct()` 閉包）

| MCP 工具 | 參數 | 說明 |
|----------|------|------|
| `create_instinct` | `id: str, trigger: str, domain: str, title: str, action: str, correct_pattern: str="", evidence: str="", reflection: str="", confidence: float=0.0, source: str="session-observation"` | 建立直覺卡片 |
| `update_instinct` | `id: str, confidence_delta: float=0.0, new_evidence: str=""` | 更新信心度 / 新增證據 |
| `search_instincts` | `query: str, domain: str="", min_confidence: float=0.0` | 語意搜尋直覺卡片 |
| `list_instincts` | `domain: str=""` | 列出所有卡片（依信心度排序） |
| `generate_retrospective` | `month: str=""` | 月度復盤報告生成（Instinct + 統計） |

---

## 9. 設計注意事項

### 9.1 suppress_stdout 裝飾器

所有 MCP tool 函式必須使用 `@suppress_stdout` 裝飾，防止 ML 模型載入時的 print 污染 MCP stdio JSON-RPC 通道。

### 9.2 Optional[dict] 參數

FastMCP 的 optional dict 參數必須用 `Optional[dict] = None`（不能用 `dict = None`），否則會產生 schema 錯誤。

### 9.3 閉包取得服務實例

`scheduler_tools` 和 `instinct_tools` 透過 `get_sched()` / `get_instinct()` 閉包取得 lifespan 中建立的單例。不可在 tool 內自行 import 建立新實例。
