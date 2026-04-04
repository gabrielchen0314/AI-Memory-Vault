---
type: rule
domain: coding
category: lua-coding-style
workspace: _global
applies_to: [lua, xlua, tolua, unity]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, lua, xlua, naming, coding-style]
ai_summary: "Lua 編碼規範補充：private 封裝、this 模組引用、禁止 self/goto、LuaDoc 格式、模組結構、Debug 延遲字串優化。通用命名規則見 _global/rules/01-coding-style-universal.md。"
---

# Lua Coding Style

> 本規範為 `workspaces/_global/rules/01-coding-style-universal.md` 的 Lua 補充。  
> 通用命名（m_/i/_ 前綴、常數、布林、集合）請見全域規則。

---

## ⛔ Lua 特定禁止

| 禁止項目 | 原因 |
|---------|------|
| `self`（用 `this` 代替） | 統一模組引用方式 |
| 省略 `local` | 全域污染、效能損耗 |
| `goto` | 同全域規則 |

```lua
-- ❌ 禁止 self
function ModuleName:DoSomething()
    self.m_Counter = 0
end

-- ✅ 使用 this
function this.DoSomething()
    private.m_Counter = 0
end

-- ❌ 禁止省略 local
TempValue = 100

-- ✅ 必須加 local
local _TempValue = 100
```

---

## 1. 模組基本架構

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

return this
```

---

## 2. 模組/類別 LuaDoc 頭部

```lua
---@class ModuleName
---@author gabrielchen
---@version 1.0
---@since ProjectName 1.0
---@date 2026.04.04
ModuleName = {}
local this = ModuleName
local private = {}
```

---

## 3. 函式 LuaDoc

```lua
---驗證玩家名稱
---@param iPlayerName string 玩家名稱
---@param iMaxLength number|nil 最大長度（可選）
---@return boolean 是否有效
function this.ValidatePlayerName( iPlayerName, iMaxLength )
    local _MaxLen = iMaxLength or 20
    if( #iPlayerName > _MaxLen ) then
        return false
    end
    return true
end
```

---

## 4. 成員變數型別標注

```lua
---@type number 計數器
private.m_Counter = 0

---@type table<number, string> 名稱字典
private.m_Dic_NameById = {}

---@type boolean 是否已就緒
private.m_IsReady = false
```

---

## 5. 陣列索引（Lua 從 1 開始）

```lua
-- ✅ 正確
for i = 1, #private.m_List_Items do
    local _Item = private.m_List_Items[i]
end

-- ✅ 使用 ipairs
for _, _Item in ipairs( private.m_List_Items ) do
    -- 處理
end

-- ❌ 錯誤（C# 思維陷阱）
for i = 0, #private.m_List_Items - 1 do
end
```

---

## 6. Debug 延遲字串優化

避免 Debug 關閉時仍執行字串連接：

```lua
-- ❌ 錯誤：總是執行字串操作
private.Debugger( EDebugMsgType.Log, "數值: " .. value )

-- ✅ 正確：以 function 延遲執行
private.Debugger( EDebugMsgType.Log, function()
    return string.format( "數值: %d", value )
end )
```

---

## 7. Dispose 清理模式

```lua
function this.Dispose()
    -- 清理事件綁定
    if( private.m_EventHandler ) then
        EventMgr.Remove( private.m_EventHandler )
        private.m_EventHandler = nil
    end

    -- 重置成員變數
    private.m_Counter = 0
    private.m_IsInitialized = false
end
```
