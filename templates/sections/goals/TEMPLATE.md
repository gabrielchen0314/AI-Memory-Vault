---
type: template
template_for: goals
domain: vault-structure
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "年度目標與季度回顧的標準格式模板"
tags: [template, vault-structure, goals]
---

# 📋 目標管理模板 (TEMPLATE)

> 建立於 `life/goals/`

---

## 命名格式

| 類型 | 格式 | 範例 |
|------|------|------|
| 年度目標 | `YYYY-goals.md` | `2026-goals.md` |
| 季度回顧 | `YYYY-QN-review.md` | `2026-Q1-review.md` |

---

## 年度目標 Frontmatter

```yaml
---
type: yearly-goals
year: YYYY
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "今年的核心目標概述"
tags: [goals, YYYY]
---
```

### 建議章節
1. **年度主題** — 一句話定義今年的方向
2. **核心目標** — 3~5 個可衡量目標（表格：目標 | 衡量指標 | 截止 | 狀態）
3. **學習計畫** — 想學的技術/書籍
4. **生活目標** — 健康、財務等

---

## 季度回顧 Frontmatter

```yaml
---
type: quarterly-review
quarter: YYYY-QN
date_range: YYYY-MM-DD ~ YYYY-MM-DD
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "本季成果概述"
tags: [goals, review, YYYY-QN]
---
```

### 建議章節
1. **目標達成率** — 對照年度目標，表格：目標 | 目標值 | 實際 | 達成率
2. **本季亮點**
3. **未達成檢討** — 原因 + 對策
4. **下季調整**
