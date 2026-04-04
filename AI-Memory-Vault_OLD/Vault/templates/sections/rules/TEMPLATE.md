---
type: template
template_for: rules
domain: vault-structure
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "公司規則集的標準結構模板：規則文件命名、Frontmatter、索引格式"
tags: [template, vault-structure, rules]
---

# 📋 規則集模板 (TEMPLATE)

> 建立於 `work/{COMPANY}/rules/`

---

## 📁 標準結構

```
work/{COMPANY}/rules/
├── index.md              ← ✅ 必要：規則索引
├── 01-{topic}.md         ← NN-{kebab-case}.md 格式
├── 02-{topic}.md
└── ...
```

---

## 命名格式

```
NN-{kebab-case-topic}.md
```

規則依領域分組，編號連續不跳號：
- 01~09：編碼規範（coding-style, architecture）
- 10~19：工作流規範（git, ci/cd）
- 20~29：安全規範（security, obfuscation）

---

## 規則文件 Frontmatter

```yaml
---
type: rule
domain: coding | networking | ui | system | security | workflow | architecture
category: {具體分類}
workspace: {COMPANY}
applies_to: [python, csharp, lua, typescript, ...]
severity: critical | must | should | nice-to-have
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "一句話描述此規則的核心要求"
tags: [rule, {domain}, {applies_to}]
---
```

---

## index.md 必要內容

1. **規則清單表格**：# | 檔案 | 領域 | 嚴重度 | 適用技術 | 說明
2. **依開發領域分類**
3. **依 Agent 對應**：哪個 Agent 參考哪條規則
4. **命名風格速查表**（如有多語言差異）
