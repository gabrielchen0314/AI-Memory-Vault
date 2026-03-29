---
type: module-catalog
project: SpinWithFriends
company: LIFEOFDEVELOPMENT
layer: lua
total_lua_files: 17
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "SpinWithFriends 全部 17 個 Lua 模組：職責、對外 API、依賴關係（v2 修正版）"
tags: [lua, modules, architecture, ui, api]
---

# SpinWithFriends — Lua 模組架構 (v2)

> ⚠️ v2 修正：`EFormLayerType` 只有 `Half=0` / `Full=1`（非分左右；使用 `EUIOrderLayers` 決定層級）

---

## Manager 清單

| Manager | 路徑 | 職責 | 主要對外函式 |
|---------|------|------|------------|
| `UIMgr` | Logic/Mgr/UI/UIMgr.lua | UI 系統主 Facade | `Init` `Dispose` `Open` `Close` `Back` `Preload` `IsOpened` `IsVisible` `GetUIStage` `GetCurrentFullPageUI` |
| `LoginMgr` | Logic/Mgr/LoginMgr.lua | 登入 Facade | `Init` `GetAvailableChannels` `InitChannel` `Login` `Logout` `GetAuthState` `IsLoggedIn` `GetCurrentChannelName` |

---

## Common 層（2個）

| 模組 | 路徑 | 職責 | 主要對外函式 |
|------|------|------|------------|
| `RequireEx` | Common/RequireEx.lua | Require 引用計數管理 | `Require(systemName, path)` `UnRequire(systemName, path?)` `GetRefCount(path)` |
| `LuaDebug` | Common/LuaDebug.lua | Editor 除錯工具 | （Editor only，內部工具） |

---

## Global 層（2個）

| 模組 | 路徑 | 職責 |
|------|------|------|
| `GDefines` | Global/GDefines.lua | 70+ C# 類別綁定為 Lua 全域（於此 require 後自動生效） |
| `GEnums` | Global/GEnums.lua | 全域列舉定義（於 GDefines 中自動 require） |

---

## InheritedBase 層（3個）

| 模組 | 路徑 | 職責 | 主要對外函式 / 工廠 |
|------|------|------|-------------------|
| `LuaLogSystem` | InheritedBase/LuaLogSystem.lua | Lua 日誌（封裝 SystemLogBase + Lua 堆疊） | `New(name, enable, fgColor, bgColor)` → `Log/LogInfo/LogWarning/LogError` |
| `UIConfig` | InheritedBase/UIConfig.lua | UI Controller 設定工廠 | `New` `FullPage` `HalfPage` `Peak` `Loading` `Set*(config)` 鏈式設定 |
| `UIControllerBase` | InheritedBase/UIControllerBase.lua | UI Controller 基底工廠函數 | `UIControllerBase(config)` → 回傳含 Hooks + ViewRef 存取的 table |

### UIControllerBase 生命週期 Hooks

```lua
function this:OnInit()     end  -- 初始化（非同步前），載入後調用一次
function this:OnOpen(...)  end  -- 每次開啟時
function this:OnOpened()   end  -- 開啟動畫完成後
function this:OnReopen(...) end -- 已 Opened 再次 Open 時
function this:OnClose()    end  -- 關閉開始
function this:OnClosed()   end  -- 關閉完成 + Prefab 已釋放
function this:OnUpdate()   end  -- 每 Update（⚠️ 目前有 BUG 無法被呼叫，見下方）
function this:OnDestroy()  end  -- GC 銷毀前
```

> ⚠️ **BUG**：`UILifecycle.Update()` 檢查 `_Controller.Update`（不存在）導致 `OnUpdate` 永遠不呼叫。

### UIConfig 工廠快捷方法

| 方法 | FormLayerType | UIOrderLayer |
|------|--------------|-------------|
| `FullPage(name, prefab)` | Full | FullPage（1000） |
| `HalfPage(name, prefab)` | Half | HalfPage（3000） |
| `Peak(name, prefab)` | Half | Peak（5000） |
| `Loading(name, prefab)` | Full | TopMost（7000） |

---

## Logic 層（10個）

### Game 主入口

| 模組 | 路徑 | 職責 | 主要對外函式 |
|------|------|------|------------|
| `Game` | Logic/Game.lua | 遊戲主邏輯入口 | `Init(callback)` `Update` `FixedUpdate` `LateUpdate` `OnApplicationFocus/Pause/Quit` |

> `Game.Init` 做的事：載入所有必要模組 → `UIMgr.Init()` → `UIMgr.Open("Main_Controller")` → 呼叫 callback

### UI 管理系統（Logic/Mgr/UI/，7個模組）

| 模組 | 職責 | 主要對外函式 |
|------|------|------------|
| `UIModel` | 資料層：Controllers Map / Stage / Visible / LoadingCallbacks | `RegisterController` `GetController` `RequireController` `SetUIStage` `GetUIStage` `SetUIVisible` `AddLoadingCallback` `PopLoadingCallbacks` |
| `UIStack` | 全版 UI 導航堆疊（僅 Full 類型） | `Push` `Pop` `Peek` `GetPrevious` `Remove` `Contains` `GetCount` |
| `UILayer` | Canvas SortingOrder 管理 | `Init` `AddToLayer` `RemoveFromLayer` `MoveToTop` `GetLayerTransform` `GetLayerCount` |
| `UILifecycle` | 非同步開關流程（12階段生命週期） | `Init` `Dispose` `OpenInternal` `CloseInternal` `Preload` `Update` `SetGarbageCollector` |
| `UIOperationQueue` | 序列化操作（防並發衝突） | `EnqueueOpen` `EnqueueClose` `IsProcessing` `HasPendingOperations` `RemoveController` |
| `UIGarbageCollector` | 超限自動銷毀最舊 UI | `Init` `RecordOpen` `CheckAndClean` `DestroyUI` `SetLayerLimit` `GetLayerUICount` |

---

## UI Controllers 層（1個）

| 模組 | 路徑 | 職責 |
|------|------|------|
| `Main_Controller` | UI/Main_Controller.lua | 主選單 UI Controller（含 VirtualScrollView 範例） |

> **命名規則**：所有 UI Controller 存放於 `UI/` 目錄，命名為 `{ScreenName}_Controller.lua`

---

## 依賴關係說明

```
GDefines.lua
  ├── require GEnums.lua             (全域列舉)
  ├── require RequireEx              (Require 管理)
  └── bind LuaLogSystem             (Lua 日誌)

Game.lua
  ├── require GDefines               (所有全域綁定)
  ├── RequireEx.Require UIConfig
  ├── RequireEx.Require UIControllerBase
  ├── RequireEx.Require UIMgr
  └── RequireEx.Require LoginMgr

UIMgr.lua
  ├── RequireEx.Require UIModel
  ├── RequireEx.Require UIStack
  ├── RequireEx.Require UILayer
  ├── RequireEx.Require UIOperationQueue
  ├── RequireEx.Require UILifecycle
  └── RequireEx.Require UIGarbageCollector

UILifecycle.lua
  ├── 接收 UIModel (Init 參數)
  ├── 接收 UIStack (Init 參數)
  ├── 接收 UILayer (Init 參數)
  ├── 接收 UIGarbageCollector (SetGarbageCollector)
  └── 呼叫 ResourceMgr:InstantiateAsync / ReleaseInstance

UIGarbageCollector.lua
  └── 接收 UIModel (Init 參數)

RequireEx.lua（被所有系統使用）
  └── 系統卸載時自動 package.loaded[path] = nil + 呼叫 Dispose
```

---

## 重要常數

### EFormLayerType（GEnums.lua）

| 值 | 說明 |
|----|------|
| `Half = 0` | 半版 UI（不遮蓋後方，不入 Stack） |
| `Full = 1` | 全版 UI（入 Stack，返回上一頁時 restore） |

### EUIOrderLayers → ORDER_BASE（UILayer.lua）

| 層級 | 值 | ORDER_BASE | 說明 |
|------|-----|-----------|------|
| `FullPage` | 0 | 1000 | 全版主畫面 |
| `HalfPage` | 1 | 3000 | 半版面板 |
| `Peak` | 2 | 5000 | 彈窗、提示 |
| `TopMost` | 3 | 7000 | Loading、覆蓋層 |
| `Debug` | 4 | 9000 | 除錯介面 |

> ORDER_INCREMENT = 10（同層每個 UI 遞增 10）

### LAYER_LIMITS（UIGarbageCollector.lua）

| 層級 | 上限 | 說明 |
|------|------|------|
| HalfPage | 5 | 超過自動銷毀最舊（m_CanAutoDestroy=true 者） |
| FullPage | 3 | 同上 |
| Peak | 3 | 同上 |
| TopMost | 1 | 同上 |
| Debug | -1 | 無限制 |
