---
type: system
domain: architecture
created: 2026.04.01
last_updated: 2026.04.01
ai_summary: "AI Memory Vault 架構重構方案：程式碼與內容分離，建立通用初始框架"
tags: [architecture, refactor, setup]
---

# AI Memory Vault — 架構重構方案

> **目標**：將程式碼（AI_Engine）與內容（Vault）分離，建立一個乾淨的初始框架供任何使用者發展。

---

## 1. 新架構總覽

```
AI-Memory-Vault/
├── AI_Engine/              → Python RAG 引擎（程式碼）
│   ├── agents/             → LangChain Agent 定義
│   ├── api/                → FastAPI 服務 + Channel 整合
│   ├── cli/                → CLI REPL 介面
│   ├── core/               → 核心模組（embedding/retriever/vectorstore）
│   ├── services/           → 業務邏輯服務層
│   ├── tools/              → MCP 工具實作
│   ├── docs/               → 引擎技術文件
│   ├── config.py           → 設定管理
│   ├── main.py             → 主入口
│   ├── mcp_server.py       → MCP Server
│   ├── requirements.txt    → 依賴清單
│   ├── .env.example        → 環境變數範本
│   └── auto_sync.ps1       → 自動同步腳本
│
└── Vault/                  → 知識庫內容
    ├── _system/            → AI 導航層（系統文件）
    ├── work/               → 工作域（以公司/組織分類）
    │   └── _shared/        → 跨組織共用資源（snippets/skills）
    ├── life/               → 生活域（日記/學習/目標/靈感）
    ├── knowledge/          → 永久知識卡片（萃取後概念）
    ├── templates/          → 模板系統
    │   ├── agents/         → Agent 角色定義
    │   ├── projects/       → 專案類型模板
    │   └── sections/       → Vault 區域結構模板
    └── attachments/        → 附件存放
```

---

## 2. 目錄責任說明

### 2.1 AI_Engine（程式碼層）

| 目錄/檔案 | 責任 | 對外介面 |
|-----------|------|---------|
| `core/` | 嵌入模型、向量庫、檢索器 | `get_embeddings()`, `get_vectorstore()` |
| `services/` | 業務邏輯（VaultService） | `search()`, `read_note()`, `write_note()` |
| `tools/` | MCP 工具實作 | search, read, write, sync |
| `api/` | REST API + Channel 整合 | FastAPI `/chat`, `/search` |
| `cli/` | 命令列 REPL | `python main.py --mode cli` |
| `mcp_server.py` | MCP 通道 | `python main.py --mode mcp` |
| `config.py` | 設定管理 | `VAULT_ROOT`, `CHROMA_DIR` |

### 2.2 Vault（內容層）

| 目錄 | 責任 | 使用者操作 |
|------|------|-----------|
| `_system/` | AI Session 導航、交接、待辦 | AI 自動讀取，使用者可編輯 |
| `work/` | 工作筆記、專案、規則 | 依公司/組織建立子目錄 |
| `work/_shared/` | 跨組織共用內容 | snippets, skills, tech-stack |
| `life/` | 個人日記、學習、目標 | 依時間/主題組織 |
| `knowledge/` | 萃取後的永久知識卡片 | 概念驅動，去脈絡化 |
| `templates/` | 新內容的標準模板 | Agent 建立新檔案時參考 |
| `attachments/` | 圖片、PDF 等附件 | 與筆記分離存放 |

---

## 3. 初始框架（空白 Vault）

供新使用者 clone 後立即使用的乾淨結構：

```
Vault/
├── _system/
│   ├── CLAUDE.md           → AI 入口指令（參考模板）
│   ├── vault-nav.md        → 導航地圖（空白）
│   ├── action-register.md  → 待辦總表（空白）
│   ├── handoff.md          → Session 交接（空白）
│   └── AGENTS.md           → 架構文件（空白）
│
├── work/
│   ├── _shared/
│   │   ├── index.md        → 共用資源入口
│   │   ├── skills/         → AI 技能檔（空）
│   │   ├── snippets/       → 程式碼片段（空）
│   │   └── tech-stack/     → 技術棧筆記（空）
│   └── MY_WORKSPACE/       → 範例工作空間（可刪除/重命名）
│       ├── index.md        → 工作空間入口
│       ├── rules/          → 編碼規範
│       ├── projects/       → 專案筆記
│       ├── meetings/       → 會議紀錄
│       └── working-context/ → 當前工作上下文
│
├── life/
│   ├── index.md            → 生活域入口
│   ├── journal/            → 日記（空）
│   ├── learning/           → 學習筆記（空）
│   │   └── index.md
│   ├── goals/              → 目標管理（空）
│   └── ideas/              → 靈感收集（空）
│
├── knowledge/
│   └── index.md            → 知識卡片入口
│
├── templates/
│   ├── index.md            → 模板系統主索引
│   ├── agents/             → Agent 角色模板（10 個）
│   ├── projects/           → 專案類型模板（3 類）
│   └── sections/           → 區域結構模板（9 類）
│
└── attachments/
    └── .gitkeep
```

---

## 4. 剝離方案

### 4.1 需要移動的檔案

| 來源（現況） | 目標（新架構） |
|-------------|---------------|
| `_AI_Engine/` | `AI_Engine/` |
| `_system/` | `Vault/_system/` |
| `work/` | `Vault/work/` |
| `life/` | `Vault/life/` |
| `knowledge/` | `Vault/knowledge/` |
| `templates/` | `Vault/templates/` |
| `attachments/` | `Vault/attachments/` |
| `.github/` | 保留在根目錄 |
| `.vscode/` | 保留在根目錄 |
| `.gitignore` | 保留在根目錄 |
| `README.md` | 保留在根目錄（更新內容） |

### 4.2 需要修改的程式碼

| 檔案 | 修改項目 |
|------|---------|
| `AI_Engine/config.py` | `VAULT_ROOT` 改為 `../Vault` |
| `AI_Engine/services/vault_service.py` | 路徑調整 |
| `.vscode/mcp.json` | 工作目錄調整 |
| `.github/copilot-instructions.md` | 路徑說明更新 |

### 4.3 執行步驟

```powershell
# 1. 建立新目錄結構
New-Item -ItemType Directory -Path "AI_Engine" -Force
New-Item -ItemType Directory -Path "Vault" -Force

# 2. 移動 AI_Engine（程式碼）
Move-Item -Path "_AI_Engine\*" -Destination "AI_Engine\" -Force
Remove-Item -Path "_AI_Engine" -Force

# 3. 移動 Vault 內容
Move-Item -Path "_system" -Destination "Vault\" -Force
Move-Item -Path "work" -Destination "Vault\" -Force
Move-Item -Path "life" -Destination "Vault\" -Force
Move-Item -Path "knowledge" -Destination "Vault\" -Force
Move-Item -Path "templates" -Destination "Vault\" -Force
Move-Item -Path "attachments" -Destination "Vault\" -Force

# 4. 更新 config.py 中的 VAULT_ROOT
# （需手動編輯）
```

---

## 5. 設定檔調整

### 5.1 config.py 修改

```python
# 舊：
VAULT_ROOT = Path( __file__ ).resolve().parent.parent

# 新：
VAULT_ROOT = Path( __file__ ).resolve().parent.parent / "Vault"
```

### 5.2 .vscode/mcp.json 修改

```json
{
  "servers": {
    "ai-memory-vault": {
      "command": "python",
      "args": ["main.py", "--mode", "mcp"],
      "cwd": "${workspaceFolder}/AI_Engine"
    }
  }
}
```

---

## 6. 給新使用者的 Quick Start

1. **Clone 專案**
   ```bash
   git clone https://github.com/xxx/AI-Memory-Vault.git
   cd AI-Memory-Vault
   ```

2. **設定環境**
   ```bash
   cd AI_Engine
   cp .env.example .env
   # 編輯 .env 填入 API Keys
   pip install -r requirements.txt
   ```

3. **啟動 MCP Server**
   ```bash
   python main.py --mode mcp
   ```

4. **開始使用**
   - 在 `Vault/work/` 建立你的工作空間
   - 參考 `Vault/templates/` 的模板
   - 使用 MCP 工具 `write_note`, `search_vault` 操作知識庫

---

## 7. 初始框架 vs 完整範例

| 版本 | 內容 | 適用對象 |
|------|------|---------|
| **初始框架** | 空白 Vault + 完整 AI_Engine | 新使用者 |
| **完整範例** | 包含 CHINESEGAMER/LIFEOFDEVELOPMENT 範例 | 學習參考 |

建議：
- 發布時提供 **初始框架** 版本（`main` branch）
- 範例內容放在獨立 branch 或 `/examples/` 目錄

---

## 附錄 A：_system 核心文件說明

| 檔案 | 用途 | Session 載入順序 |
|------|------|:---------------:|
| `CLAUDE.md` | AI 入口指令 | Step 1 |
| `vault-nav.md` | 導航地圖 | Step 2 |
| `action-register.md` | 待辦總表 | Step 3 |
| `handoff.md` | Session 交接 | Step 4 |
| `AGENTS.md` | 架構文件 | 需要時查閱 |

---

## 附錄 B：Vault 路徑規則

| 內容類型 | 正確路徑 |
|---------|---------|
| 公司專案筆記 | `Vault/work/{COMPANY}/projects/{Project}/` |
| 編碼規範 | `Vault/work/{COMPANY}/rules/` |
| 會議紀錄 | `Vault/work/{COMPANY}/meetings/` |
| 共用 Snippets | `Vault/work/_shared/snippets/` |
| 永久知識卡片 | `Vault/knowledge/` |
| 日記 | `Vault/life/journal/` |
| 學習筆記 | `Vault/life/learning/` |
