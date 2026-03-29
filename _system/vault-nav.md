---
type: system
domain: navigation
created: 2026-03-27
last_updated: 2026-03-29
ai_summary: "Vault 導航地圖：所有區域的入口索引。AI Session 啟動時的第二份必讀文件。"
---

# 🗺️ Vault Navigation Map

> **AI Session 啟動時的第 2 步必讀。** 快速了解所有入口點。

---

## ⚡ 快速跳轉

| 我想... | 去哪裡 |
|---------|--------|
| 看待辦事項 | [[_system/action-register]] |
| 看上次做了什麼 | [[_system/handoff]] |
| 寫 C# / Lua（遊戲端） | [[work/CHINESEGAMER/rules/index]]（Rule 01~07） |
| 寫 TypeScript（Extension） | [[work/CHINESEGAMER/rules/index]]（Rule 08~10） |
| 查某個專案 | [[#專案]] |
| 記錄學到的東西 | [[life/learning/index]] |
| 寫今天的日記 | [[life/journal/]] |
| 查 AI Engine 架構 | [[work/LIFEOFDEVELOPMENT/projects/AIMemoryVault/architecture]] |
| 查 AI Engine 進度 | [[work/LIFEOFDEVELOPMENT/projects/AIMemoryVault/dev-progress]] |

---

## 📋 _system — AI 導航層

| 檔案 | 用途 | Session 讀取順序 |
|------|------|:---------------:|
| [[_system/CLAUDE.md\|CLAUDE.md]] | AI 入口指令 | Step 1 |
| [[_system/vault-nav\|vault-nav.md]] | 本檔案 | Step 2 |
| [[_system/action-register\|action-register.md]] | 待辦總表 | Step 3 |
| [[_system/handoff\|handoff.md]] | Session 交接 | Step 4 |
| [[_system/AGENTS.md\|AGENTS.md]] | Vault 架構文件（v3.1） | 需要時查閱 |

---

## 🔧 工作域 — 共用資源 (`_shared`)

| 入口 | 內容 |
|------|------|
| [[work/_shared/tech-stack/\|Tech Stack]] | Unity, C#, XLua, TypeScript, VS Code API |
| [[work/_shared/skills/\|Skills]] | AI 技能檔 |
| [[work/_shared/snippets/\|Snippets]] | C# / Lua / TypeScript 程式碼片段 |

---

## 🔧 工作域 — CHINESEGAMER（上班）

### 規範（10 條 Rule）

> 所有規範都在 `work/CHINESEGAMER/rules/` 底下。

#### 🎮 遊戲開發（Rule 01~07）

| Rule | 入口 | 技術 |
|:----:|------|------|
| 01 | [[work/CHINESEGAMER/rules/01-csharp-coding-style\|C# Style]] | C#, Unity |
| 02 | [[work/CHINESEGAMER/rules/02-lua-coding-style\|Lua Style]] | Lua, XLua |
| 03 | [[work/CHINESEGAMER/rules/03-protocol-implementation\|Protocol]] | Lua, Networking |
| 04 | [[work/CHINESEGAMER/rules/04-viewref-binding\|ViewRef]] | Lua, Unity UI |
| 05 | [[work/CHINESEGAMER/rules/05-tag-system\|Tag System]] | Lua, Game System |
| 06 | [[work/CHINESEGAMER/rules/06-security-game\|Security]] | C#, Lua |
| 07 | [[work/CHINESEGAMER/rules/07-git-conventions\|Git]] | Git |

#### 🔌 VS Code Extension（Rule 08~10）

| Rule | 入口 | 技術 |
|:----:|------|------|
| 08 | [[work/CHINESEGAMER/rules/08-vscode-extension\|Extension 架構]] | TypeScript, VS Code API |
| 09 | [[work/CHINESEGAMER/rules/09-obfuscation-guide\|混淆與驗證]] | webpack, TypeScript |
| 10 | [[work/CHINESEGAMER/rules/10-multi-project-git\|多專案 Git]] | Git, TypeScript |

### 專案

| 專案 | 狀態 | 入口 |
|------|:----:|------|
| SpinWithFriends | 🔄 進行中 | [[work/CHINESEGAMER/projects/SpinWithFriends/project-overview]] |

### 其他

| 入口 | 內容 |
|------|------|
| [[work/CHINESEGAMER/meetings/\|Meetings]] | 會議紀錄 |
| [[work/CHINESEGAMER/people/\|People]] | 人物檔案 |
| [[work/CHINESEGAMER/working-context/\|Working Context]] | 當前工作上下文 |

---

## 🔧 工作域 — LIFEOFDEVELOPMENT（個人專案）

### 規範（3 條 Rule）

| Rule | 入口 | 說明 |
|:----:|------|------|
| 01 | [[work/LIFEOFDEVELOPMENT/rules/01-python-coding-style\|Python Style]] | Python 命名規範 |
| 02 | [[work/LIFEOFDEVELOPMENT/rules/02-ai-engine-architecture\|AI Engine Architecture]] | AI Engine 四層架構規範 |
| 03 | [[work/LIFEOFDEVELOPMENT/rules/03-project-api-map-sync\|Project API Map Sync]] | 程式專案 API Map 同步規則 |

### 專案

| 專案 | 狀態 | 入口 |
|------|:----:|------|
| AIMemoryVault | 🔄 v2.1 | [[work/LIFEOFDEVELOPMENT/projects/AIMemoryVault/project-overview]] |

---

## 🌱 生活域

| 入口 | 內容 |
|------|------|
| [[life/learning/\|📚 Learning]] | 學習筆記（初期扁平存放，≥3 篇同類後建子目錄） |
| [[life/journal/\|📓 Journal]] | 日記 & 每週回顧（格式：YYYY-MM-DD.md / YYYY-WNN-review.md） |
| [[life/goals/\|🎯 Goals]] | 年度目標 & 季度回顧 |
| [[life/ideas/\|💡 Ideas]] | 靈感速記 |

---

## 📚 知識庫

> 經過萃取的**永久概念卡片**。學習過程中的筆記放 `life/learning/`。

| 入口 | 內容 |
|------|------|
| [[knowledge/index\|Knowledge MOC]] | 知識地圖（Map of Content） |

---

## 🧠 記憶系統

| 入口 | 內容 |
|------|------|
| `.ai_memory/instincts/` | Instinct 直覺檔案 |
| `.ai_memory/instinct_config.json` | 系統設定 |
| `.ai_memory/logs/` | Session Log + Chat History |

---

## 🏗️ 模板系統

> 詳見 [[templates/index\|templates/index.md]]（主索引）

| 類型 | 路徑 | 說明 |
|------|------|------|
| Agent 模板 | `templates/agents/` | 10 個 Agent .md（唯一真相來源） |
| 專案類型模板 | `templates/projects/` | python-app / unity-game / vscode-ext |
| Vault 區域模板 | `templates/sections/` | 9 個區域結構模板 |

---

## 📊 Vault 統計

| 指標 | 數量 |
|------|:----:|
| CHINESEGAMER Rules | 10 |
| LIFEOFDEVELOPMENT Rules | 3 |
| Projects | 2（SpinWithFriends / AIMemoryVault） |
| Agent 模板 | 10 |
| Section 模板 | 9 |

---

*最後更新：2026-03-29*
