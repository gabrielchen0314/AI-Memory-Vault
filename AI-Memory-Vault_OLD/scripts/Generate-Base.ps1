<#
.SYNOPSIS
    AI Memory Vault 初始框架生成腳本
.DESCRIPTION
    生成一個乾淨的空白 Vault 結構，供新使用者快速上手。
.PARAMETER OutputPath
    輸出目錄路徑（預設為當前目錄的 AI-Memory-Vault-Starter）
.NOTES
    @author gabrielchen
    @version 1.0
    @date 2026.04.01
#>

param(
    [string]$OutputPath = ".\AI-Memory-Vault"
)

$ErrorActionPreference = "Stop"

Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   AI Memory Vault — 初始框架生成器                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "輸出路徑: $OutputPath" -ForegroundColor Gray
Write-Host ""

# ── 建立目錄結構 ────────────────────────────────────────────
$_Directories = @(
    "Vault",
    "Vault\_system",
    "Vault\work",
    "Vault\work\_shared",
    "Vault\work\_shared\skills",
    "Vault\work\_shared\snippets",
    "Vault\work\_shared\snippets\csharp",
    "Vault\work\_shared\snippets\lua",
    "Vault\work\_shared\snippets\typescript",
    "Vault\work\_shared\tech-stack",
    "Vault\work\MY_WORKSPACE",
    "Vault\work\MY_WORKSPACE\rules",
    "Vault\work\MY_WORKSPACE\projects",
    "Vault\work\MY_WORKSPACE\meetings",
    "Vault\work\MY_WORKSPACE\working-context",
    "Vault\life",
    "Vault\life\journal",
    "Vault\life\learning",
    "Vault\life\goals",
    "Vault\life\ideas",
    "Vault\knowledge",
    "Vault\templates",
    "Vault\templates\agents",
    "Vault\templates\projects",
    "Vault\templates\sections",
    "Vault\attachments",
    ".vscode",
    ".github"
)

Write-Host "[1/3] 建立目錄結構..." -ForegroundColor Green

foreach( $_Dir in $_Directories )
{
    $_FullPath = Join-Path $OutputPath $_Dir
    New-Item -ItemType Directory -Path $_FullPath -Force | Out-Null
    Write-Host "  [+] $_Dir" -ForegroundColor DarkGray
}

# ── 建立基礎檔案 ────────────────────────────────────────────
Write-Host "`n[2/3] 建立基礎檔案..." -ForegroundColor Green

# README.md
$_ReadmeContent = @"
# AI Memory Vault

> 一個由 AI 驅動的個人知識管理系統，結合 RAG 技術實現智慧搜尋與記憶。

## 架構

``````
AI-Memory-Vault/
├── AI_Engine/          → Python RAG 引擎
└── Vault/              → 知識庫內容
    ├── _system/        → AI 導航層
    ├── work/           → 工作域
    ├── life/           → 生活域
    ├── knowledge/      → 知識卡片
    └── templates/      → 模板系統
``````

## 快速開始

1. **設定環境**
   ``````bash
   cd AI_Engine
   cp .env.example .env
   # 編輯 .env 填入 API Keys
   pip install -r requirements.txt
   ``````

2. **啟動 MCP Server**
   ``````bash
   python main.py --mode mcp
   ``````

3. **開始使用**
   - 在 ``Vault/work/`` 建立你的工作空間
   - 參考 ``Vault/templates/`` 的模板
   - 使用 MCP 工具操作知識庫

## MCP 工具

| 工具 | 用途 |
|------|------|
| ``search_vault`` | 搜尋知識庫（BM25 + 向量） |
| ``read_note`` | 讀取筆記內容 |
| ``write_note`` | 寫入/更新筆記 |
| ``sync_vault`` | 同步向量索引 |

## 文件

- [架構說明](docs/ARCHITECTURE-REFACTOR.md)
- [Vault 導航](_system/vault-nav.md)
"@
Set-Content -Path ( Join-Path $OutputPath "README.md" ) -Value $_ReadmeContent -Encoding UTF8

# .gitignore
$_GitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
.env

# AI Engine
AI_Engine/chroma_db/
AI_Engine/*.log
AI_Engine/*.sql

# IDE
.vscode/*
!.vscode/mcp.json
!.vscode/settings.json
.idea/

# OS
.DS_Store
Thumbs.db

# Obsidian
.obsidian/
"@
Set-Content -Path ( Join-Path $OutputPath ".gitignore" ) -Value $_GitignoreContent -Encoding UTF8

# .env.example
$_EnvExampleContent = @"
# AI Memory Vault 環境變數

# OpenAI API（用於 LLM）
OPENAI_API_KEY=your-openai-api-key

# 嵌入模型設定（可選，預設使用本地模型）
# EMBEDDING_MODEL=text-embedding-3-small

# Debug 模式
DEBUG=false
"@
Set-Content -Path ( Join-Path $OutputPath "AI_Engine\.env.example" ) -Value $_EnvExampleContent -Encoding UTF8

# Vault/_system/CLAUDE.md
$_ClaudeContent = @"
---
type: system
domain: ai-entry
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "AI Session 入口指令。啟動時第一個讀取的文件。"
---

# CLAUDE.md — AI Session 入口

> **每次 Session 開始時，請依序讀取以下文件：**

1. 本文件（入口指令）
2. [[vault-nav]] — 導航地圖
3. [[action-register]] — 待辦總表
4. [[handoff]] — 上次 Session 交接

---

## Vault 結構

- ``Vault/work/`` — 工作筆記、專案、規則
- ``Vault/life/`` — 日記、學習、目標
- ``Vault/knowledge/`` — 永久知識卡片
- ``Vault/templates/`` — 建立新內容的模板

---

## 常用指令

- 搜尋知識庫：``search_vault("關鍵字")``
- 讀取筆記：``read_note("路徑")``
- 寫入筆記：``write_note("路徑", "內容")``
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\_system\CLAUDE.md" ) -Value $_ClaudeContent -Encoding UTF8

# Vault/_system/vault-nav.md
$_VaultNavContent = @"
---
type: system
domain: navigation
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "Vault 導航地圖：所有區域的入口索引。"
---

# Vault Navigation Map

> **AI Session 啟動時的第 2 步必讀。**

---

## 快速跳轉

| 我想... | 去哪裡 |
|---------|--------|
| 看待辦事項 | [[_system/action-register]] |
| 看上次做了什麼 | [[_system/handoff]] |
| 查某個專案 | [[work/MY_WORKSPACE/projects/]] |
| 記錄學到的東西 | [[life/learning/]] |
| 寫今天的日記 | [[life/journal/]] |

---

## 目錄結構

| 路徑 | 用途 |
|------|------|
| ``work/_shared/`` | 跨組織共用資源 |
| ``work/MY_WORKSPACE/`` | 你的工作空間（可重命名） |
| ``life/journal/`` | 日記 |
| ``life/learning/`` | 學習筆記 |
| ``life/goals/`` | 目標管理 |
| ``knowledge/`` | 永久知識卡片 |
| ``templates/`` | 模板系統 |
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\_system\vault-nav.md" ) -Value $_VaultNavContent -Encoding UTF8

# Vault/_system/action-register.md
$_ActionRegisterContent = @"
---
type: system
domain: action
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "待辦事項總表。"
---

# Action Register

> 所有待處理的任務。

---

## 待辦

- [ ] 設定你的工作空間
- [ ] 閱讀 templates/ 了解模板系統
- [ ] 建立第一份筆記

---

## 已完成

_（空）_
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\_system\action-register.md" ) -Value $_ActionRegisterContent -Encoding UTF8

# Vault/_system/handoff.md
$_HandoffContent = @"
---
type: system
domain: handoff
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "Session 交接文件。記錄上次做了什麼、下次要做什麼。"
---

# Session Handoff

> 每次 Session 結束時更新此文件。

---

## 上次 Session

_（尚無記錄）_

---

## 下次要做

_（尚無記錄）_
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\_system\handoff.md" ) -Value $_HandoffContent -Encoding UTF8

# Vault/_system/AGENTS.md
$_AgentsContent = @"
---
type: system
domain: vault-architecture
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "Vault 架構文件。"
---

# AGENTS.md

> 本檔案描述 Vault 的架構，供 AI Agent 理解知識庫結構。

---

## 架構總覽

``````
AI-Memory-Vault/
├── AI_Engine/              → Python RAG 引擎
└── Vault/
    ├── _system/            → AI 導航層
    ├── work/               → 工作域
    │   ├── _shared/        → 跨組織共用
    │   └── MY_WORKSPACE/   → 你的工作空間
    ├── life/               → 生活域
    ├── knowledge/          → 知識卡片
    └── templates/          → 模板系統
``````

---

## 路徑規則

| 內容類型 | 路徑 |
|---------|------|
| 工作專案 | ``work/{WORKSPACE}/projects/{Project}/`` |
| 編碼規範 | ``work/{WORKSPACE}/rules/`` |
| 會議紀錄 | ``work/{WORKSPACE}/meetings/`` |
| 日記 | ``life/journal/`` |
| 學習筆記 | ``life/learning/`` |
| 知識卡片 | ``knowledge/`` |
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\_system\AGENTS.md" ) -Value $_AgentsContent -Encoding UTF8

# Vault/work/_shared/index.md
$_SharedIndexContent = @"
---
type: index
domain: shared
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "跨組織共用資源入口。"
---

# 共用資源

| 目錄 | 內容 |
|------|------|
| ``skills/`` | AI 技能檔 |
| ``snippets/`` | 程式碼片段 |
| ``tech-stack/`` | 技術棧筆記 |
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\work\_shared\index.md" ) -Value $_SharedIndexContent -Encoding UTF8

# Vault/work/MY_WORKSPACE/index.md
$_WorkspaceIndexContent = @"
---
type: index
domain: workspace
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "你的工作空間入口。"
---

# MY_WORKSPACE

> 這是你的工作空間，你可以將此目錄重命名為你的公司或組織名稱。

---

## 目錄結構

| 目錄 | 用途 |
|------|------|
| ``rules/`` | 編碼規範 |
| ``projects/`` | 專案筆記 |
| ``meetings/`` | 會議紀錄 |
| ``working-context/`` | 當前工作上下文 |
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\work\MY_WORKSPACE\index.md" ) -Value $_WorkspaceIndexContent -Encoding UTF8

# Vault/life/index.md
$_LifeIndexContent = @"
---
type: index
domain: life
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "生活域入口。"
---

# 生活域

| 目錄 | 用途 |
|------|------|
| ``journal/`` | 日記、週/月回顧 |
| ``learning/`` | 學習筆記 |
| ``goals/`` | 目標管理 |
| ``ideas/`` | 靈感收集 |
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\life\index.md" ) -Value $_LifeIndexContent -Encoding UTF8

# Vault/knowledge/index.md
$_KnowledgeIndexContent = @"
---
type: index
domain: knowledge
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "永久知識卡片入口。"
---

# 知識卡片

> 這裡存放萃取後的概念和原則，去脈絡化的永久知識。

---

## 如何使用

1. 從 ``life/learning/`` 或工作經驗中萃取概念
2. 使用 ``templates/sections/knowledge-card/`` 模板
3. 一張卡片只講一個概念
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\knowledge\index.md" ) -Value $_KnowledgeIndexContent -Encoding UTF8

# Vault/templates/index.md
$_TemplatesIndexContent = @"
---
type: index
domain: templates
created: $(Get-Date -Format "yyyy.MM.dd")
ai_summary: "Vault 模板系統主索引。"
---

# 模板系統

> 建立新內容時，請先查閱對應模板。

---

## 模板分類

### Agent 角色模板 — ``agents/``

定義每個 Agent 的職責和輸出格式。

### 專案類型模板 — ``projects/``

| 類型 | 用途 |
|------|------|
| ``python-app/`` | Python 應用程式 |
| ``unity-game/`` | Unity 遊戲專案 |
| ``vscode-ext/`` | VS Code 擴充套件 |

### 區域結構模板 — ``sections/``

| 區域 | 用途 |
|------|------|
| ``company-workspace/`` | 公司工作域 |
| ``rules/`` | 編碼規範 |
| ``meeting/`` | 會議紀錄 |
| ``journal/`` | 日記 |
| ``learning/`` | 學習筆記 |
| ``knowledge-card/`` | 知識卡片 |
"@
Set-Content -Path ( Join-Path $OutputPath "Vault\templates\index.md" ) -Value $_TemplatesIndexContent -Encoding UTF8

# .vscode/mcp.json
$_McpJsonContent = @"
{
  "servers": {
    "ai-memory-vault": {
      "command": "python",
      "args": ["main.py", "--mode", "mcp"],
      "cwd": "`${workspaceFolder}/AI_Engine"
    }
  }
}
"@
Set-Content -Path ( Join-Path $OutputPath ".vscode\mcp.json" ) -Value $_McpJsonContent -Encoding UTF8

# .github/copilot-instructions.md
$_CopilotInstructionsContent = @"
# AI Memory Vault — Workspace Instructions

This repository is an **AI Memory Vault**: a personal knowledge base powered by a local RAG engine.

## MCP Tools Available

| Tool | When to Use |
|------|-------------|
| ``search_vault`` | Find notes by topic, keyword, or semantic query |
| ``read_note`` | Read the full content of a specific note |
| ``write_note`` | Create or overwrite a note (auto-indexes to vector DB) |
| ``sync_vault`` | Rebuild the vector index after bulk file changes |

## Path Convention

All ``file_path`` arguments are **relative to the Vault root** (``Vault/`` folder).

``````
✅  work/MY_WORKSPACE/projects/notes.md
✅  knowledge/python-tips.md
✅  life/journal/2026-04-01.md
❌  D:/AI-Memory-Vault/Vault/... (absolute path)
``````

## Vault Structure

``````
Vault/
├── _system/          → AI navigation layer
├── work/             → Work domain
│   ├── _shared/      → Cross-organization snippets, skills
│   └── MY_WORKSPACE/ → Your workspace (rename as needed)
├── life/             → Personal domain
├── knowledge/        → Permanent knowledge cards
└── templates/        → Structure templates
``````
"@
Set-Content -Path ( Join-Path $OutputPath ".github\copilot-instructions.md" ) -Value $_CopilotInstructionsContent -Encoding UTF8

# .gitkeep files
$_GitkeepPaths = @(
    "Vault\attachments\.gitkeep",
    "Vault\work\_shared\skills\.gitkeep",
    "Vault\work\_shared\snippets\csharp\.gitkeep",
    "Vault\work\_shared\snippets\lua\.gitkeep",
    "Vault\work\_shared\snippets\typescript\.gitkeep",
    "Vault\work\_shared\tech-stack\.gitkeep",
    "Vault\work\MY_WORKSPACE\rules\.gitkeep",
    "Vault\work\MY_WORKSPACE\projects\.gitkeep",
    "Vault\work\MY_WORKSPACE\meetings\.gitkeep",
    "Vault\work\MY_WORKSPACE\working-context\.gitkeep",
    "Vault\life\journal\.gitkeep",
    "Vault\life\learning\.gitkeep",
    "Vault\life\goals\.gitkeep",
    "Vault\life\ideas\.gitkeep",
    "Vault\templates\agents\.gitkeep",
    "Vault\templates\projects\.gitkeep",
    "Vault\templates\sections\.gitkeep"
)

foreach( $_Path in $_GitkeepPaths )
{
    $_FullPath = Join-Path $OutputPath $_Path
    Set-Content -Path $_FullPath -Value "" -Encoding UTF8
}

# ── 完成 ────────────────────────────────────────────────────
Write-Host "`n[3/3] 完成！" -ForegroundColor Green
Write-Host ""
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "初始框架已生成於: $OutputPath" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:" -ForegroundColor Cyan
Write-Host "  1. 將 AI_Engine 程式碼複製到 $OutputPath\AI_Engine"
Write-Host "  2. cd $OutputPath\AI_Engine"
Write-Host "  3. cp .env.example .env && 編輯 .env"
Write-Host "  4. pip install -r requirements.txt"
Write-Host "  5. python main.py --mode mcp"
Write-Host ""
