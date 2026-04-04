---
type: template
template_for: learning
domain: vault-structure
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "學習筆記（讀書、課程、文章）的標準格式模板"
tags: [template, vault-structure, learning]
---

# 📋 學習筆記模板 (TEMPLATE)

> 建立學習筆記於 `life/learning/`

---

## 命名格式

```
YYYY-MM-DD-{type}-{title}.md
```

| type | 用途 | 範例 |
|------|------|------|
| `book` | 讀書筆記 | `2026-03-29-book-clean-code.md` |
| `course` | 課程筆記 | `2026-03-29-course-langchain-masterclass.md` |
| `article` | 文章摘要 | `2026-03-29-article-rag-best-practices.md` |

---

## Frontmatter

```yaml
---
type: book-note | course-note | article-note
title: "{完整標題}"
author: "{作者}"
source: "{URL 或出版資訊}"
status: to-read | reading | completed
rating: 1-5
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "一句話描述學到了什麼"
tags: [learning, {type}, {主題}]
---
```

---

## 建議章節

### 讀書筆記
1. **為什麼讀** — 動機、預期收穫
2. **核心觀點** — 3~5 個關鍵 Takeaway
3. **章節摘要** — 每章一句話
4. **我的反思** — 如何應用到工作中
5. **萃取到 knowledge/** — 是否有值得萃取為永久概念卡的內容

### 課程筆記
1. **課程資訊** — 平台、講師、總時長
2. **每章重點** — 依章節記錄
3. **實作紀錄** — 跟著課程做了什麼 Lab
4. **萃取候選** — 哪些可以變成 knowledge/ 卡片

### 文章摘要
1. **一句話摘要**
2. **關鍵觀點** — Bullet points
3. **與我的關聯** — 對目前工作的影響
