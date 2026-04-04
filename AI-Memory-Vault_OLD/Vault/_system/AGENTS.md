---
type: system
domain: vault-architecture
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "Vault 架構文件（v3.2）：全域模板系統、VaultService 重構後 _AI_Engine v2.1（14 模組），vault-nav.md 同步規則補齊"
tags: [system, vault, architecture, agents]
---

# AGENTS.md

> 📐 **本檔案是 Vault 的架構文件，供 AI Coding Agent 理解整個知識庫的結構。**
> ⚠️ 此文件描述的是**實際存在**的結構。標記 `📋 擴展指引` 的部分代表未來新增內容時應遵循的路徑。

---

## 1. Vault 架構總覽

```
AI-Memory-Vault/
├── _system/              → AI 導航層（5 個核心文件）
├── _AI_Engine/           → Python RAG 引擎 v2.1（14 模組，含 services/）
├── work/                 → 工作域（以公司分類）
│   ├── _shared/          → 跨公司共用資源（skills / snippets / tech-stack）
│   ├── CHINESEGAMER/     → 上班的地方（遊戲開發 + Extension）
│   └── LIFEOFDEVELOPMENT/ → 自己的公司專案
├── life/                 → 生活域（日記、學習、目標、靈感）
├── knowledge/            → 永久知識卡片（萃取後的概念）
├── .ai_memory/           → 記憶系統（Instinct + Session Log）
├── attachments/          → 附件
└── templates/            → 🏗️ 全域模板系統
    ├── index.md          → ⭐ 模板主索引（所有 Agent 必讀）
    ├── agents/           → 10 個 Agent .md（唯一真相來源）
    ├── projects/         → 專案知識庫模板（python-app / unity-game / vscode-ext）
    └── sections/         → Vault 區域結構模板（9 類型）
```

> ⚠️ 工作域以公司分類，共用資源放在 `work/_shared/`。每家公司都有對應的 `rules/` 編碼規範。

---

## 2. 工作空間詳細結構

### 共用資源 (`work/_shared/`)

```
work/_shared/
├── index.md                            ← ⭐ 共用資源入口
├── skills/                             ← AI 技能檔（📋 新增 SKILL.md 放這裡）
├── snippets/                           ← 常用程式碼片段
│   ├── csharp/
│   ├── lua/
│   └── typescript/
└── tech-stack/                         ← 技術棧知識庫（📋 新增技術筆記放這裡）
```

### CHINESEGAMER (`work/CHINESEGAMER/`)

```
work/CHINESEGAMER/
├── index.md                            ← ⭐ 公司工作入口
├── rules/                              ← 編碼規範（10 條）
│   ├── index.md                        ← ⭐ 規則索引
│   ├── 01-csharp-coding-style.md       ← 🎮 C#
│   ├── 02-lua-coding-style.md          ← 🎮 Lua
│   ├── 03-protocol-implementation.md   ← 🎮 封包格式
│   ├── 04-viewref-binding.md           ← 🎮 UI 綁定
│   ├── 05-tag-system.md                ← 🎮 Tag + Bit Array
│   ├── 06-security-game.md             ← 🔒 遊戲安全
│   ├── 07-git-conventions.md           ← 📦 Git（遊戲端）
│   ├── 08-vscode-extension.md          ← 🔌 Extension 架構
│   ├── 09-obfuscation-guide.md         ← 🔌 混淆與驗證
│   └── 10-multi-project-git.md         ← 🔌 多專案 Git
├── projects/
│   └── SpinWithFriends/
│       ├── project-overview.md         ← Unity + XLua 架構總覽
│       ├── dev-progress.md             ← 開發進度 + BUG 清單
│       ├── lua-module-catalog.md       ← Lua 模組目錄
│       └── LoginMgr_APIMap.md          ← 登入系統 API Map
├── meetings/                           ← 會議紀錄（📋 格式參見 templates/sections/meeting/）
├── people/                             ← 人物檔案（📋 格式參見 templates/sections/people/）
└── working-context/                    ← 當前工作上下文
```

### LIFEOFDEVELOPMENT (`work/LIFEOFDEVELOPMENT/`)

```
work/LIFEOFDEVELOPMENT/
├── rules/                              ← 編碼規範（3 條）
│   ├── index.md                        ← ⭐ 規則索引
│   ├── 01-python-coding-style.md       ← 🐍 Python 命名規範
│   ├── 02-ai-engine-architecture.md    ← 🧠 AI Engine 四層架構規範
│   └── 03-project-api-map-sync.md      ← 📋 專案 API Map 同步規則
├── projects/
│   ├── AIMemoryVault/
│   │   ├── project-overview.md         ← 願景 + 四層架構 + Roadmap
│   │   ├── architecture.md             ← 模組責任表 + 資料流 + ADR（v2.1）
│   │   ├── dev-progress.md             ← 分階段進度 + 待辦 + BUG
│   │   ├── module-catalog.md           ← 14 模組目錄 + 對外 API（v2.1）
│   │   └── {Module}_APIMap.md          ← 📋 選用：單模組詳細 API
│   └── SpinWithFriends/
│       ├── project-overview.md         ← Unity + XLua 架構總覽
│       ├── dev-progress.md             ← 開發進度
│       ├── lua-module-catalog.md       ← Lua 模組目錄
│       └── LoginMgr_APIMap.md          ← 登入系統 API Map
└── working-context/                    ← 當前工作上下文
```

---

## 3. 全域模板系統 (`templates/`)

> ⭐ **主索引**：`templates/index.md`（所有 Agent 操作前必讀）

模板分為三大類：

### 3.1 Agent 角色模板 — `templates/agents/`

| Agent | 檔案 | 用途 |
|-------|------|------|
| Architect | `agents/architect.md` | 架構分析、技術決策 |
| Doc Updater | `agents/doc-updater.md` | 文檔更新與索引 |
| Code Reviewer | `agents/code-reviewer.md` | 程式碼審查 |
| Build Error Resolver | `agents/build-error-resolver.md` | 建置錯誤排除 |
| Git Committer | `agents/git-committer.md` | Git 操作規範 |
| Planner | `agents/planner.md` | 任務規劃 |
| Refactor Cleaner | `agents/refactor-cleaner.md` | 重構清理 |
| Security Reviewer | `agents/security-reviewer.md` | 安全審查 |
| TDD Guide | `agents/tdd-guide.md` | 測試驅動開發 |
| Learn Trigger | `agents/learn-trigger.md` | 學習觸發器 |

### 3.2 專案類型模板 — `templates/projects/`

| 類型 | 檔案 | 識別特徵 |
|------|------|---------| 
| Python App | `projects/python-app/TEMPLATE.md` | `requirements.txt` / `.venv` / `.py` |
| Unity Game | `projects/unity-game/TEMPLATE.md` | `Assets/` / `.unity` / `.cs` + `.lua` |
| VS Code Extension | `projects/vscode-ext/TEMPLATE.md` | `package.json` + `contributes` |

### 3.3 Vault 區域模板 — `templates/sections/`

| 區域 | 模板 | 適用路徑 |
|------|------|---------|
| 公司工作域 | `sections/company-workspace/TEMPLATE.md` | `work/{COMPANY}/` |
| 規則集 | `sections/rules/TEMPLATE.md` | `work/{COMPANY}/rules/` |
| 會議紀錄 | `sections/meeting/TEMPLATE.md` | `work/{COMPANY}/meetings/` |
| 人物檔案 | `sections/people/TEMPLATE.md` | `work/{COMPANY}/people/` |
| 日記 / 週回顧 | `sections/journal/TEMPLATE.md` | `life/journal/` |
| 學習筆記 | `sections/learning/TEMPLATE.md` | `life/learning/` |
| 目標管理 | `sections/goals/TEMPLATE.md` | `life/goals/` |
| 靈感速記 | `sections/ideas/TEMPLATE.md` | `life/ideas/` |
| 知識卡片 | `sections/knowledge-card/TEMPLATE.md` | `knowledge/` |

---

## 4. 🔒 全域模板檢查規則（所有 Agent 必須遵守）

> 此規則優先於所有 Agent 的個別行為。**任何 Agent** 在 Vault 任意位置建立新內容前，都必須執行此流程。

### 流程

```
Agent 要在 Vault 建立新內容
        │
        ▼
  ┌──────────────────────────────┐
  │ 1. 判斷目標路徑屬於哪種區域    │
  │ 2. 查找對應模板：              │
  │    • templates/sections/      │
  │    • templates/projects/      │
  └──────────────┬───────────────┘
                 │
         ┌───────┴───────┐
         │ 模板存在？      │
         ├── YES ────────► 依模板格式建立（Frontmatter + 命名 + 章節）
         └── NO ─────────► 進入「草案提案」流程
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │ 1. 草擬模板結構（參考最接近的   │
                    │    既有模板延伸）               │
                    │ 2. 向使用者展示                 │
                    │ 3. ⏸️ WAIT FOR CONFIRM         │
                    │ 4. 使用者確認後：               │
                    │    a) 儲存為正式模板             │
                    │       templates/sections/{type}/ │
                    │    b) 依模板建立內容             │
                    │ 5. 使用者拒絕 → 本次跳過         │
                    └──────────────────────────────┘
```

### 路徑 → 模板對應表

| 目標路徑 | 對應模板 |
|----------|---------|
| `work/{NEW_COMPANY}/` | `sections/company-workspace/` |
| `work/{COMPANY}/rules/` | `sections/rules/` |
| `work/{COMPANY}/meetings/` | `sections/meeting/` |
| `work/{COMPANY}/people/` | `sections/people/` |
| `work/{COMPANY}/projects/{PROJECT}/` | `projects/{type}/` |
| `life/journal/` | `sections/journal/` |
| `life/learning/` | `sections/learning/` |
| `life/goals/` | `sections/goals/` |
| `life/ideas/` | `sections/ideas/` |
| `knowledge/` | `sections/knowledge-card/` |
| 其他未知路徑 | → 草案提案流程 |

---

## 5. 生活域結構

```
life/
├── index.md
├── learning/
│   └── index.md
├── journal/
├── goals/
└── ideas/
```

---

## 6. 知識庫與記憶系統

### 知識庫 (`knowledge/`)

```
knowledge/
├── index.md
└── {concept-name}.md             ← 📋 永久知識卡片（萃取後的概念）
```

> **邊界定義**：`knowledge/` 存放**經過萃取的永久概念卡片**。學習過程中的筆記放在 `life/learning/`。

### 記憶系統 (`.ai_memory/`)

```
.ai_memory/
├── instincts/
│   └── {domain}-{name}.md
├── instinct_config.json
├── sequence.txt
└── logs/                         ← Session Log & Chat History（唯一存放處）
    ├── session-log-YYYY-MM-DD.jsonl
    └── chat-history-YYYY-MM-DD_{標題}.md
```

---

## 7. Frontmatter 規範

### 所有筆記必要欄位

```yaml
---
type: [類型]
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
tags: [標籤列表]
ai_summary: "一句話摘要"
---
```

### Rule

```yaml
---
type: rule
domain: coding | networking | ui | system | security | workflow | architecture
category: [具體分類]
workspace: CHINESEGAMER | LIFEOFDEVELOPMENT | _shared
applies_to: [csharp, lua, typescript, python, ...]
severity: critical | must | should | nice-to-have
ai_summary: "..."
---
```

### Project（overview）

```yaml
---
type: project
workspace: {COMPANY}
domain: {domain}
status: planning | active | on-hold | completed
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "..."
---
```

### Architecture

```yaml
---
type: architecture
project: {ProjectName}
workspace: {COMPANY}
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "..."
---
```

### Dev Progress

```yaml
---
type: dev-progress
project: {ProjectName}
workspace: {COMPANY}
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "..."
---
```

### Module Catalog

```yaml
---
type: module-catalog
project: {ProjectName}
workspace: {COMPANY}
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "..."
---
```

---

## 8. 檔案命名規則

| 類型 | 格式 | 範例 |
|------|------|------|
| Rule | `NN-{kebab-case}.md` | `01-csharp-coding-style.md` |
| Project 總覽 | `project-overview.md` | — |
| 架構文件 | `architecture.md` | — |
| 開發進度 | `dev-progress.md` | — |
| 模組目錄 | `module-catalog.md` （Unity：`lua-module-catalog.md`） | — |
| API Map | `{ModuleName}_APIMap.md`（Vault）/ `docs/API_MAP.md`（原始碼） | `LoginMgr_APIMap.md` |
| Meeting | `YYYY-MM-DD-{主題}.md` | `2026-03-27-sprint-review.md` |
| ADR | `ADR-NNN-{title}.md` | `ADR-001-monorepo.md` |
| Journal | `YYYY-MM-DD.md` | `2026-03-29.md` |
| Learning | `YYYY-MM-DD-{type}-{title}.md` | `2026-03-29-book-clean-code.md` |
| Knowledge | `{kebab-case-concept}.md` | `rag-architecture.md` |
| Ideas | `YYYY-MM-DD-{title}.md` | `2026-03-29-ai-voice-assistant.md` |
| Goals | `YYYY-goals.md` / `YYYY-QN-review.md` | `2026-goals.md` |

**禁止**：檔名中不要有空格、不要用中文檔名

---

## 9. index.md 規範

每個資料夾**都必須有** `index.md`。AI 每次建立或刪除檔案時，必須同步更新。

---

## 10. Agent → Vault 路徑對應

| Agent | 主要操作路徑 | memory_categories | mcp_tools |
|-------|------------|-------------------|-----------| 
| `@Memory` | `chroma_db/`（向量庫） | work, life, knowledge | sync_vault, search_vault |
| `@Planner` | `work/*/projects/` | work, life, knowledge | search_vault |
| `@Architect` | `projects/`, `templates/`, `rules/` | work, knowledge | search_vault |
| `@CodeReviewer` | `rules/`（CHINESEGAMER 01~05,08；LIFEOFDEVELOPMENT 01,02） | work | search_vault |
| `@RefactorCleaner` | `rules/`, `work/*/projects/` | work | search_vault |
| `@LearnTrigger` | `.ai_memory/`, `knowledge/`, `life/learning/` | knowledge, work | search_vault, sync_vault |
| `@SecurityReviewer` | `rules/` 06, 09；LIFEOFDEVELOPMENT 01 | work | search_vault |
| `@GitCommitter` | `rules/` 07, 10 | work | search_vault |
| `@DocUpdater` | `work/*/projects/`, `life/`, `knowledge/`；Rule 03 API Map | work, life | search_vault |
| `@BuildErrorResolver` | `work/*/projects/`, `rules/` | work | search_vault |
| `@TddGuide` | `work/*/projects/`, `knowledge/` | work, knowledge | search_vault |

---

## 11. _AI_Engine 架構 (v2.1)

```
_AI_Engine/
├── config.py              ← 全域設定（Pydantic BaseSettings，.env 載入）
├── main.py                ← 入口（--mode cli | api | mcp）
├── mcp_server.py          ← MCP Server v2.1（FastMCP SDK，4 tools → VaultService）
├── auto_sync.ps1          ← Windows 排程腳本（每日 20:00）
├── requirements.txt
├── .env                   ← API Key + LLM_PROVIDER（不 commit）
├── .venv/                 ← Python 3.12.9 虛擬環境
├── docs/
│   └── API_MAP.md         ← 模組公開 API 速查手冊（Rule 03）
├── services/              ← ⭐ v2.1 新增：業務邏輯層
│   ├── __init__.py
│   └── vault_service.py   ← 統一入口：路徑驗證 + read/write/search/sync
├── core/
│   ├── embeddings.py      ← multilingual-MiniLM-L12-v2（50+ 語言，384 維）
│   ├── llm_factory.py     ← LLM 工廠（Ollama / Gemini 可插拔）
│   ├── vectorstore.py     ← ChromaDB + SQLRecordManager
│   ├── indexer.py         ← 掃描 → Frontmatter 解析 → 切塊 → 增量同步
│   └── retriever.py       ← Hybrid Search + Recency Bias
├── tools/                 ← LangChain Tool 薄封裝（全部委派 VaultService）
│   ├── sync.py, search.py, read.py, write.py
├── agents/
│   ├── base.py            ← ABC 介面
│   ├── memory_agent.py    ← 預設記憶 Agent（4 工具 + Core Memory 注入）
│   └── router.py          ← @mention 意圖路由器
├── api/
│   ├── app.py             ← FastAPI v2.1（/health, /sync, /search, /read, /write → VaultService）
│   └── schemas.py         ← Pydantic Request/Response（含 Read/Write 模型）
└── cli/
    └── repl.py            ← 互動終端（串流 + 工具呼叫 + 自動存檔）
```

### LLM 切換

```ini
LLM_PROVIDER=ollama     # 本地免費
LLM_PROVIDER=gemini     # Google Gemini API
```

---

## 12. ⚠️ 同步強制規則

> 以下情況**必須同時更新**：`/memories/repo/ai-memory-vault-progress.md`（Copilot 記憶）與 `_system/ai-engine-progress.md`

### 12.1 進度鏡像同步

| 觸發情況 | 需更新的內容 |
|----------|------------|
| 新開聊天視窗 | 讀取記憶確認進度，無需寫入 |
| 完成一個功能 | 更新進度清單（勾選 ✅） |
| 新增 Agent | Agent 表（第 10 節）|
| 新增專案類型模板 | `templates/projects/index.md` + 本文第 3.2 節 |
| 新增區域模板 | `templates/index.md` + 本文第 3.3 節 |
| 架構變更 | 第 2 節 + 第 11 節 |
| 進度更新 | `work/LIFEOFDEVELOPMENT/projects/AIMemoryVault/dev-progress.md` |

### 12.2 vault-nav.md 同步

> `_system/vault-nav.md` 是全域導航入口，橫跨整個 Vault。以下變更**必須同步更新** vault-nav.md 對應區塊。

| 觸發情況 | vault-nav.md 需更新的區塊 |
|----------|--------------------------|
| 新增 / 重命名專案 | 該公司的「專案」表格 |
| 新增 / 刪除公司 rules | 該公司的「規範」表格 |
| 新增 / 刪除公司工作域 | 工作域區段（新增整個公司區塊） |
| 模板系統結構變更 | 「模板系統」區段 |
| _system/ 檔案增減 | 「_system — AI 導航層」表格 |
| Vault 統計數字變動 | 「Vault 統計」表格 |

---

*最後更新：2026.03.29*
