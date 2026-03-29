---
type: template
template_for: unity-game
domain: architecture
workspace: _shared
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "Unity C# + XLua 遊戲專案的標準知識庫文件結構模板"
tags: [template, unity, xlua, csharp, lua, project-structure]
---

# 📋 Unity Game 專案模板 (TEMPLATE)

> **此為模板說明文件。** 新建 Unity + XLua 遊戲專案時，依此結構在 `work/{COMPANY}/projects/{ProjectName}/` 建立文件。

---

## 📁 標準文件結構

```
work/{COMPANY}/projects/{ProjectName}/
├── project-overview.md         ← ✅ 必要：專案總覽、C#↔Lua 架構、目錄結構、BUG 清單
├── dev-progress.md             ← ✅ 必要：開發進度、待辦事項、已知問題
├── lua-module-catalog.md       ← ✅ 必要：所有 Lua 模組與 Manager 的責任清單
└── {Module}_APIMap.md          ← 🔶 選用：單一 Manager 的詳細 API（對外函式）
```

---

## 📄 project-overview.md Frontmatter

```yaml
---
type: project-overview
project: {ProjectName}
workspace: {local-path}          # 本機專案路徑，如 d:\MyWork\SpinWithFriends
engine: Unity (XLua)
company: {COMPANY}
author: gabrielchen
created: YYYY.MM.DD
last_updated: YYYY.MM.DD
ai_summary: "一句話：C# 層做什麼，Lua 層做什麼"
tags: [unity, xlua, lua, csharp, game]
---
```

### 必要章節
1. 基本資訊（表格：專案名、公司、引擎、路徑、唯一場景）
2. 整體架構（程式碼樹示意 + 層次說明表）
3. C# ↔ Lua 橋接方式
4. 專案目錄結構（Assets/ 樹）
5. C# 核心類別表
6. Lua 全域綁定表（GDefines.lua）
7. 已知問題 / BUG

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
1. 當前版本 / 迭代狀態
2. 最近完成的功能
3. 進行中 / 待辦
4. 已知問題 / BUG（嚴重度標記）
5. 技術債

---

## 📄 lua-module-catalog.md

### 必要章節
1. Manager 清單（Manager | 路徑 | 責任 | 主要對外函式）
2. Common / Global 模組清單
3. UI 系統模組清單（Controller 命名規則）
4. 依賴關係說明

---

## 識別特徵（Architect 自動偵測用）

| 特徵 | 值 |
|------|----|
| 語言 | C# (.cs) + Lua (.lua) |
| 目錄特徵 | Assets/ / ProjectSettings/ / *.unity |
| XLua 特徵 | `[XLua.LuaCallCSharp]` / `LuaEnv` / `XLuaManager` |
| 純 C# Unity | Assets/ 存在但無 .lua → 不套用此模板 |
