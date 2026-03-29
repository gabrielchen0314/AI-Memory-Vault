---
type: index
domain: templates
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "Vault 全域模板系統主索引：agents（10 角色）、projects（3 類型）、sections（9 區域）"
tags: [index, template, vault-system]
---

# 📋 模板系統主索引 (Templates)

> 此目錄為 Vault 模板的唯一根入口。所有 Agent 在建立新內容時，**必須先查閱對應模板**。

---

## 📂 模板分類

### 1. Agent 角色模板 — `templates/agents/`

定義每個 Agent 的職責、觸發條件、輸出格式。

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

---

### 2. 專案類型模板 — `templates/projects/`

定義不同類型專案在 `work/{COMPANY}/projects/{PROJECT}/` 下的標準檔案結構。

| 類型 | 檔案 | 識別特徵 |
|------|------|---------|
| Python App | `projects/python-app/TEMPLATE.md` | `requirements.txt` / `.venv` / `.py` |
| Unity Game | `projects/unity-game/TEMPLATE.md` | `Assets/` / `.unity` / `.cs` + `.lua` |
| VS Code Extension | `projects/vscode-ext/TEMPLATE.md` | `package.json` + `contributes` |

詳見：`templates/projects/index.md`

---

### 3. Vault 區域模板 — `templates/sections/`

定義 Vault 各分支區域的標準結構與文件格式。**任何 Agent 在建立新內容時，必須查閱此處。**

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

## 🔁 全域模板自動偵測規則

> 此規則適用於**所有 Agent**，不限於 Architect。

### 流程

```
Agent 要在 Vault 任意位置建立內容
        │
        ▼
  ┌──────────────────────┐
  │ 查找對應模板          │
  │ templates/sections/   │
  │ templates/projects/   │
  └──────────┬───────────┘
             │
     ┌───────┴───────┐
     │ 模板存在？      │
     ├── YES ────────► 依模板建立
     └── NO ─────────► 進入草案流程
                              │
                              ▼
                ┌──────────────────────────┐
                │ 1. 產出「草案模板」範例結構  │
                │ 2. 向使用者展示             │
                │ 3. ⏸️ 等待確認              │
                │ 4. 確認後：                 │
                │    a) 儲存為正式模板         │
                │    b) 依模板建立內容         │
                └──────────────────────────┘
```

### 草案模板格式

```markdown
## 🆕 發現未知結構類型：{TYPE_NAME}

**偵測位置**：`{path}`
**Agent**：{agent_name}

### 建議結構

{提出的資料夾 + 檔案結構}

### 建議 Frontmatter

{YAML 範例}

### 建議章節

{標準章節列表}

---

> ✅ 確認此結構 → 我將儲存為 `templates/sections/{type}/TEMPLATE.md` 並開始建立內容
> ✏️ 需要調整 → 請告訴我要修改哪些部分
> ❌ 跳過模板 → 直接建立（不儲存模板）
```

---

## ⚠️ 規則

1. **模板優先**：有模板必須遵循，不可跳過
2. **未知先問**：遇到未知結構，先草案再確認
3. **模板可演進**：使用者確認後的修改應回寫模板
4. **路徑唯一**：每個模板只對應一種路徑模式
