---
type: skill
id: api-map-writing
title: API Map 撰寫技能包
domain: documentation
created: 2026-04-10
last_updated: 2026-04-10
ai_summary: "API Map 文件格式規範 — 適用 C#/Lua/Python 專案的接口索引撰寫指南"
applicable_agents: [DocUpdater, Architect]
---

# 🗺️ API Map 撰寫 Skill

> API Map 是「接口索引」，讓 AI 每次對話不需重讀完整程式碼即能理解系統結構。

---

## 什麼時候需要 API Map？

**必要條件（任一即需要）**：
- 專案包含任何程式語言原始碼（.cs / .lua / .py / .ts 等）
- 有跨檔案呼叫的公開介面
- AI 需要理解系統結構才能做修改

---

## API Map 標準格式

```markdown
---
type: api-map
project: {project-name}
org: {ORG}
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
ai_summary: "系統接口索引 — 快速定位模組/類別/函數"
---

# {Project} API Map

## 系統架構概覽

```
{Layer 1} → {Layer 2} → {Layer 3}
{簡述各層職責}
```

## 模組清單

| 模組/類別 | 檔案路徑 | 職責 | 主要公開方法 |
|----------|---------|------|-------------|
| `ModuleName` | `path/to/file.cs` | 職責說明 | `Method1()`, `Method2()` |

## 核心 API 索引

### {Category 1}

#### `ClassName.MethodName(param: Type) -> ReturnType`
- **檔案**：`path/to/file.cs:LineN`
- **說明**：方法用途
- **參數**：
  - `param`：說明
- **回傳**：說明
- **注意**：特殊行為 / 副作用

## 資料結構

### `ClassName`
| 欄位 | 型別 | 說明 |
|------|------|------|
| `m_FieldName` | `string` | 說明 |

## 重要常數 / 列舉

| 名稱 | 值/類型 | 用途 |
|------|---------|------|
| `EStateOfGame` | enum | 遊戲狀態機 |
```

---

## 存放位置規範

```
# Vault 版（AI 可搜尋）
workspaces/{ORG}/projects/{project}/api-map.md

# 專案側（開發者參考，git 同步）
{project-root}/Docs/ApiMap.md
```

> **原則**：專案側 API Map 為主要維護版本；Vault 版為 AI 搜尋用副本。

---

## 撰寫品質指南

### ✅ 好的 API Map
- 每個公開 API 有明確說明
- 包含參數型別和回傳值
- 標出副作用（寫 DB、發事件、改狀態）
- 每次有破壞性變更就同步更新

### ❌ 常見問題
- 只列函數名稱、沒有說明 → 等於沒有
- 過於詳細（直接貼原始碼）→ 看 code 就夠了
- 更新滯後 → 造成 AI 依賴舊接口

---

## 更新觸發條件

| 情境 | 動作 |
|------|------|
| 新增公開方法 | 對應模組區塊加一行 |
| 方法簽名變更 | 更新參數 + 回傳型別 |
| 方法刪除 | 移除對應行，加 `~~刪除~~` 標記保留 1 版 |
| 新模組建立 | 模組清單加一行 + 新增詳細區塊 |
