---
type: system
inject: true
created: 2026.04.01
last_updated: 2026.04.10
---

## 🌐 語言規定

> **所有回應、解說、分析必須使用繁體中文。**
> - 技術術語可保留英文（如 `ChromaDB`、`MCP`、`chunks`、`API`）
> - 程式碼本身（變數名、函式名）按各語言慣例
> - Commit message、Vault 筆記、CLI 輸出、MCP 工具回傳：全部繁體中文
> - 禁止整段英文回應；若引用原文需附中文說明

# 🤖 Agent 架構文件

## 🚀 對話開始 SOP（每次對話自動執行）

> AI 在接到任何工作任務時，應先完成以下步驟，再開始工作。

```
Step 1：判斷任務類型 → dispatch_agent(@AgentName)
Step 2：search_instincts(任務關鍵字) → 召回相關直覺（信心 ≥ 0.65 自動提醒）
Step 3：（若需要操作型知識）→ load_skill(相關 Skill 名稱)
```

### 任務類型 → Agent 對照表

| 任務類型 | Agent |
|---------|-------|
| 架構設計 / 技術決策 / 全面審查 | `@Architect` |
| 新功能實作完成 / PR 前 / Bug 修復後 | `@CodeReviewer` |
| 有建置錯誤 / Compile Error | `@BuildErrorResolver` |
| 想重構 / 移除死碼 / 清理技術債 | `@RefactorCleaner` |
| 安全敏感功能 / 輸入驗證 / 反作弊 | `@SecurityReviewer` |
| 規劃複雜任務 / 分解工作 | `@Planner` |
| 撰寫測試 / TDD 流程 | `@TddGuide` |
| 提交程式碼 / 整理 Commit | `@GitCommitter` |
| 更新文件 / API Map | `@DocUpdater` |
| 犯錯後 / 學到新知 / 建立直覺 | `@LearnTrigger` |

> **自動偵測原則**：若對話中出現多個任務類型，主導任務決定 Agent；
> 次要任務（如：實作後審查）在完成後切換至對應 Agent。

### Skill 按需載入原則

- **不需要每次都 load**，只在以下情況載入：
  - 任務需要「操作步驟 / checklist / 決策流程」時
  - 對應 Rule 存在但需要「如何執行」補充時
- `list_skills()` 取得可用清單，`load_skill(name)` 載入對應包

---

## 可用工具（39 個，v3.6）

### Vault 筆記操作

| 工具 | 說明 | DB 更新 |
|------|------|---------|
| `search_vault` | BM25 + 向量混合搜尋 | No |
| `sync_vault` | 全量增量同步 .md → ChromaDB | Yes |
| `read_note` | 讀取指定筆記原始內容 | No |
| `write_note` | 寫入/更新筆記（overwrite/append）+ 自動索引 | Yes |
| `edit_note` | 局部文字替換（old→new，不全覆蓋） | Yes |
| `delete_note` | 刪除 .md + 移除 ChromaDB 向量 | Yes |
| `rename_note` | 移動筆記 + 向量再索引 | Yes |
| `list_notes` | 列出指定目錄下所有 .md | No |
| `batch_write_notes` | 批次寫入多筆，單次索引 | Yes |
| `grep_vault` | 精確文字 / 正規表達式搜尋 | No |

### 排程生成工具

| 工具 | 說明 | DB 更新 |
|------|------|---------|
| `generate_project_daily` | 專案每日進度模板（冪等） | Yes |
| `generate_daily_review` | 每日總進度表（永遠覆寫） | Yes |
| `generate_weekly_review` | 每週總進度表（永遠覆寫） | Yes |
| `generate_monthly_review` | 每月總進度表（永遠覆寫） | Yes |
| `log_ai_conversation` | 對話摘要 + 可選 detail 結構化紀錄 | Yes |
| `generate_ai_weekly_analysis` | AI 對話週報（準確率/Token）| Yes |
| `generate_ai_monthly_analysis` | AI 對話月報（趨勢/評分）| Yes |
| `generate_project_status` | status.md 模板生成（冪等） | Yes |
| `list_scheduled_tasks` | 列出排程任務清單 | No |
| `run_scheduled_task` | 手動觸發排程任務 | Yes |

### 專案與知識管理

| 工具 | 說明 | DB 更新 |
|------|------|---------|
| `list_projects` | 列出所有組織及專案 | No |
| `get_project_status` | status.md 結構化讀取（待辦 + 脈絡） | No |
| `extract_knowledge` | conversations/ → knowledge/ 萃取 | Yes |

### Todo 管理

| 工具 | 說明 | DB 更新 |
|------|------|---------|
| `update_todo` | todo checkbox toggle（不全覆蓋） | Yes |
| `add_todo` | 新增 todo 項目（指定 section） | Yes |
| `remove_todo` | 整行刪除 todo 項目 | Yes |

### 向量索引管理

| 工具 | 說明 | DB 更新 |
|------|------|---------|
| `check_vault_integrity` | 孤立 ChromaDB 向量偵測 | No |
| `clean_orphans` | 外科手術清除孤立向量 | Yes |
| `check_index_status` | 索引設定比對（是否需重建） | No |
| `reindex_vault` | 清除並重建索引 | Yes |

### Agent 與 Skill 管理

| 工具 | 說明 | DB 更新 |
|------|------|---------|
| `list_agents` | 列出所有 Agent 模板（templates/agents/） | No |
| `dispatch_agent` | 載入指定 Agent 完整行為指令 | No |
| `list_skills` | 列出 workspaces/_global/skills/ 知識包 | No |
| `load_skill` | 讀取 Skill 知識包完整內容 | No |

### 直覺記憶工具

| 工具 | 說明 | DB 更新 |
|------|------|---------|
| `create_instinct` | 建立直覺卡片（觸發條件 + 正確做法 + 信心度） | Yes |
| `update_instinct` | 更新信心度 / 新增證據 | Yes |
| `search_instincts` | 語意搜尋直覺卡片（domain / 信心度過濾） | No |
| `list_instincts` | 列出所有卡片（依信心度排序） | No |
| `generate_retrospective` | 月度復盤報告生成（Instinct + 統計）| Yes |

---

## 工具使用原則

- **不重複接口**：相同功能只有一個工具，不建立多個入口
- **DB 更新自動觸發**：所有寫入類工具都會自動更新 ChromaDB
- **冪等注意**：`generate_project_status` / `generate_project_daily` 已存在不覆蓋；`generate_*_review` 永遠覆寫
- **edit_note 優先於 write_note**：局部修改用 `edit_note`，只有全文替換才用 `write_note(overwrite)`
- **delete_note 配對 check_vault_integrity**：先偵測孤立，再清理

---

## AI 自主學習管道

### 學習流程

```
工作中犯錯 / 學到新知
  → 判斷是否符合 instinct 建立條件
  → create_instinct（信心初始 0.6）
  → 寫入 personal/instincts/{id}.md
  → 下次類似情境 → search_instincts → 主動提醒
  → 驗證成功 → update_instinct(+0.1)
  → 月底 → generate_retrospective → 審查 + 演化 Skill
```

### 直覺卡片格式

```yaml
---
id: "slug-format-id"
trigger: "什麼情境下應該想起這條規則"
confidence: 0.6
domain: "debugging|workflow|csharp|unity|lua|python|architecture"
source: "session-observation"
created: "YYYY-MM-DD"
---

# 標題

## 動作
遇到觸發條件時該怎麼做

## 正確模式
程式碼範例（正確 vs 錯誤）

## 證據
- 日期、情境、發生了什麼

## ⚠️ 錯誤反思
### 錯在哪 / 為什麼錯 / 正確做法 / 避免再犯
```

### 信心度管理

| 閾值 | 意義 |
|------|------|
| ≥ 0.7 | 🟢 自動套用（任務開始時主動 search_instincts 並提醒） |
| 0.3 ~ 0.69 | 🟡 參考（搜尋時顯示） |
| < 0.3 | 淘汰（不再顯示） |

- 驗證成功 → `update_instinct(confidence_delta=+0.1)`
- 驗證失敗 / 過時 → `update_instinct(confidence_delta=-0.1)`
- 時間衰減 → 月度復盤時審查

### 建立 Instinct 的時機

1. **犯錯後**：`log_ai_conversation` 的 `detail.problems` 揭示可避免的錯誤
2. **學到新知**：`detail.learnings` 包含值得記住的模式
3. **重複問題**：同類問題第二次出現時，信心度提升
4. **開發者指正**：被使用者糾正後，記錄正確做法

---

## Skills vs Rules 分工

> 詳細說明見 `_config/skills-rules-guide.md`（按需 `read_note` 讀取）

| | Rules (`_global/rules/`) | Skills (`_global/skills/`) |
|--|--|--|
| **性質** | 約束（must/must-not） | 流程（how-to） |
| **載入時機** | 永遠注入（不可跳過） | 任務開始前按需載入 |
| **內容** | 「這樣做是錯的 + 為什麼」 | 「這個任務怎麼做 + checklist」 |
| **對規則的態度** | 是規範本身 | 引用規則（不重複） |

---

## 收工 SOP 標準流程

```
1. generate_project_daily(org, project)           → 建立今日進度模板（冪等）
2. log_ai_conversation(..., detail={...})         → 對話摘要 + 結構化詳細紀錄
3. 萃取直覺（從步驟 2 的 detail 判斷）：
   - detail.problems 有可避免錯誤 → create_instinct
   - detail.learnings 有值得記住的模式 → create_instinct
   - 已有相關直覺被驗證成功/失敗 → update_instinct(±0.1)
4. write_note(status.md, overwrite)               → 更新待辦事項
5. generate_daily_review(date, projects=[])       → 更新每日總進度（永遠覆寫）
```

### log_ai_conversation 參數說明

```
log_ai_conversation(
  organization = "LIFEOFDEVELOPMENT",
  project      = "ai-memory-vault",
  session_name = "api-map-planning",
  content      = "## 對話摘要\n...",      ← 簡短摘要（必填）
  detail       = {                        ← 結構化詳細紀錄（選填）
    "topic":         "API Map 規劃與實作",
    "qa_pairs":      [{"question": "...", "analysis": "...", "decision": "...", "alternatives": "..."}],
    "files_changed": [{"path": "path/to/file", "action": "修改", "summary": "..."}],
    "commands":      [{"command": "...", "purpose": "...", "result": "成功"}],
    "problems":      [{"problem": "...", "cause": "...", "solution": "..."}],
    "learnings":     ["..."],
    "decisions":     [{"decision": "...", "options": "A / B", "chosen": "A", "reason": "..."}]
  }
)
```

> **AI 使用指南**：detail 的所有欄位都是選填，有多少填多少。
> AI 應從 conversation summary、工作記憶、tool call 紀錄中自動萃取。

---

## Coding 規則索引

> 所有規則集中在 `workspaces/_global/rules/`（全域）與 `workspaces/{組織}/rules/`（組織特例）。
> 使用 `search_vault(query="type:rule", top_k=30)` 動態發現最新規則清單。

**規則套用邏輯：**
- frontmatter `workspace: _global` → 永遠套用（所有組織）
- frontmatter `workspace: {ORG}` → 僅套用於該組織的專案

---

## VS Code 整合

統一橋接入口：`{vscode_user_path}/prompts/vault-bridge.instructions.md`
- 語言規定（繁體中文）
- 程式任務前呼叫 `search_vault(query="type:rule")` 取得最新規則
- 程式任務前並行呼叫 `search_instincts(query="{任務關鍵字}")` 載入相關直覺
- Vault 路徑規範與目錄查詢指引
