---
type: template
template_for: knowledge-card
domain: vault-structure
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "永久知識卡片（萃取後概念）的標準格式模板"
tags: [template, vault-structure, knowledge]
---

# 📋 知識卡片模板 (TEMPLATE)

> 建立於 `knowledge/`  
> **邊界**：只放經過萃取的永久概念。學習過程筆記放 `life/learning/`。

---

## 命名格式

```
{kebab-case-concept}.md
```

範例：`design-patterns.md`、`solid-principles.md`、`rag-architecture.md`

---

## Frontmatter

```yaml
---
type: knowledge-card
title: "{概念名稱}"
domain: architecture | coding | ai | devops | management | other
maturity: seed | growing | evergreen
source_notes: ["{相關 learning 筆記路徑}"]
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "一句話定義此概念"
tags: [knowledge, {domain}]
---
```

### maturity 定義
| 等級 | 說明 |
|------|------|
| `seed` | 初步萃取，可能不完整 |
| `growing` | 已有多次補充與驗證 |
| `evergreen` | 成熟穩定，是核心知識 |

---

## 建議章節

1. **一句話定義** — 用自己的話解釋此概念
2. **核心原則** — 3~5 個關鍵要點
3. **常見應用** — 在什麼場景下使用
4. **我的實踐** — 在自己的專案中怎麼用（含連結）
5. **相關概念** — `[[其他知識卡片]]` 連結
6. **參考來源** — 書籍、文章、課程
