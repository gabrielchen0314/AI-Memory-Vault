---
type: template
template_for: meeting
domain: vault-structure
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "會議紀錄的標準 Frontmatter 與章節模板"
tags: [template, vault-structure, meeting]
---

# 📋 會議紀錄模板 (TEMPLATE)

> 新增會議紀錄時依此格式建立於 `work/{COMPANY}/meetings/`

---

## 命名格式

```
YYYY-MM-DD-{主題}.md
```

範例：`2026-03-29-sprint-review.md`

---

## Frontmatter

```yaml
---
type: meeting
date: YYYY-MM-DD
attendees: [人名1, 人名2]
project: {關聯專案名}
action_items: {數量}
workspace: {COMPANY}
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "一句話會議摘要"
tags: [meeting, {project}]
---
```

---

## 必要章節

1. **議題（Agenda）**
2. **討論重點** — 每個議題的結論
3. **決策事項（Decisions）** — 表格：決策 | 原因 | 負責人
4. **行動事項（Action Items）** — 表格：項目 | 負責人 | 截止日 | 狀態
5. **下次會議** — 日期 + 預定議題
