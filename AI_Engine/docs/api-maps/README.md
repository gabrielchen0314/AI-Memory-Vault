# AI Memory Vault — API Map 索引

> **用途**：AI 助手快速理解系統結構的接口索引，無需逐一讀取原始碼
> **最後更新**：2026.04.10
> **版本**：v3.6.0（40 MCP Tools / 237 Tests）

---

## 四層架構

```
┌─────────────────────────────────────────────┐
│  Transport Layer（MCP / CLI / SSE）          │
│  main.py → mcp_app/server.py / cli/repl.py  │
├─────────────────────────────────────────────┤
│  MCP Tool Layer（40 tools，7 模組）           │
│  mcp_app/tools/*.py                          │
├─────────────────────────────────────────────┤
│  Service Layer                               │
│  services/vault.py (Facade) + 8 services     │
├─────────────────────────────────────────────┤
│  Core Layer                                  │
│  core/*.py（embedding, indexer, vectorstore） │
└─────────────────────────────────────────────┘
```

---

## 分層索引

| # | 層級 | 檔案 | 模組數 | 對外方法數 |
|---|------|------|--------|-----------|
| 1 | [設定層](01-config_APIMap.md) | `config.py` | 1 | 3 (ConfigManager) + 10 dataclass + 12 VaultPaths 方法 |
| 2 | [Core 層](02-core_APIMap.md) | `core/*.py` | 7 | 17 |
| 3 | [Service 層](03-services_APIMap.md) | `services/*.py` | 9 | 55 |
| 4 | [MCP Tool 層](04-mcp-tools_APIMap.md) | `mcp_app/tools/*.py` | 7 | 40 MCP tools |
| 5 | [Transport 層](05-transport_APIMap.md) | `main.py` / `mcp_app/server.py` / `cli/*` | 4 | 6 |

---

## 全模組清單

| 模組 | 職責 | 入口檔案 | 所屬層 |
|------|------|---------|--------|
| **config** | 設定管理（dataclass + config.json） | `config.py` | 設定 |
| **core/embeddings** | 嵌入模型（HuggingFace 單例） | `core/embeddings.py` | Core |
| **core/errors** | VaultError 例外階層 | `core/errors.py` | Core |
| **core/frontmatter** | YAML Frontmatter 解析/渲染 | `core/frontmatter.py` | Core |
| **core/indexer** | .md → ChromaDB 增量同步 | `core/indexer.py` | Core |
| **core/logger** | vault.* 命名空間日誌 | `core/logger.py` | Core |
| **core/migration** | 索引設定遷移管理 | `core/migration.py` | Core |
| **core/retriever** | 語意搜尋（Hybrid BM25+Vector） | `core/retriever.py` | Core |
| **core/vectorstore** | ChromaDB + RecordManager 單例 | `core/vectorstore.py` | Core |
| **services/vault** | 業務邏輯 Facade（唯一入口） | `services/vault.py` | Service |
| **services/backup** | ChromaDB ZIP 備份 + 清理 | `services/backup.py` | Service |
| **services/instinct** | 直覺卡片 CRUD + 搜尋 + 復盤 | `services/instinct.py` | Service |
| **services/scheduler** | 排程生成（daily/weekly/monthly） | `services/scheduler.py` | Service |
| **services/auto_scheduler** | APScheduler cron 觸發層 | `services/auto_scheduler.py` | Service |
| **services/agent_router** | Agent 模板掃描 + 分發 | `services/agent_router.py` | Service |
| **services/git_service** | Vault git 自動 commit | `services/git_service.py` | Service |
| **services/knowledge_extractor** | 對話 → 知識卡片萃取 | `services/knowledge_extractor.py` | Service |
| **services/setup** | 首次執行初始化精靈 | `services/setup.py` | Service |
| **services/token_counter** | 輕量 Token 估算 | `services/token_counter.py` | Service |
| **mcp_app/tools/vault_tools** | 筆記 CRUD + 搜尋（10 tools） | `mcp_app/tools/vault_tools.py` | MCP Tool |
| **mcp_app/tools/scheduler_tools** | 排程生成（10 tools） | `mcp_app/tools/scheduler_tools.py` | MCP Tool |
| **mcp_app/tools/project_tools** | 專案管理（3 tools） | `mcp_app/tools/project_tools.py` | MCP Tool |
| **mcp_app/tools/todo_tools** | Todo 管理（3 tools） | `mcp_app/tools/todo_tools.py` | MCP Tool |
| **mcp_app/tools/index_tools** | 索引管理（5 tools） | `mcp_app/tools/index_tools.py` | MCP Tool |
| **mcp_app/tools/agent_tools** | Agent/Skill 管理（4 tools） | `mcp_app/tools/agent_tools.py` | MCP Tool |
| **mcp_app/tools/instinct_tools** | 直覺記憶（5 tools） | `mcp_app/tools/instinct_tools.py` | MCP Tool |
| **mcp_app/server** | FastMCP Server + lifespan | `mcp_app/server.py` | Transport |
| **mcp_app/utils** | stdout 重導向 + 裝飾器 | `mcp_app/utils.py` | Transport |
| **cli/registry** | CLI 工具登記表 | `cli/registry.py` | Transport |
| **cli/repl** | 互動式 CLI 介面 | `cli/repl.py` | Transport |
| **main** | CLI/API/MCP 三模式入口 | `main.py` | Transport |

---

## 設計模式速查

| 模式 | 應用位置 | 說明 |
|------|---------|------|
| **Facade** | `VaultService` | 統一業務入口，隱藏 _vault/ 子模組 |
| **Singleton (lru_cache)** | embeddings, vectorstore | 全域唯一實例 |
| **Observer (Hook)** | `VaultService.register_post_write_hook` | 寫入後觸發回呼鏈 |
| **Registry** | `TOOL_REGISTRY`, `TASK_REGISTRY` | 宣告式工具/任務登記 |
| **Classmethod API** | `VaultService`, `GitService`, `ConfigManager` | 無需實例化 |
| **Lazy Import** | core 層 ML 依賴 | torch/transformers 在函式內 import |

---

## 相依性圖

```
main.py
├── mcp_app/server.py
│   ├── services/vault.py (Facade)
│   │   ├── core/indexer.py → core/vectorstore.py → core/embeddings.py
│   │   ├── core/retriever.py → core/vectorstore.py
│   │   ├── core/errors.py
│   │   └── services/_vault/*.py
│   ├── services/scheduler.py → services/vault.py
│   ├── services/instinct.py → services/vault.py
│   ├── services/backup.py
│   └── mcp_app/tools/*.py → services/*
├── services/auto_scheduler.py → services/scheduler.py + backup.py
└── cli/repl.py → services/vault.py + scheduler.py
```

---

## 核心依賴套件

| 套件 | 用途 |
|------|------|
| `mcp[cli]` | FastMCP Server 框架 |
| `langchain-chroma` | ChromaDB 向量資料庫 |
| `langchain-huggingface` | HuggingFace 嵌入模型 |
| `langchain-community` | BM25 Retriever |
| `langchain-text-splitters` | Markdown 文字切塊 |
| `apscheduler` | 背景排程 |
| `uvicorn` + `starlette` | SSE HTTP 伺服器 |
| `filelock` | 跨行程檔案鎖 |
| `pyyaml` | YAML Frontmatter 解析 |
| `rank_bm25` | BM25 排序演算法 |
