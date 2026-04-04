---
type: template
template_for: python-app
domain: architecture
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "Python 應用程式專案的標準知識庫文件結構模板"
tags: [template, python, project-structure]
---

# 📋 Python App 專案模板 (TEMPLATE)

> **此為模板說明文件。** 新建 Python 應用程式專案時，依此結構在 `work/{COMPANY}/projects/{ProjectName}/` 建立文件。

---

## 📁 標準文件結構

```
work/{COMPANY}/projects/{ProjectName}/
├── project-overview.md     ← ✅ 必要：專案總覽、願景、架構圖、Roadmap
├── architecture.md         ← ✅ 必要：模組責任表、資料流、關鍵設計決策
├── dev-progress.md         ← ✅ 必要：開發進度、待辦事項、已知問題
├── module-catalog.md       ← ✅ 必要：所有模組清單（含責任、對外 API 摘要）
└── {Module}_APIMap.md      ← 🔶 選用：單一模組的詳細 API 文件
```

---

## 📄 project-overview.md Frontmatter

```yaml
---
type: project
workspace: {COMPANY}
domain: {domain}               # web / ai-infrastructure / automation / cli
status: planning | active | on-hold | completed
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "一句話描述專案用途"
tags: [python, fastapi, ...]   # 實際使用的技術
---
```

### 必要章節
1. 🎯 專案願景
2. 🏗️ 核心架構（分層或模組圖）
3. 📁 目錄結構（`tree` 格式）
4. 🗺️ Roadmap（依階段，含完成狀態）
5. 🛠️ 常用指令

---

## 📄 architecture.md Frontmatter

```yaml
---
type: architecture
project: {ProjectName}
workspace: {COMPANY}
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "模組責任表與資料流"
---
```

### 必要章節
1. 模組責任表（Module | 職責 | 依賴 | 對外介面）
2. 資料流圖（User Input → ... → Output）
3. 關鍵設計決策（ADR 格式）
4. 安全考量（輸入驗證、路徑防護、API Key 管理）

---

## 📄 dev-progress.md Frontmatter

```yaml
---
type: dev-progress
project: {ProjectName}
workspace: {COMPANY}
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "開發進度追蹤"
---
```

### 必要章節
1. 當前版本狀態
2. 已完成功能（依版本）
3. 進行中 / 待辦
4. 已知問題 / BUG
5. 技術債清單

---

## 📄 module-catalog.md Frontmatter

```yaml
---
type: module-catalog
project: {ProjectName}
workspace: {COMPANY}
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "Python 模組目錄，含責任邊界與對外 API"
---
```

### 必要章節
1. 模組清單總覽表（Module | 檔案 | 責任 | 主要對外函式）
2. 依賴關係圖
3. 各模組簡述（每個模組：責任、入口函式、重要設定）

---

## 識別特徵（Architect 自動偵測用）

| 特徵 | 值 |
|------|----|
| 語言 | Python (.py) |
| 框架特徵 | requirements.txt / pyproject.toml / .venv / Dockerfile |
| 主流框架 | FastAPI / LangChain / Click / Typer / Celery |
| 排除 | 不含 Assets/ 或 package.json + vscode engine |
