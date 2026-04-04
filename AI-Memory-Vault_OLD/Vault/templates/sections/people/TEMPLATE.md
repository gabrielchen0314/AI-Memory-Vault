---
type: template
template_for: people
domain: vault-structure
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "同事/聯絡人檔案的標準 Frontmatter 與章節模板"
tags: [template, vault-structure, people]
---

# 📋 人物檔案模板 (TEMPLATE)

> 新增人物檔案時依此格式建立於 `work/{COMPANY}/people/`

---

## 命名格式

```
{kebab-case-name}.md
```

範例：`alice-chen.md`

---

## Frontmatter

```yaml
---
type: person
name: {Full Name}
role: {職稱}
team: {團隊}
workspace: {COMPANY}
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "一句話描述此人的職責與合作關係"
tags: [person, {team}]
---
```

---

## 必要章節

1. **基本資訊** — 表格：姓名 | 職稱 | 團隊 | 聯繫方式
2. **職責範圍** — 負責什麼、與我的交集
3. **合作備忘** — 溝通偏好、注意事項
