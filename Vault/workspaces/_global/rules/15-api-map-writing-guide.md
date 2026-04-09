---
type: rule
domain: documentation
category: api-map
workspace: _global
applies_to: [lua, csharp, typescript, python, all-projects]
severity: should
created: 2026.04.09
last_updated: 2026.04.09
ai_summary: "API Map 撰寫指南：定義 API Map 的結構規範、命名規則、模板格式與撰寫原則。搭配 02-project-api-map-sync.md 使用。"
tags: [rule, documentation, api-map, template, global]
---

# 15 — API Map 撰寫指南（全域）

> 本文件為 AI 助手提供撰寫 API Map 的規範與模板，確保 API Map 的一致性和可讀性。
> 搭配 `02-project-api-map-sync.md`（同步規則 = when/where）使用，本文件定義 how。

---

## 1. 什麼是 API Map

API Map 是一份結構化的文件，用於描述模組的：
- **公開介面**：外部可呼叫的 API
- **私有成員**：內部使用的變數和函式
- **資料結構**：Class、Enum、常數定義
- **使用範例**：典型的使用情境和程式碼範例
- **設計理念**：架構決策和注意事項

**主要受眾**：AI 助手（如 GitHub Copilot），用於理解現有模組結構，協助開發新功能。

---

## 2. 檔案命名與存放位置

### 2.1 命名規則

```
{ModuleName}_APIMap.md
```

範例：
- `ColliderMgr_APIMap.md`（Lua）
- `PlayerService_APIMap.md`（C#）
- `AuthModule_APIMap.md`（TypeScript）

### 2.2 存放位置（通用原則）

API Map **放在專案原始碼內**，靠近被描述的模組：

| 專案類型 | 建議路徑 |
|----------|---------|
| 有 `docs/` 目錄 | `{PROJECT_ROOT}/docs/api-maps/{ModuleName}_APIMap.md` |
| 模組式結構 | `{ModuleName}/APIMap/{ModuleName}_APIMap.md` |
| 無特定結構 | `{PROJECT_ROOT}/API_MAP.md`（單檔彙整） |

#### Lua/Unity 專案範例

```
Assets/04.LuaScript/Logic/Mgr/{ModuleName}/
├── {ModuleName}.lua
├── {RelatedModule}.lua
└── APIMap/
    └── {ModuleName}_APIMap.md
```

### 2.3 單一檔案 vs 分開檔案

**建議採用單一檔案**，將高度耦合的模組整合在同一份 API Map 中。

| 情況 | 建議 |
|------|------|
| 輔助模組專屬於主模組 | 合併到主模組的 API Map |
| 輔助模組被多處引用 | 獨立建立 API Map 並相互 Reference |
| 模組間低耦合 | 各自獨立的 API Map |

---

## 3. API Map 結構規範

### 3.1 必要章節

| 章節 | 說明 |
|------|------|
| 模組概覽 | 基本資訊、用途、設計模式 |
| 相依性 | 引用的模組列表 |
| 相關列舉/常數 | Enum 和常數定義 |
| 資料結構 | Class / Struct / Table 欄位定義 |
| 私有成員 | 內部變數和函式 |
| 公開 API | 對外暴露的函式 |
| 使用範例 | 典型使用情境的程式碼 |

### 3.2 選用章節

| 章節 | 說明 |
|------|------|
| 設計模式與注意事項 | 架構決策、效能考量 |
| 版本變更記錄 | API 變更歷史 |
| 關聯模組 Reference | 相關 API Map 路徑 |

---

## 4. 通用模板

````markdown
# {ModuleName} API Map

> **用途**：{簡短描述模組用途}
> **最後更新**：{YYYY.MM.DD}

---

## 1. 模組概覽

| 屬性 | 值 |
|------|-----|
| **模組名稱** | `{ModuleName}` |
| **檔案路徑** | `{FilePath}` |
| **用途** | {用途說明} |
| **設計模式** | {設計模式} |
| **語言** | {Lua / C# / TypeScript / Python} |

### 1.1 架構說明

{描述模組的整體架構和設計理念}

---

## 2. 相依性

### 2.1 引用模組

| 模組名稱 | 引用方式 | 用途 |
|----------|---------|------|
| `{Module}` | `require` / `using` / `import` | {用途} |

### 2.2 被引用情況

- `{OtherModule}` — {引用原因}

---

## 3. 相關列舉與常數

### 3.1 列舉定義

#### {EnumName}

| 值 | 數值 | 說明 |
|----|------|------|
| `Value1` | 0 | {說明} |
| `Value2` | 1 | {說明} |

### 3.2 常數定義

| 常數名稱 | 型別 | 值 | 說明 |
|----------|------|-----|------|
| `CONSTANT_NAME` | number | 100 | {說明} |

---

## 4. 資料結構

### 4.1 {ClassName}

> {Class 用途說明}

#### 欄位定義

| 欄位名稱 | 型別 | 預設值 | 說明 |
|----------|------|--------|------|
| `m_FieldName` | `Type` | `default` | {說明} |

#### 方法列表

| 方法名稱 | 參數 | 返回值 | 說明 |
|----------|------|--------|------|
| `MethodName` | `(param: Type)` | `ReturnType` | {說明} |

---

## 5. 私有成員

### 5.1 私有變數

| 變數名稱 | 型別 | 說明 |
|----------|------|------|
| `_varName` | `Type` | {說明} |

### 5.2 私有函式

#### `_FunctionName(param1, param2)`

> {函式功能說明}

| 參數 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `param1` | `Type` | ✅ | {說明} |
| `param2` | `Type` | ❌ | {說明} |

**返回值**：`ReturnType` — {說明}

---

## 6. 公開 API

### 6.1 初始化與生命週期

#### `ModuleName.Init(param1, param2)`

> {函式功能說明}

| 參數 | 型別 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `param1` | `Type` | ✅ | — | {說明} |
| `param2` | `Type?` | ❌ | `nil` | {說明} |

**返回值**：無

### 6.2 主要功能

#### `ModuleName.DoSomething(param)`

> {函式功能說明}

| 參數 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `param` | `Type` | ✅ | {說明} |

**返回值**：`ReturnType` — {說明}

---

## 7. 使用範例

### 7.1 基本初始化

```
ModuleName.Init(param1, param2)
ModuleName.RegisterCallback(EventType, handler)
```

### 7.2 典型使用情境

```
-- 情境：{描述}
local result = ModuleName.DoSomething(param)
```

---

## 8. 設計模式與注意事項

### 8.1 設計模式

- **{模式名稱}**：{說明}

### 8.2 效能考量

- {注意事項}

### 8.3 常見問題

| 問題 | 解決方案 |
|------|----------|
| {問題} | {方案} |

---

## 9. 關聯模組 Reference（選用）

| 模組 | API Map 路徑 | 關聯說明 |
|------|--------------|----------|
| `{Module}` | `{path}` | {說明} |
````

---

## 5. 撰寫原則

### 5.1 格式規範

1. **表格優先**：使用表格呈現結構化資訊，方便 AI 解析
2. **程式碼區塊**：標記正確的語言（`lua` / `csharp` / `typescript`）
3. **型別標註**：使用對應語言的型別標註格式
4. **參數命名**：遵循專案的命名規範

### 5.2 內容原則

1. **完整性**：涵蓋所有公開 API 和重要的私有成員
2. **準確性**：參數型別、返回值必須與程式碼一致
3. **實用性**：提供可直接使用的程式碼範例
4. **可維護性**：更新程式碼時同步更新 API Map

### 5.3 AI 友善設計

1. **結構化資訊**：使用固定的章節順序，方便 AI 快速定位
2. **明確的型別**：清楚標註參數和返回值的型別
3. **設計意圖**：說明「為什麼」這樣設計，避免 AI 誤解
