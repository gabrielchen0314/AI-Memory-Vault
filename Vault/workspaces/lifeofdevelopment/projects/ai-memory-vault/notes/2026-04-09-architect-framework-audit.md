---
type: architecture-review
project: ai-memory-vault
org: lifeofdevelopment
created: 2026-04-09
last_updated: 2026-04-09
ai_summary: "Architect + Refactor-Cleaner 全面審查：框架重大問題、技術債、Agent/Tools/Skill 優化提案（參考 Claude Code 25 Tools）"
tags: [architecture, audit, refactor, tech-debt, optimization]
---

# AI Memory Vault v3 — 框架全面審查報告

> **審查範圍**：AI_Engine 全部模組（config / core / services / tools / mcp_app / cli / main）
> **審查模式**：Architect（架構分析）+ Refactor-Cleaner（技術債）+ Agent/Tools/Skill 優化
> **參考基準**：Claude Code 25 核心工具架構

---

## 一、重大問題（Critical）

### 🐛 C-1：`_exec_morning_brief` 屬性名稱錯誤 → 執行期崩潰

| 項目 | 內容 |
|------|------|
| 檔案 | `services/auto_scheduler.py` line 420 |
| 問題 | `self.m_Config.vault_root` — `AppConfig` 無 `vault_root` 屬性，正確應為 `vault_path` |
| 影響 | `morning-brief` 排程任務必定 `AttributeError` 崩潰 |
| 狀態 | ✅ **已修復**（本次審查直接修正） |

### ⚠️ C-2：MCP Server 每次工具呼叫都重新 `ConfigManager.load()` + `SchedulerService()`

| 項目 | 內容 |
|------|------|
| 檔案 | `mcp_app/server.py` 所有 `generate_*` / `log_*` / `extract_*` 工具 |
| 問題 | 約 12 個 MCP Tool 在每次呼叫內部都執行 `ConfigManager.load()` + `SchedulerService( _Config )`，重複讀取 config.json、建立物件 |
| 影響 | 效能浪費 + 記憶體碎片；VaultService 已有 classmethod 單例模式，但 SchedulerService 沒有 |
| 建議 | 在 `lifespan` 階段初始化一個 `SchedulerService` 實例，透過 `mcp.ctx` 傳入各 tool |

### ⚠️ C-3：`VaultService` classmethod 單例但無執行緒安全保護

| 項目 | 內容 |
|------|------|
| 檔案 | `services/vault.py` |
| 問題 | `m_IsInitialized` / `m_Indexer` / `m_Retriever` 等為類變數，MCP 服務在 asyncio 環境中可能併發呼叫 |
| 影響 | 如果 MCP Client 併發發送多個 tool call，可能出現「尚未初始化就被呼叫」的競態條件 |
| 建議 | 加入 `threading.Lock()` 或改用 `asyncio.Lock()`（視 FastMCP 架構而定） |

---

## 二、架構層級問題（Architecture）

### A-1：四層架構在 MCP Server 中打破

**現況**：
```
config → services → core → tools/registry → mcp_app → cli
```

**問題**：`mcp_app/server.py` 的 tool function 直接 import `services.vault` / `services.scheduler` / `services.knowledge_extractor` / `core.migration` / `config.ConfigManager`，等於同時穿越了 3 層。

**建議**：tool function 統一透過 VaultService 門面呼叫，SchedulerService 整合進 VaultService 或獨立單例。

### A-2：`tools/registry.py` 僅服務 CLI，MCP 未使用

`TOOL_REGISTRY` (12 ToolEntry) 存在聲明式的 tool 定義，但 MCP Server 的 25 個 `@mcp.tool()` 全部手動定義，兩者完全解耦。

**風險**：CLI 新增的 tool 不會自動反映到 MCP，反之亦然。
**建議**：統一 tool 註冊表，MCP + CLI 共用一份定義。

### A-3：缺乏統一錯誤模型

- `VaultService` 返回 `(result, error_string)`
- MCP tools 直接 `return f"Error: {_E}"`
- CLI 用 `print()` + `try/except`
- 排程器用 `_logger.error()`

同一個錯誤在 4 個界面有 4 種處理方式，無法統一追蹤。

**建議**：定義 `VaultError` 基礎異常類別 + `VaultResult` 資料類別，所有層使用統一回傳格式。

### A-4：日誌系統不完整

- 只有 `auto_scheduler.py` 和 `core/migration.py` 使用 `logging`
- 其餘模組一律 `print()`（混合 `sys.stderr` / `sys.stdout`）
- MCP 模式下 `print()` 流向不一致

**建議**：全模組統一使用 `logging`，main.py 層配置 handler（stderr / file）。

---

## 三、技術債（Refactor-Cleaner）

### D-1：`mcp_app/server.py` 膨脹（730+ 行）

25 個 tool 全部寫在同一個檔案，每個 tool 都有完整的 try/except + 重複的 import。

**建議**：
- 拆分為 `mcp_app/tools/vault_tools.py`、`mcp_app/tools/scheduler_tools.py`、`mcp_app/tools/admin_tools.py`
- 或使用裝飾器自動從 registry 產生 MCP tool

### D-2：`main.py` 巨型入口（400+ 行）

`main.py` 包含：argparse、依賴檢查、GUI 彈窗、bootstrap、各種 `_start_*` / `_run_*` 函式。

**建議**：
- `main.py` 只保留 argparse + dispatch
- 函式搬到 `cli/commands.py` 或各自的 service

### D-3：`cli/repl.py` 手動 dispatch 過長

`_dispatch()` 和 `_menu_dispatch()` 包含大量 `if / elif` 分支（search / read / write / delete / rename / status / ...），手動路由與參數收集。

**現有改善**：已有 `TOOL_REGISTRY` + `_collect_params()` 自動橋接，但仍有 ~10 個「手動工具」未遷移。

**建議**：將 search / read / write / delete / rename 等也納入 `TOOL_REGISTRY`，消除手動 dispatch。

### D-4：重複的 lazy import

幾乎每個 MCP tool 都有：
```python
from services.vault import VaultService
from config import ConfigManager
from services.scheduler import SchedulerService
```

Python 的 `import` 系統有模組快取，首次 import 後後續是 O(1) 查表，但程式碼可讀性差。

**建議**：在 `lifespan` 中匯入並快取，tool function 從上下文存取。

### D-5：匈牙利命名法一致性

整體良好（`m_Config`、`i` 前綴參數、`_LocalVar` 前底線），但有少數不一致：
- `_g_ChromaDir`（模組級全域用 `_g_`）✅ 一致
- `_ALIASES`（靜態常數）✅ 一致
- `_exec_morning_brief` 中 `_VaultRoot` 應為 `_VaultPath`（語義對齊 config）

### D-6：`_StdoutToStderr` 重複寫在每個 MCP tool 呼叫中

`with _StdoutToStderr():` 出現在 ~15 次。

**建議**：改用 MCP middleware / decorator 統一套用。

---

## 四、缺失功能（Gap Analysis）

### 對比 Claude Code 25 核心工具

| Claude Code 工具 | AI Vault 現況 | 缺口 | 優先級 |
|------------------|---------------|------|--------|
| **FileRead** | ✅ `read_note` | — | — |
| **FileWrite** | ✅ `write_note` + `batch_write_notes` | — | — |
| **FileEdit** | ❌ 無局部編輯 | 目前只有 overwrite / append，無 patch | P2 |
| **Glob** | ✅ `list_notes` | — | — |
| **Grep** | ⚠️ `search_vault`（語意搜尋） | 無純基於正規表達式的文字搜尋 | P2 |
| **NotebookEdit** | ❌ | 不適用（Markdown only） | — |
| **Bash** | ❌ | 無 shell 執行能力 | P3 |
| **WebFetch** | ❌ | 無 URL 存取 | P3 |
| **WebSearch** | ❌ | 無網路搜尋 | P3 |
| **Agent** | ❌ | 無 sub-agent 分派 | P1 |
| **SendMessage** | ❌ | 無跨 agent 通訊 | P2 |
| **TaskCreate/Get/Update/List/Stop/Output** | ⚠️ 排程任務（TASK_REGISTRY） | 只有 predefined tasks，非動態 Task 管理 | P2 |
| **EnterPlanMode / ExitPlanMode** | ❌ | 無規劃模式切換 | P3 |
| **TodoWrite** | ✅ `update_todo` | 僅切換 checkbox，無建立新 todo | P2 |
| **AskUserQuestion** | ❌ | 無互動式提問機制 | P3 |
| **Skill** | ❌ | 無技能套用/管理 | P1 |
| **ListMcpResources / ReadMcpResource** | ❌ | 無跨 MCP Server 呼叫 | P3 |
| **LSP** | ❌ | 不適用（非 IDE） | — |

### 具體缺失歸納

#### GAP-1：無 Sub-Agent 系統（P1）
目前所有工具扁平化在一個 MCP Server 中，無法：
- 將複雜任務分派給專門的 Agent（如 Reviewer Agent、Doc Agent）
- 多 Agent 協作完成收工流程

**建議**：
1. 實作 `AgentRouter` 服務，讀取 `templates/agents/*.md` 作為 Agent 定義
2. 新增 `dispatch_agent` MCP tool：根據任務描述自動路由到最適 Agent
3. Agent 之間透過 Vault 的 conversations/ 或 status.md 協調

#### GAP-2：無 Skill 系統（P1）
Vault 已有 `workspaces/_global/rules/*.md` 和 `templates/agents/*.md`，但引擎端無機制動態載入技能知識包。

**建議**：
1. 定義 `SkillEntry` dataclass（類似 `ToolEntry`）
2. Skill 存放於 `knowledge/skills/` 或 `workspaces/_global/skills/`
3. 新增 `load_skill` / `list_skills` MCP tools
4. Agent 在執行任務前自動查詢相關 Skill

#### GAP-3：無文字搜尋（Grep）（P2）
`search_vault` 是語意搜尋（embedding），但有時需要精確的關鍵字 / 正規表達式搜尋。

**建議**：
1. 新增 `grep_vault` MCP tool
2. 在 VaultService 中新增 `grep()` 方法，遍歷 .md 檔做文字比對
3. 支援 `pattern` (regex) + `path` (限定目錄) 參數

#### GAP-4：`update_todo` 功能不完整（P2）
只能切換既有 checkbox 的 done/undone，無法：
- 新增 todo 項目
- 刪除 todo 項目
- 批次更新

**建議**：擴充為 `manage_todo` tool，支援 `add` / `remove` / `toggle` / `list` 操作。

#### GAP-5：無 `edit_note` 局部編輯（P2）
目前只有 overwrite（全覆蓋）和 append（追加），無法對檔案做指定行的修改。

**建議**：新增 `edit_note` MCP tool，支援 `old_text` → `new_text` 替換模式（類似 FileEdit）。

---

## 五、優化建議路線圖

### Phase 5：穩定化 + 核心缺口修復

| 序號 | 任務 | 類型 | 估計複雜度 |
|------|------|------|-----------|
| 5.1 | 統一 SchedulerService 單例（MCP lifespan 注入） | 架構 | 低 |
| 5.2 | `_StdoutToStderr` 改用 decorator / middleware | 技術債 | 低 |
| 5.3 | 全模組統一 logging（取代 print） | 技術債 | 中 |
| 5.4 | 新增 `grep_vault` 精確搜尋 MCP tool | 功能 | 低 |
| 5.5 | 擴充 `update_todo` → `manage_todo`（add/remove） | 功能 | 低 |
| 5.6 | 新增 `edit_note` 局部編輯 MCP tool | 功能 | 中 |
| 5.7 | VaultError 統一錯誤模型 | 架構 | 中 |

### Phase 6：Agent + Skill 系統

| 序號 | 任務 | 類型 | 估計複雜度 |
|------|------|------|-----------|
| 6.1 | 設計 AgentRouter 架構（讀取 templates/agents/*.md） | 架構 | 高 |
| 6.2 | 實作 `dispatch_agent` / `list_agents` MCP tools | 功能 | 高 |
| 6.3 | 設計 Skill 載入系統（SkillEntry + skill index） | 架構 | 中 |
| 6.4 | 實作 `load_skill` / `list_skills` MCP tools | 功能 | 中 |
| 6.5 | Agent 收工流程自動化（串接 End-of-Day checklist） | 功能 | 中 |

### Phase 7：進階能力

| 序號 | 任務 | 類型 | 估計複雜度 |
|------|------|------|-----------|
| 7.1 | 動態 Task 管理（create / get / update / stop） | 功能 | 高 |
| 7.2 | MCP Server 拆分為 Tool / Agent / Admin 三個子 Server | 架構 | 高 |
| 7.3 | `server.py` 拆分為多個 tool module | 技術債 | 中 |
| 7.4 | 統一 TOOL_REGISTRY 同時驅動 CLI + MCP | 架構 | 高 |
| 7.5 | CLI 手動 dispatch 全面遷移至 TOOL_REGISTRY | 技術債 | 中 |

---

## 六、正面評價

審查過程中觀察到的良好實踐：

1. **config.py 資料結構設計優秀** — 完全使用 dataclass，路徑計算集中在 VaultPaths，ENGINE_DIR / DATA_DIR 分離正確處理 frozen 模式
2. **VaultPaths 的 helper methods** — `project_dir()`、`parse_project_path()`、`get_project_skeleton_dirs()` 等方法讓路徑邏輯集中化
3. **延遲載入策略執行到位** — torch / chromadb / sentence_transformers 均在 function 內 import，`@lru_cache` 確保只初始化一次
4. **VaultService 路徑防護** — `_validate_path` / `_validate_write_path` 有效防止目錄遍歷攻擊
5. **自動專案骨架建立** — `_ensure_project_skeleton()` 冪等設計，優雅處理新專案初始化
6. **Migration 系統完整** — `vault_meta.json` signature 比對 + `MigrationManager` 偵測 embedding 設定變更
7. **測試覆蓋率良好** — 11 個測試模組涵蓋 scheduler / vault_service / retriever / migration / cli / knowledge_extractor
8. **Git 整合優雅** — `GitService` 靜默降級設計（git 不在 PATH 時不崩潰）
9. **Hybrid Search 設計精良** — BM25 + Vector 混合搜尋支援 keyword / semantic / 均衡三種模式
10. **batch_write_notes** — 單次索引多檔，比逐一呼叫效率高

---

## 附錄：審查涵蓋檔案清單

| 模組 | 檔案 | 行數（約） | 狀態 |
|------|------|-----------|------|
| 入口 | `main.py` | ~400 | ✅ 完整審查 |
| 設定 | `config.py` | ~380 | ✅ 完整審查 |
| MCP | `mcp_app/server.py` | ~730 | ✅ 完整審查 |
| 服務 | `services/vault.py` | ~450 | ✅ 完整審查 |
| 服務 | `services/scheduler.py` | ~500 | ✅ 部分審查 |
| 服務 | `services/auto_scheduler.py` | ~480 | ✅ 完整審查 |
| 服務 | `services/setup.py` | ~300 | ✅ 部分審查 |
| 服務 | `services/git_service.py` | ~100 | ✅ 完整審查 |
| 服務 | `services/knowledge_extractor.py` | ~150 | ✅ 完整審查 |
| 核心 | `core/indexer.py` | ~200 | ✅ 完整審查 |
| 核心 | `core/retriever.py` | ~200 | ✅ 完整審查 |
| 核心 | `core/vectorstore.py` | ~70 | ✅ 完整審查 |
| 核心 | `core/embeddings.py` | ~40 | ✅ 完整審查 |
| 核心 | `core/migration.py` | ~100 | ✅ 完整審查 |
| 工具 | `tools/registry.py` | ~200 | ✅ 完整審查 |
| CLI | `cli/repl.py` | ~600 | ✅ 部分審查 |
| 測試 | `tests/` (11 files) | — | ✅ 確認存在 |
