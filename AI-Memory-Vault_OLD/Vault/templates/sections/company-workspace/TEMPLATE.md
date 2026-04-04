---
type: template
template_for: company-workspace
domain: vault-structure
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "公司工作域的標準資料夾結構模板：rules、projects、meetings、people、working-context"
tags: [template, vault-structure, company]
---

# 📋 公司工作域模板 (TEMPLATE)

> 新增一家公司到 `work/` 時，依此結構建立資料夾。

---

## 📁 標準結構

```
work/{COMPANY}/
├── index.md                    ← ✅ 必要：公司入口導航
├── rules/                      ← ✅ 必要：編碼 / 架構 / 工作流規範
│   └── index.md
├── projects/                   ← ✅ 必要：專案知識庫（套用 templates/projects/{type}）
│   └── .gitkeep
├── meetings/                   ← 🔶 選用：會議紀錄
├── people/                     ← 🔶 選用：人物檔案
└── working-context/            ← 🔶 選用：當前工作上下文
```

---

## 📄 index.md 內容框架

```markdown
# {COMPANY} 工作域

| 欄位 | 值 |
|------|-----|
| 公司名稱 | {COMPANY} |
| 主要技術棧 | {列出主要語言/框架} |
| 規則數量 | {N} 條 |
| 專案數量 | {N} 個 |
```
