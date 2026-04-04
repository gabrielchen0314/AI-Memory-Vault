---
type: template
template_for: vscode-ext
domain: architecture
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "VS Code Extension TypeScript 專案的標準知識庫文件結構模板"
tags: [template, vscode, typescript, extension, project-structure]
---

# 📋 VS Code Extension 專案模板 (TEMPLATE)

> **此為模板說明文件。** 新建 VS Code Extension 專案時，依此結構在 `work/{COMPANY}/projects/{ProjectName}/` 建立文件。

---

## 📁 標準文件結構

```
work/{COMPANY}/projects/{ProjectName}/
├── project-overview.md     ← ✅ 必要：Extension 功能、啟動流程、發布資訊
├── architecture.md         ← ✅ 必要：Provider/Command/Webview 架構、命名規則
├── dev-progress.md         ← ✅ 必要：版本進度、功能清單、已知問題
└── {Module}_APIMap.md      ← 🔶 選用：特定 Provider 的詳細 API
```

---

## 📄 project-overview.md Frontmatter

```yaml
---
type: project
workspace: {COMPANY}
domain: vscode-extension
status: planning | active | on-hold | completed
engine: VS Code Extension (TypeScript)
publisher: {publisher-name}
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "Extension 用途一句話"
tags: [vscode, typescript, extension]
---
```

### 必要章節
1. Extension 功能概述
2. 啟動流程（activate() → Command 註冊 → Provider 初始化）
3. 打包設定（webpack / esbuild）
4. 發布資訊（marketplace / 私有）
5. 常用指令（compile、watch、package、publish）

---

## 📄 architecture.md Frontmatter

```yaml
---
type: architecture
project: {ProjectName}
workspace: {COMPANY}
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "VS Code Extension 元件架構與命名規則"
---
```

### 必要章節
1. 元件職責表（Component | 類型 | 職責 | 說明）
   - Types: TreeDataProvider / WebviewViewProvider / Command / EventHandler / StatusBar
2. 命名規則（TypeScript 特定，與遊戲端 m_/i 前綴不同）
3. 生命週期（activate → 使用 → deactivate）
4. 安全考量（混淆設定、公司網路驗證）

---

## 📄 dev-progress.md Frontmatter

```yaml
---
type: dev-progress
project: {ProjectName}
workspace: {COMPANY}
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "Extension 開發進度"
---
```

---

## 識別特徵（Architect 自動偵測用）

| 特徵 | 值 |
|------|----|
| 語言 | TypeScript (.ts) |
| 檔案特徵 | package.json 含 `"engines": { "vscode": "..." }` |
| 目錄特徵 | src/extension.ts / out/ |
| 排除 | package.json 無 vscode engine → 不套用此模板 |
