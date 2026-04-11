# Transport 層 API Map

> **檔案**：`main.py` / `mcp_app/server.py` / `mcp_app/utils.py` / `cli/*.py`
> **用途**：入口分發、MCP Server 生命週期管理、CLI 互動介面
> **最後更新**：2026.04.10

---

## 1. 模組概覽

| 模組 | 檔案 | 職責 | 對外方法數 |
|------|------|------|-----------|
| main | `main.py` | 三模式入口 + 依賴檢查 | 1 |
| server | `mcp_app/server.py` | FastMCP Server + lifespan + hook 管理 | 3 |
| utils | `mcp_app/utils.py` | stdout 重導向 + MCP tool 裝飾器 | 1 |
| registry | `cli/registry.py` | CLI 工具宣告式登記表 | — |
| repl | `cli/repl.py` | 互動式 CLI 介面 | 2 |

---

## 2. main.py — 入口程式

> 依賴檢查 → 參數解析 → 模式分發

### 2.1 啟動模式

```
main.py --mode mcp       → run_mcp_server()       [預設]
main.py --mode cli       → VaultRepl.run()
main.py --mode api       → run_mcp_sse_server()   [SSE port 8765]
main.py --scheduler      → AutoScheduler.block()
main.py --run-once       → AutoScheduler.run_once()
main.py --setup          → SetupService.run_setup()
```

### 2.2 函式

| 函式 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `main()` | — | `None` | 主入口：依賴檢查→參數解析→模式分發 |
| `_find_missing_packages()` | — | `list[str]` | 掃描缺少的 pip 套件 |
| `_ask_install_gui(iMissing)` | missing list | `bool\|None` | tkinter 彈窗詢問安裝 |
| `_check_and_install_deps()` | — | `None` | 啟動前依賴自動檢查安裝 |
| `_detect_frozen_mode()` | — | `None` | PyInstaller 打包後自動設定模式 |

---

## 3. mcp_app/server.py — MCP Server

> FastMCP stdio/SSE server 建立、lifespan 管理、工具註冊、instructions 注入

### 3.1 模組級物件

| 名稱 | 型別 | 說明 |
|------|------|------|
| `mcp` | `FastMCP` | MCP Server 實例（全域 entry point） |

### 3.2 公開函式

| 函式 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `run_mcp_server()` | — | `None` | 啟動 MCP stdio 伺服器 |
| `run_mcp_sse_server(iHost, iPort)` | host, port | `None` | 啟動 MCP SSE 伺服器（uvicorn） |

### 3.3 內部函式

| 函式 | 說明 |
|------|------|
| `_get_scheduler()` | 取得 lifespan 初始化的 SchedulerService 單例 |
| `_get_instinct()` | 取得 lifespan 初始化的 InstinctService 單例 |
| `_load_vault_instructions()` | 載入 `_config/` 中 `inject:true` 的 .md 作為 MCP instructions |
| `_on_vault_write(iRelPath)` | 寫入後 hook：auto-learn + instinct cache 失效 |
| `_register_write_hooks()` | 啟動時註冊 hooks |
| `_unregister_write_hooks()` | 關閉時移除 hooks |
| `_provision_org_skeleton()` | 確保組織目錄骨架存在 |

### 3.4 Lifespan 流程

```
啟動 (startup)
    1. ConfigManager.load() → AppConfig
    2. VaultService.initialize(config)
    3. _provision_org_skeleton()
    4. _register_write_hooks()
    5. _load_vault_instructions() → 注入 MCP instructions
    6. 建立 SchedulerService / InstinctService 單例
    7. 註冊 7 個 tool 模組（40 tools）
    8. 日誌記錄工具數

關閉 (shutdown)
    1. _unregister_write_hooks()
```

### 3.5 Post-Write Hook — `_on_vault_write`

| 偵測路徑 | 行為 |
|---------|------|
| `conversations/` | 觸發 auto-learn pipeline（`_auto_learn_instincts`） |
| `knowledge/` | 日誌記錄 |
| 任何寫入 | 使 InstinctService 搜尋快取失效 |

### 3.6 SSE Server

```python
run_mcp_sse_server("0.0.0.0", 8765)
# → FastMCP.sse_app() 取得 Starlette app
# → uvicorn.run(app, host, port)
# → Client 連線 http://host:8765/sse
```

---

## 4. mcp_app/utils.py — MCP 工具函式

### 4.1 StdoutToStderr（Context Manager）

> 重導向 stdout → stderr，保護 MCP JSON-RPC 通道不被 ML 模型的 print 汙染

| 方法 | 說明 |
|------|------|
| `__enter__` | 重導向 stdout→stderr（Python 層 + OS fd 層雙重保護） |
| `__exit__` | 還原 |

### 4.2 suppress_stdout（裝飾器）

```python
@suppress_stdout
async def my_mcp_tool(param: str) -> str:
    ...
```

功能：
- 自動包裝 `StdoutToStderr`
- 攔截未預期例外，轉為 `"Error: {message}"` 字串回傳
- 所有 MCP tool 函式必須使用此裝飾器

---

## 5. cli/registry.py — CLI 工具登記表

> 宣告式 CLI 工具描述，自動產生 alias/help/選單/Tab 補全

### 5.1 資料結構

**ToolParam**：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `name` | `str` | 參數名稱 |
| `prompt` | `str` | 互動式提示文字 |
| `kind` | `str` | 參數類型（`"text"` / `"bool"` / `"choice"`） |
| `required` | `bool` | 是否必填 |
| `default` | `str` | 預設值 |

**ToolEntry**：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `name` | `str` | 指令名稱 |
| `alias` | `str` | 簡寫別名 |
| `group` | `str` | 分組（files/projects/reviews/ai/other） |
| `icon` | `str` | Emoji 圖示 |
| `menu_label` | `str` | 選單顯示文字 |
| `help_line` | `str` | 一句話說明 |
| `params` | `list[ToolParam]` | 參數清單 |
| `invoke` | `Optional[Callable]` | 執行函式 |

### 5.2 資料

`TOOL_REGISTRY: list[ToolEntry]` — 全部 CLI 工具清單（~20 entries）

分組：`files` / `projects` / `reviews` / `ai` / `other`

---

## 6. cli/repl.py — CLI REPL

> 互動式 CLI 介面，支援指令列模式和 questionary 選單模式

**相依性**：`cli.registry`, `services.scheduler`, `services.vault`

### VaultRepl

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `__init__(iConfig)` | AppConfig | — | 建立 REPL（含 readline/Tab 補全設定） |
| `run()` | — | `None` | 啟動指令列模式（`vault>` 提示符） |
| `run_menu()` | — | `None` | 啟動 questionary 選單模式 |

---

## 7. 設計注意事項

### 7.1 三模式分離

- **stdio MCP**（預設）：VS Code MCP Client 連線用
- **SSE MCP**（`--mode api`）：HTTP/SSE 遠端連線用（Docker / 雲端）
- **CLI**（`--mode cli`）：開發除錯用

### 7.2 PyInstaller 打包

`_detect_frozen_mode()` 在 frozen 環境自動設定 `--mode mcp`，確保 exe 啟動即為 MCP Server。

### 7.3 依賴自動安裝

首次執行時 `_check_and_install_deps()` 掃描缺失套件，彈出 tkinter 對話框詢問是否安裝。安裝完成後重啟程式。
