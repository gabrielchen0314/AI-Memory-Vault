---
type: rule
domain: coding
category: lua-coding-style
workspace: CHINESEGAMER
applies_to: [lua, xlua, tolua, unity]
severity: must
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, lua, xlua, naming, coding-style, data-validation]
source: RD-指示-Lua Coding Style.instructions.md, RD-指示-LuaData型別驗證修正.instructions.md
ai_summary: "Lua 編碼規範：private 封裝、this 模組引用、m_ 成員變數、i 參數、_ 區域變數、禁止 goto/self、LuaDoc 註解、Dispose 清理、Data 型別驗證。"
---

# Lua Coding Style — CHINESE GAMER

> ⚠️ **絕對禁止使用 goto 語句**
> 📋 **完整 Golden Example**：`.copilot/skills/lua-coding-style/SKILL.md`

---

## 📐 編碼原則

| 原則 | 說明 |
|------|------|
| **Readability First** | 程式碼是給人讀的，清晰的命名優於註解，保持一致的格式 |
| **KISS** | 選擇最簡單可行的方案，避免過度設計，易懂 > 花俏 |
| **DRY** | 不重複自己，抽取共用邏輯，建立可重用元件 |
| **YAGNI** | 不預先建構未需要的功能，先簡單實作，需要時再重構 |

---

## 🏷️ 命名規範速查表

| 類型 | 前綴 | 範例 |
|------|------|------|
| 成員變數 | `m_` | `private.m_Counter`, `private.m_IsActive` |
| 參數 | `i` | `iAmount`, `iPlayerData` |
| 區域變數 | `_` | `local _TempValue`, `local _Result` |
| 常數 | 全大寫 | `local MAX_COUNT = 100` |
| 布林變數 | `Is/Can/Has` | `m_IsInitialized`, `m_CanMove` |
| 模組引用 | `this` | `local this = ModuleName` |
| 私有封裝 | `private` | `local private = {}` |
| 列舉類型 | `E` 前綴 | `ECounterState`, `EItemType` |

### Unity 組件命名

```lua
-- ✅ 格式：m_{型別}_{名稱}
private.m_Button_Start = nil
private.m_Text_Title = nil
private.m_Image_Icon = nil
private.m_Trans_Content = nil
```

```lua
-- ❌ 錯誤：缺少型別前綴
private.m_Start = nil
private.m_Title = nil
```

### 集合命名

```lua
-- ✅ 格式：m_{容器類型}_{內容}
private.m_List_Items = {}      -- 陣列（index 從 1 開始）
private.m_Dic_NameById = {}    -- 字典（key-value）
```

```lua
-- ❌ 錯誤：缺少容器類型
private.m_Items = {}
private.m_Names = {}
```

---

## 🏗️ 模組結構

```lua
ModuleName = {}
local this = ModuleName
local private = {}

-- region 常數定義
local MAX_COUNT = 100
-- endregion

-- region 私有成員變數
---@type number 計數器
private.m_Counter = 0

---@type boolean 是否已初始化
private.m_IsInitialized = false
-- endregion

-- region 公開成員變數

-- endregion

-- region 私有函式

-- endregion

-- region 公開函式

-- endregion

-- region 事件處理

-- endregion
```

---

## 📝 LuaDoc 註解模板

### 模組註解

```lua
---@class ModuleName
---@author 作者
---@telephone 分機
---@version 1.0
---@date YYYY.MM.DD
ModuleName = {}
local this = ModuleName
```

### 函式註解

```lua
---函式說明
---@param iParam1 number 參數1說明
---@param iParam2 string|nil 參數2說明（可選）
---@return boolean 返回值說明
function this.DoSomething(iParam1, iParam2)
end
```

### 成員變數型別標註

```lua
---@type number 計數器
private.m_Counter = 0

---@type table<number, string> 名稱字典
private.m_Dic_NameById = {}
```

---

## ⚠️ 絕對禁止

| 禁止項目 | 原因 |
|---------|------|
| ❌ `goto` | 破壞結構化流程控制 |
| ❌ `self`（用 `this` 代替） | 統一模組引用方式 |
| ❌ 省略 `local` | 全域污染，效能損耗 |

```lua
-- ❌ 禁止使用 self
function ModuleName:DoSomething()
    self.m_Counter = 0
end

-- ✅ 使用 this
function this.DoSomething()
    private.m_Counter = 0
end
```

```lua
-- ❌ 禁止省略 local
TempValue = 100

-- ✅ 必須加 local
local _TempValue = 100
```

---

## 🔢 陣列索引

```lua
-- ✅ Lua 陣列從 1 開始
for i = 1, #m_List_Items do
    local _Item = m_List_Items[i]
end

-- ✅ 使用 ipairs 遍歷陣列
for _, _Item in ipairs(m_List_Items) do
    -- 處理
end

-- ❌ 從 0 開始（C# 思維陷阱）
for i = 0, #m_List_Items - 1 do
end
```

---

## 🛡️ nil 檢查

```lua
-- ✅ 正確的 nil 檢查
if not iValue then
    return
end

-- ✅ 安全存取
local _Name = iData and iData.Name or "Unknown"

-- ❌ 使用 == nil（冗長）
if iValue == nil then
    return
end
```

---

## 🧹 Dispose 清理

每個模組**必須**有 Dispose 函式：

```lua
function this.Dispose()
    -- 移除事件監聽
    if private.m_Button_Start then
        private.m_Button_Start:RemoveAllListeners()
    end

    -- 清空引用
    private.m_Button_Start = nil
    private.m_IsInitialized = false
    private.m_List_Items = {}
    private.m_Dic_NameById = {}
end
```

---

## 📊 Data 型別驗證（串檔）

### 核心對照

```
Assets/AI USE/Data/*_AIUSE_C.txt  →  Assets/04.LuaScript/Data/*.lua
```

| C# Type | DataReader 方法 | @type |
|---------|-----------------|-------|
| `BYTE` | `ReadByte()` | `number` |
| `BYTE`（布林語意） | `ReadByte() == 1` | `boolean` |
| `WORD` | `ReadUInt16()` | `number` |
| `SMALL` | `ReadInt16()` | `number` |
| `DWORD` | `ReadUInt32()` | `number` |
| `INT` | `ReadInt32()` | `number` |
| `UINT64` | `ReadUInt64()` | `number` |
| `FLOAT` | `ReadFloat()` | `number` |
| `STRING` | `ReadString()` | `string` |

### 驗證規則

```lua
-- ✅ 型別正確
m_HP = iReader:ReadUInt32(),        -- DWORD
m_Level = iReader:ReadUInt16(),     -- WORD
m_Damage = iReader:ReadInt16(),     -- SMALL

-- ✅ 布林語意（欄位名含「開啟」「是否」「啟用」）
m_IsOpen = iReader:ReadByte() == 1, -- @type boolean

-- ✅ 連續 3+ 同類型 → table + for 迴圈
m_RoleTags = {},
for _i = 1, 6 do
    table.insert(_Data.m_RoleTags, iReader:ReadByte())
end

-- ✅ 空欄位 → m_Reserved + 編號
m_Reserved1 = iReader:ReadUInt32(),
m_Reserved2 = iReader:ReadUInt32(),
```

```lua
-- ❌ 型別錯誤（DWORD 用了 ReadUInt16）
m_HP = iReader:ReadUInt16(),        -- 應該是 ReadUInt32

-- ❌ 順序錯誤（必須與 _AIUSE_C.txt 完全一致）
-- ❌ 布林欄位沒有用 == 1
m_IsOpen = iReader:ReadByte(),      -- 應該是 ReadByte() == 1
```

---

## ✅ 快速檢查清單

### 一般程式碼
- [ ] 成員變數用 `private.m_`
- [ ] 參數用 `i` 前綴
- [ ] 區域變數用 `local _` 前綴
- [ ] 所有變數都有 `local`
- [ ] 沒有使用 `self`（用 `this`）
- [ ] 沒有使用 `goto`
- [ ] 有 LuaDoc 註解
- [ ] 使用 `region` 組織程式碼
- [ ] 陣列索引從 1 開始
- [ ] 有 `Dispose()` 清理函式

### 串檔 Data
- [ ] 型別與 `_AIUSE_C.txt` 對應正確
- [ ] 欄位順序完全一致
- [ ] 布林語意欄位使用 `ReadByte() == 1`
- [ ] 連續 3+ 欄位使用 table
- [ ] 空欄位使用 `m_Reserved`
- [ ] 註解格式完整（@class, @field, @type）

---

## 例外情況

- xLua 綁定呼叫 C# 時需加 `CS.` 前綴（如 `CS.UnityEngine.Time.deltaTime`）
- 第三方模組的 API 不強制 `i` 參數前綴
- 效能熱區可用 `local` 快取全域函式（如 `local table_insert = table.insert`）
