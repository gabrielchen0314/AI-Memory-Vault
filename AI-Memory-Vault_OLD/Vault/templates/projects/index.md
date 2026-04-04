---
type: index
domain: meta
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "專案知識庫模板系統：定義各專案類型的標準文件結構，供 Architect Agent 自動偵測並套用。"
tags: [template, project, index]
---

# 📐 專案模板系統 (Project Templates)

> **用途**：定義各類型軟體專案在 Vault 中的標準知識庫結構。  
> 每個模板資料夾內有 `TEMPLATE.md`，描述該類型需要哪些文件、各文件的 Frontmatter 規範與內容框架。

---

## 已定義類型

| 類型 | 資料夾 | 適用專案 |
|------|--------|----------|
| Python 應用程式 | `python-app/` | FastAPI、RAG 引擎、CLI 工具、自動化腳本 |
| Unity 遊戲（C# + XLua） | `unity-game/` | Unity + XLua 雙層架構遊戲 |
| VS Code Extension | `vscode-ext/` | TypeScript + VS Code API Extension |

---

## 📋 各類型標準文件清單

| 文件 | python-app | unity-game | vscode-ext |
|------|:----------:|:----------:|:----------:|
| `project-overview.md` | ✅ 必要 | ✅ 必要 | ✅ 必要 |
| `architecture.md` | ✅ 必要 | 🔶 選用 | ✅ 必要 |
| `dev-progress.md` | ✅ 必要 | ✅ 必要 | ✅ 必要 |
| `module-catalog.md` | ✅ 必要 | ✅ 必要（lua-module-catalog.md） | 🔶 選用 |
| `{Module}_APIMap.md` | 🔶 選用 | 🔶 選用 | 🔶 選用 |
| `rules-ref.md` | 🔶 選用 | — | — |

---

## 🤖 Architect Agent 自動偵測流程

```
新專案知識庫建立請求
        ↓
1️⃣ 識別 project_type
   依據：語言特徵 / 框架 / 目錄結構 / 使用者描述
        ↓
2️⃣ 查找對應模板
   ├─ 找到 → 載入 TEMPLATE.md → 產生架構提案 → ⏳ WAIT FOR CONFIRM
   └─ 找不到 ↓
        ↓
3️⃣ [新類型處理] 自動推導參考結構
   - 分析專案特性（語言、框架、規模）
   - 基於最接近的既有模板延伸
   - 產生「草稿架構提案」（含標記：📋 草稿，待確認）
        ↓
4️⃣ ⏳ 主動詢問使用者：
   「偵測到新類型 {type}，以下是推薦結構，是否確認並儲存為新模板？」
        ↓
5️⃣ 使用者確認 → 建立 templates/projects/{new-type}/TEMPLATE.md
   使用者修改 → 依回饋調整後建立
   使用者拒絕 → 僅套用於此專案，不儲存模板
```

---

## ⚠️ 使用規則

1. 模板只定義「應有什麼文件」，不預填專案具體內容
2. 每次新增模板類型同步更新本 `index.md` 的類型清單
3. `TEMPLATE.md` 本身不會被 RAG 索引為知識，只作為 AI 指引

---

*最後更新：2026.03.29*
