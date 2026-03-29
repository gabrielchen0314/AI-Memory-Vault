---
type: api-map
project: SpinWithFriends
module: LoginMgr
layer: lua
depends_on: [LoginManager.cs, cjson, ProjectMgr, SystemLogBase]
author: gabrielchen
version: 1.0
since: XluaBase
created: 2026.02.12
doc_created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "Lua 側登入管理器，Facade 封裝 C# LoginManager，JSON 橋接渠道登入/登出"
tags: [lua, api-map, login, auth]
---

# LoginMgr — API Map

## 模組概覽

| 欄位 | 值 |
|------|-----|
| 模組路徑 | `Assets/04.LuaScripts/Logic/Mgr/LoginMgr.lua` |
| 橋接對象 | `Assets/03.RunTimeScripts/Auth/LoginManager.cs` |
| 設計模式 | Facade（隱藏 C# ILoginProvider 細節） |
| 資料傳遞 | JSON 字串（C# → cjson.decode → Lua Table） |

---

## 相依性

| 相依 | 類型 | 說明 |
|------|------|------|
| `LoginManager` | C# MonoSingleton | `[LuaCallCSharp]` 暴露的 C# 登入管理器 |
| `cjson` | Lua 內建 | JSON 編解碼 |
| `ProjectMgr` | C# Binding（GDefines） | `IsRelease()` 用於 Debug log 控制 |
| `SystemLogBase` | C# Binding（GDefines） | `New("LoginMgr", true, "cyan", "white")` |
| `EDebugType` | 全域列舉（GEnums） | Log 類型常數 |
| `ELoginChannel` | C# Enum（Binding） | 登入渠道識別 |

---

## 私有成員

| 名稱 | 類型 | 說明 |
|------|------|------|
| `private.m_DebugConfig` | `DebugMsgBase \| nil` | Debug 日誌設定，Release 模式為 nil |

---

## 公開 API

### `LoginMgr.Init()`

```lua
function LoginMgr.Init()
```

初始化 LoginMgr 模組。非 Release 模式時建立 DebugConfig；Release 模式設為 nil。
應在遊戲啟動時（`Game.Init()`）呼叫一次。

---

### `LoginMgr.GetAvailableChannels()`

```lua
---@return table 渠道名稱陣列
function LoginMgr.GetAvailableChannels()
```

取得所有可用的登入渠道名稱陣列。

**回傳範例**：
```lua
-- {"Line", "Editor"}
local _Channels = LoginMgr.GetAvailableChannels()
```

---

### `LoginMgr.InitChannel(iChannel, iCallback)`

```lua
---@param iChannel ELoginChannel 渠道列舉
---@param iCallback function|nil 完成回呼，參數為 Lua Table (AuthResult)
function LoginMgr.InitChannel(iChannel, iCallback)
```

初始化指定登入渠道。結果透過 callback 回傳。

**使用範例**：
```lua
LoginMgr.InitChannel(ELoginChannel.Line, function(_Result)
    if _Result and _Result.m_IsSuccess then
        print("渠道初始化成功")
    end
end)
```

---

### `LoginMgr.Login(iChannel, iCallback)`

```lua
---@param iChannel ELoginChannel 渠道列舉
---@param iCallback function|nil 完成回呼，參數為 Lua Table (AuthResult)
function LoginMgr.Login(iChannel, iCallback)
```

執行指定渠道登入。成功時 `_Result.m_IsSuccess == true`。

**AuthResult 欄位**：
| 欄位 | 型別 | 說明 |
|------|------|------|
| `m_IsSuccess` | boolean | 是否成功 |
| `m_ChannelName` | string | 渠道名稱 |
| `m_UserId` | string | 使用者 ID |
| `m_ErrorMessage` | string | 失敗時的錯誤訊息 |

**使用範例**：
```lua
LoginMgr.Login(ELoginChannel.Line, function(_Result)
    if _Result and _Result.m_IsSuccess then
        print("登入成功, UserId: " .. _Result.m_UserId)
    else
        print("登入失敗: " .. (_Result and _Result.m_ErrorMessage or "nil"))
    end
end)
```

---

### `LoginMgr.Logout()`

```lua
function LoginMgr.Logout()
```

執行登出，直接呼叫 `LoginManager:Logout()`，無回呼。

---

### `LoginMgr.GetAuthState()`

```lua
---@return number EAuthState 列舉值
function LoginMgr.GetAuthState()
```

取得當前認證狀態（對應 C# `EAuthState` 列舉值）。

---

### `LoginMgr.IsLoggedIn()`

```lua
---@return boolean
function LoginMgr.IsLoggedIn()
```

是否已完成登入。

---

### `LoginMgr.GetCurrentChannelName()`

```lua
---@return string 渠道名稱，未登入時回傳空字串
function LoginMgr.GetCurrentChannelName()
```

取得當前登入渠道名稱。

---

## 私有函數

### `private.DecodeResult(iJsonStr)`

```lua
---@param iJsonStr string
---@return table|nil
function private.DecodeResult(iJsonStr)
```

JSON 字串解碼為 Lua Table。空字串或解碼失敗時回傳 nil 並記錄 Error log。使用 `pcall` 保護。

### `private.Log(iType, iMsg)`

```lua
---@param iType number EDebugType 列舉值
---@param iMsg string|function 訊息或延遲訊息函數
function private.Log(iType, iMsg)
```

Debug 日誌輸出。遵循延遲執行慣例（iMsg 傳入 function 避免 Release 模式字串拼接）。

---

## 對應 C# API（LoginManager.cs）

| C# 方法 | 說明 |
|---------|------|
| `LoginManager:GetAvailableChannels()` | 回傳 JSON 陣列字串 |
| `LoginManager:InitChannel(channel, Action<string>)` | 非同步，callback 傳 JSON |
| `LoginManager:Login(channel, Action<string>)` | 非同步，callback 傳 JSON |
| `LoginManager:Logout()` | 同步 |
| `LoginManager.AuthState` | Property，EAuthState |
| `LoginManager.IsLoggedIn` | Property，bool |
| `LoginManager.CurrentChannelName` | Property，string |

## 登入渠道（ELoginChannel.cs）

| 渠道 | 值 | 條件編譯 |
|------|-----|---------|
| `Editor` | 0 | `#if UNITY_EDITOR` |
| `Line` | 1 | `#if LINE_SDK` |

---

## 健康狀態

| 檢查項目 | 狀態 |
|----------|------|
| 所有公開 API 都有記錄 | ✅ |
| 函式簽名與程式碼一致 | ✅ |
| 範例程式碼可執行 | ✅ |
| 依賴模組清單正確 | ✅ |
