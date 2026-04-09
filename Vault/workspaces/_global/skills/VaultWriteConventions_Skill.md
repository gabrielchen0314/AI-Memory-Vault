---
type: skill
id: vault-write-conventions
title: Vault 寫入規範技能包
domain: vault-workflow
created: 2026-04-10
last_updated: 2026-04-10
ai_summary: "撰寫 Vault .md 筆記的格式規範 — frontmatter、路徑、命名、todo 管理"
applicable_agents: [DocUpdater, Architect, Planner]
---

# 📋 Vault 寫入規範 Skill

> 載入此技能包以確保所有 Vault 寫入操作符合標準格式。

---

## 1. Frontmatter 規範

每個 Vault 筆記的 frontmatter 必須包含：

```yaml
---
type: <note-type>     # 必填。例如 project-status, conversation, knowledge
project: <name>       # 專案筆記必填
org: <ORG_NAME>       # 組織筆記必填（大寫）
created: YYYY-MM-DD   # 必填
last_updated: YYYY.MM.DD  # 建議，每次修改更新
ai_summary: "..."    # 建議，讓 AI 快速理解內容
tags: [tag1, tag2]    # 選填
---
```

### type 值一覽

| type | 用途 |
|------|------|
| `project-status` | 專案 status.md |
| `project-daily` | 每日進度 |
| `conversation` | AI 對話摘要 |
| `conversation-detail` | AI 對話詳細紀錄 |
| `knowledge` | 知識卡片 |
| `daily-summary` | 每日總覽 |
| `weekly-summary` | 每週總覽 |
| `agent-template` | Agent 定義 |
| `skill` | Skill 知識包 |
| `instinct` | 直覺卡片 |

---

## 2. 路徑規範

| 內容類型 | 路徑格式 |
|----------|----------|
| 專案狀態 | `workspaces/{ORG}/projects/{proj}/status.md` |
| 每日進度 | `workspaces/{ORG}/projects/{proj}/daily/{YYYY-MM-DD}.md` |
| 對話摘要 | `workspaces/{ORG}/projects/{proj}/conversations/{YYYY-MM-DD}_{session}.md` |
| 對話詳細 | `workspaces/{ORG}/projects/{proj}/conversations/{YYYY-MM-DD}_{session}-detail.md` |
| 知識卡片 | `knowledge/{YYYY-MM-DD}-{topic-slug}.md` |
| 每日總覽 | `personal/reviews/daily/{YYYY-MM-DD}.md` |
| 每週總覽 | `personal/reviews/weekly/{YYYY}-W{WW}.md` |
| 全域規則 | `workspaces/_global/rules/{NN}-{slug}.md` |
| 技能包 | `workspaces/_global/skills/{Name}_Skill.md` |
| 直覺卡片 | `workspaces/_global/instincts/{slug}.md` |

---

## 3. Todo 管理規範

```
# status.md 結構
## 待辦事項

### 進行中
- [ ] 正在做的任務

### 待處理
- [ ] 下一步任務

### 已完成
- [x] 已完成的任務
```

### MCP 工具對應

| 操作 | 工具 |
|------|------|
| 切換完成狀態 | `update_todo(file_path, todo_text, done=True)` |
| 新增 todo | `add_todo(file_path, todo_text, section="## 待辦事項")` |
| 移除 todo | `remove_todo(file_path, todo_text)` |

---

## 4. 寫入操作選擇指南

| 情境 | 工具 |
|------|------|
| 全新筆記 / 全覆蓋 | `write_note(path, content, mode="overwrite")` |
| 追加內容到尾端 | `write_note(path, content, mode="append")` |
| 局部替換特定文字 | `edit_note(path, old_text, new_text)` |
| 批次寫入多筆 | `batch_write_notes([{file_path, content, mode}])` |
| 移動 / 重命名 | `rename_note(old_path, new_path)` |
| 刪除 | `delete_note(path)` |

> ⚠️ **注意**：edit_note 的 old_text 必須在檔案中恰好出現一次。
