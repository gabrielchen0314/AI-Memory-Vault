---
type: api-map
project: SpinWithFriends
module: LoginMgr
layer: lua
file: Assets/04.LuaScripts/Logic/Mgr/LoginMgr.lua
bridges_to: Assets/03.RunTimeScripts/Auth/LoginManager.cs
author: gabrielchen
version: 1.0
since: XluaBase
code_date: 2026.02.12
doc_created: 2026.03.29
last_updated: 2026.03.29
health: ✅ 健康
ai_summary: "Lua 登入 Facade，7個公開API，JSON橋接C#LoginManager，支援Editor/Line渠道"
tags: [lua, api-map, login, auth, facade]
---

# LoginMgr — API Map

## 模組概覽

| 欄位 | 值 |
|------|-----|
| **模組路徑** | `Assets/04.LuaScripts/Logic/Mgr/LoginMgr.lua` |
| **橋接 C#** | `Assets/03.RunTimeScripts/Auth/LoginManager.cs` |
| **設計模式** | Facade（隱藏 C# ILoginProvider 實作細節） |
| **資料傳遞** | JSON 字串（C# Callback → `cjson.decode` → Lua Table） |
| **公開 API** | 7 個 |
| **私有函式** | 2 個 |

---

## 相依性

| 相依 | 類型 | 用途 |
|------|------|------|
| `LoginManager` | C# MonoSingleton `[LuaCallCSharp]` | 主要橋接對象 |
| `cjson` | Lua 內建 | JSON 解碼（`cjson.decode`） |
| `ProjectMgr` | C# Binding（GDefines） | `IsRelease()` 控制 Debug log |
| `SystemLogBase` | C# Binding（GDefines） | `New("LoginMgr", true, "cyan", "white")` |
| `EDebugType` | 全域列舉（GEnums） | Log 類型（Log/Warning/Error） |
| `ELoginChannel` | C# Enum Binding | 渠道識別（Editor=0, Line=1） |

---

## 私有成員

| 名稱 | 型別 | 說明 |
|------|------|------|
| `private.m_DebugConfig` | `DebugMsgBase \| nil` | Debug 配置，Release 模式為 nil（關閉 log） |

---

## 公開 API（7個）

### `LoginMgr.Init()`

初始化模組。非 Release 建立 DebugConfig；Release 設為 nil。應在 `Game.Init()` 呼叫一次。

```lua
LoginMgr.Init()
```

---

### `LoginMgr.GetAvailableChannels()`

```lua
---@return table 渠道名稱陣列
```

取得所有可用登入渠道。直接呼叫 C#，同步回傳。

```lua
local _Channels = LoginMgr.GetAvailableChannels()
-- 結果: {"Line", "Editor"}
```

---

### `LoginMgr.InitChannel(iChannel, iCallback)`

```lua
---@param iChannel    ELoginChannel
---@param iCallback   function|nil   callback(_Result: AuthResult)
```

初始化指定渠道，結果透過 callback 非同步回傳。

```lua
LoginMgr.InitChannel(ELoginChannel.Line, function(_Result)
    if _Result and _Result.m_IsSuccess then
        -- 初始化成功
    end
end)
```

---

### `LoginMgr.Login(iChannel, iCallback)`

```lua
---@param iChannel    ELoginChannel
---@param iCallback   function|nil   callback(_Result: AuthResult)
```

執行登入。AuthResult 欄位：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `m_IsSuccess` | boolean | 是否成功 |
| `m_ChannelName` | string | 渠道名稱 |
| `m_UserId` | string | 使用者 ID |
| `m_ErrorMessage` | string | 失敗時的錯誤訊息 |

```lua
LoginMgr.Login(ELoginChannel.Line, function(_Result)
    if _Result and _Result.m_IsSuccess then
        print("UserId: " .. _Result.m_UserId)
    else
        print("Error: " .. (_Result and _Result.m_ErrorMessage or "nil"))
    end
end)
```

---

### `LoginMgr.Logout()`

執行登出，同步，無 callback。

---

### `LoginMgr.GetAuthState()`

```lua
---@return number  EAuthState 列舉值
```

---

### `LoginMgr.IsLoggedIn()`

```lua
---@return boolean
```

---

### `LoginMgr.GetCurrentChannelName()`

```lua
---@return string  未登入時回傳空字串
```

---

## 私有函式（2個）

### `private.DecodeResult(iJsonStr)`

```lua
---@param  iJsonStr  string
---@return table|nil
```

JSON → Lua Table。空字串或解碼失敗回傳 nil，並記錄 Error log。使用 `pcall` 保護。

### `private.Log(iType, iMsg)`

```lua
---@param iType  number           EDebugType
---@param iMsg   string|function  延遲執行函數可避免 Release 模式無謂字串拼接
```

---

## C# 對照表（LoginManager.cs）

| Lua 呼叫 | C# 對應 | 模式 |
|---------|---------|------|
| `GetAvailableChannels()` | `LoginManager:GetAvailableChannels()` | 同步，回傳 JSON 字串 |
| `InitChannel(ch, cb)` | `LoginManager:InitChannel(channel, Action<string>)` | 非同步，callback JSON |
| `Login(ch, cb)` | `LoginManager:Login(channel, Action<string>)` | 非同步，callback JSON |
| `Logout()` | `LoginManager:Logout()` | 同步 |
| `GetAuthState()` | `LoginManager.AuthState` | Property |
| `IsLoggedIn()` | `LoginManager.IsLoggedIn` | Property |
| `GetCurrentChannelName()` | `LoginManager.CurrentChannelName` | Property |

---

## 健康狀態

| 檢查項目 | 狀態 |
|----------|------|
| 所有公開 API 都有記錄 | ✅ |
| 函式簽名與程式碼一致 | ✅ |
| 範例程式碼可執行 | ✅ |
| 依賴模組清單正確 | ✅ |
