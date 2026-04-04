---
type: index
domain: meta
category: rules-index
workspace: LIFEOFDEVELOPMENT
created: 2026.03.29
last_updated: 2026.03.29
tags: [index, rules, LIFEOFDEVELOPMENT]
ai_summary: "LIFEOFDEVELOPMENT 工作域的規則索引，涵蓋 Python 編碼規範、AI Engine 架構規範、專案 API Map 同步規則。"
---

# 📋 Rules Index — LIFEOFDEVELOPMENT

> 所有工作規範的單一索引，涵蓋 Python 應用程式開發、AI 引擎架構、工作流程

---

## 規則清單

| # | 檔案 | 領域 | 嚴重度 | 適用技術 | 說明 |
|---|------|------|:------:|---------|------|
| 01 | [[01-python-coding-style 1]] | Coding | Must | Python | Python 命名規範、模組結構、型別標注、GC 防護 |
| 02 | [[02-ai-engine-architecture]] | Architecture | Must | Python, LangChain, FastAPI | AI Engine 模組責任邊界、Agent 模式、工具封裝規範 |
| 03 | [[03-project-api-map-sync]] | Workflow | Must | Python, C#, Lua, TypeScript | 專案知識庫建立時同步在原始碼目錄建立 API Map |

---

## 依開發領域分類

### 🐍 Python 應用程式
- [[01-python-coding-style 1]] — 命名前綴、模組結構、例外處理

### 🧠 AI 引擎架構
- [[02-ai-engine-architecture]] — 四層架構、LangChain Tool、Agent ABC、MCP Protocol

### 📋 工作流程
- [[03-project-api-map-sync]] — Vault 知識庫 ↔ 專案原始碼 API Map 雙向同步

---

## 依 Agent 對應

| Agent | 相關 Rule |
|-------|----------|
| `@CodeReviewer` | 01 |
| `@Architect` | 01, 02, 03 |
| `@BuildErrorResolver` | 01, 02 |
| `@RefactorCleaner` | 01, 02 |
| `@SecurityReviewer` | 01 |
| `@DocUpdater` | 03 |

---

## ⚠️ 命名風格速查（Python）

| 元素 | Python（LIFEOFDEVELOPMENT） |
|------|:-------------------------:|
| 成員變數 | `m_` 前綴（`self.m_Counter`） |
| 參數 | `i` 前綴（`iFilePath`） |
| 區域變數 | `_` 前綴（`_Result`, `_AbsPath`） |
| 常數 | 全大寫（`MAX_RETRIES`, `VAULT_ROOT`） |
| 例外變數 | `_Ex`（`except Exception as _Ex`） |
| 類別 | PascalCase（`VaultIndexer`, `MemoryAgent`） |
| 函式/方法 | snake_case（`sync_notes`, `read_note`） |

---

*最後更新：2026.03.29*
