---
type: template
template_for: journal
domain: vault-structure
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "日記與每週回顧的標準格式模板"
tags: [template, vault-structure, journal]
---

# 📋 日記模板 (TEMPLATE)

> 建立日記於 `life/journal/`

---

## 命名格式

| 類型 | 格式 | 範例 |
|------|------|------|
| 每日日記 | `YYYY-MM-DD.md` | `2026-03-29.md` |
| 每週回顧 | `YYYY-WNN-review.md` | `2026-W13-review.md` |

---

## 每日日記 Frontmatter

```yaml
---
type: daily
date: YYYY-MM-DD
mood: 😊 | 😐 | 😓 | 🔥 | 💤
energy: high | medium | low
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "今天一句話摘要"
---
```

### 建議章節
1. **今日重點** — 3 件最重要的事
2. **完成事項** — 清單
3. **學到的事** — 可觸發 knowledge/ 萃取
4. **明日待辦**

---

## 每週回顧 Frontmatter

```yaml
---
type: weekly-review
week: YYYY-WNN
date_range: YYYY-MM-DD ~ YYYY-MM-DD
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "本週一句話摘要"
---
```

### 建議章節
1. **本週成就** — 清單
2. **本週挑戰** — 遇到什麼問題、怎麼解決
3. **下週計畫**
4. **心得 & 反思**
