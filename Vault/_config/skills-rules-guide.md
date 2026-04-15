---
type: system-guide
category: skills-rules
created: 2026-04-10
last_updated: 2026-04-12
inject: false
ai_summary: "Skills vs Rules 分工指南 — 邊界定義、Skill 撰寫規範、命名慣例、Instinct 演化觸發條件"
---

# Skills vs Rules 分工指南

> 此文件說明 `_global/rules/` 與 `_global/skills/` 的設計邊界，
> 供維護者和 AI 在新增內容時參考。
> 按需讀取：`read_note("_config/skills-rules-guide.md")`

---

## 核心差異

| 面向 | Rules | Skills |
|------|-------|--------|
| **存放位置** | `workspaces/_global/rules/{NN}-{slug}.md` | `workspaces/_global/skills/{Domain}_{UseCase}_Skill.md` |
| **性質** | 約束（must / must-not） | 流程（how-to / checklist） |
| **載入時機** | 永遠注入（VS Code instructions / 全域） | 任務開始前 `load_skill()` 按需載入 |
| **內容焦點** | 「這樣做是錯的 + 為什麼」 | 「這個任務怎麼做一步步來」 |
| **對命名規範的態度** | 是規範本身，有完整範例 | 說「請見 Rule NN」，不重複 |
| **更新來源** | 人工定義，版本才改 | 從 Instinct 聚類演化，也可人工新增 |
| **粒度** | 完整規範（長文、全面） | 精煉知識包（聚焦特定場景，< 200 行） |

---

## 不應該重複的內容

Skill 如果只是把 Rule 的內容複製一遍，等於沒有價值。

### ❌ 錯誤示範（CSharpCodingStyle_Skill.md 不應這樣寫）

```markdown
## 變數命名
- 成員變數加 m_ 前綴
- 參數加 i 前綴
- 區域變數加 _ 前綴
```

這些已經在 `Rule 03-csharp-coding-style.md` 中了，不要重複。

### ✅ 正確示範（Skill 應該補 Rule 沒有的部分）

```markdown
## 建立新 C# 類別 SOP

> 命名規範請見 `workspaces/_global/rules/03-csharp-coding-style.md`

### Step 1：確認類別類型
- MonoBehaviour？ → 不能有建構函式，用 Awake()
- Singleton？ → 繼承 Singleton<T>，加 Instance

### Step 2：建立前檢查清單
- [ ] 確認是否需要 [LuaCallCSharp] 標籤
- [ ] Awake / OnDestroy 是否成對
- [ ] 是否需要物件池（頻繁建立/銷毀）

### Step 3：常見錯誤地雷
| 雷區 | 正確做法 |
|------|---------|
| Update 中字串拼接 | StringBuilder 或 避免 |
| 直接 GetComponent 不快取 | Awake 中快取到 m_ 變數 |
```

---

## Skill 撰寫規範

### 必要 Frontmatter

```yaml
---
type: skill
id: {domain-usecase}             ← kebab-case
title: {標題}
domain: {領域}                   ← 同 Instinct domain 標籤
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "一句話說明此 Skill 的適用場景"
applicable_agents: [Agent1, Agent2]   ← 哪些 Agent 應載入此 Skill
---
```

### 命名規則

格式：`{Domain}_{UseCase}_Skill.md`

| 範例 | 說明 |
|------|------|
| `Debug_Workflow_Skill.md` | 通用除錯流程 |
| `CSharp_NewClass_Skill.md` | 建立 C# 類別 SOP |
| `Lua_Module_Skill.md` | Lua 模組建立 SOP |
| `ApiMap_Writing_Skill.md` | API Map 撰寫流程 |
| `Git_Commit_Skill.md` | Git 提交流程 |
| `VaultWrite_Conventions_Skill.md` | Vault 筆記寫入規範 |

> **不應包含** Rule 的完整內容。Rule 應直接引用，不複製。

### 長度控制

- 目標：< 200 行
- 超過時，拆分為多個 Skill（依 UseCase 細分）

---

## Instinct → Skill 聚類演化

### 觸發條件

| 條件 | 閾值 |
|------|------|
| 同 domain 的 Instinct 數量 | ≥ 3 |
| 加權平均信心度 | ≥ 0.65 |
| 觸發條件有明確關聯 | 是 |

### 演化流程

```
monthly → generate_retrospective()
  ↓ 分析 Instinct 聚類
  ↓ 找出可合併的 domain 群
  ↓ 人工確認 + 整理流程
  ↓ 新增 Skill 知識包
  ↓ 在對應 Instinct 加上 evolved_to: {skill_name} 標記
```

---

## 現有 Skills 一覽

> 完整清單見 `workspaces/_global/skills/index.md`（唯一真實來源）。
> 使用 `list_skills()` 查詢最新可用技能包。

---

## 新增 Skill 必做清單

> **每次新增 `_global/skills/*.md`，AI 必須完成以下三項。**

| # | 檔案 | 動作 |
|---|------|------|
| 1 | `_global/skills/index.md` | 在「可用技能包」表格加入新行 |
| 2 | `_config/agents.md` | 若 Skill 影響 Agent 行為，更新對應 Agent 註解 |
| 3 | VS Code `prompts/global-prompts-maintenance.instructions.md` | 在 `skills/` 表格加入新行 |

違反此清單的症狀：`list_skills()` / `index.md` 展示舊内容，AI 不清楚最新可用 Skill。

---

## 新增 Rule 必做清單

> **每次新增 `_global/rules/*.md`，必須完成以下步驟。**

| # | 檔案 | 動作 |
|---|------|------|
| 1 | 本檔「現有 Rules 一覽」 | 在表格加入新行 |
| 2 | VS Code `prompts/global-prompts-maintenance.instructions.md` | 在「全域規則清單」加入新行 |
| 3 | `templates/agents/*.md` | 更新相關 Agent 的 `related_rules` |

---

## 現有 Rules 一覽（`_global/rules/`）

> 僅供速查索引。最新規則以 `search_vault(query="type:rule")` 為準。

| 編號 | 檔案 | 涵蓋領域 |
|------|------|---------|
| 01 | `01-coding-style-universal.md` | 通用命名（m_/i/_ 前綴、常數、布林）|
| 02 | `02-project-api-map-sync.md` | API Map 同步規範 |
| 03 | `03-csharp-coding-style.md` | C# / Unity 編碼規範補充 |
| 04 | `04-lua-coding-style.md` | Lua 編碼規範 |
| 05 | `05-python-coding-style.md` | Python 編碼規範 |
| 06 | `06-protocol-implementation.md` | 協定實作規範 |
| 07 | `07-viewref-binding.md` | ViewRef 綁定規範 |
| 08 | `08-tag-system.md` | Tag 系統規範 |
| 09 | `09-security-game.md` | 遊戲安全規範 |
| 10 | `10-git-conventions.md` | Git 提交規範 |
| 11 | `11-vscode-extension.md` | VS Code Extension 規範 |
| 12 | `12-obfuscation-guide.md` | 混淆指南 |
| 13 | `13-multi-project-git.md` | 多專案 Git 規範 |
| 14 | `14-ai-engine-architecture.md` | AI Engine 架構規範 |
| 15 | `15-api-map-writing-guide.md` | API Map 撰寫指南（格式範本）|

---

## 版本更新必做清單

> **版本號提升時（如 v3.7 → v3.8），必須同步更新以下檔案。**

| # | 檔案 | 更新項目 |
|---|------|---------|
| 1 | `AI_Engine/config.py` | `VERSION` 常數 |
| 2 | `AI_Engine/pyproject.toml` | `version` 欄位 |
| 3 | `_config/agents.md` | 標題中的版本號（如「可用工具（N 個，vX.Y）」） |
| 4 | `{org}/projects/{project}/status.md` | 版本相關待辦標記完成 |
| 5 | `{org}/projects/{project}/notes/roadmap.md` | 對應 Phase 標記 ✅ |
