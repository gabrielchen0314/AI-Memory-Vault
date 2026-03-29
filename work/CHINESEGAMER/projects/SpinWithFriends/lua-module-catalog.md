---
type: module-catalog
project: SpinWithFriends
layer: lua
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "SpinWithFriends 全部 Lua 模組清單與職責"
tags: [lua, modules, architecture]
---

# SpinWithFriends — Lua 模組架構

## 模組完整清單

### Common 層

| 模組 | 路徑 | 職責 |
|------|------|------|
| `LuaDebug` | Common/LuaDebug.lua | Editor 模式除錯工具 |
| `RequireEx` | Common/RequireEx.lua | Lua Require 管理器（引用計數 + 自動釋放 UnRequire） |

### Global 層

| 模組 | 路徑 | 職責 |
|------|------|------|
| `GDefines` | Global/GDefines.lua | 全域定義（UnityEngine / TMPro / GameTools C# 綁定到 Lua） |
| `GEnums` | Global/GEnums.lua | 全域列舉（EUIStage, EFormLayerType, EUIOrderLayers, EUIOperation） |

### InheritedBase 層（基底類別）

| 模組 | 路徑 | 職責 |
|------|------|------|
| `LuaLogSystem` | InheritedBase/LuaLogSystem.lua | Lua 日誌系統，封裝 C# SystemLogBase，補充 Lua 堆疊資訊 |
| `UIConfig` | InheritedBase/UIConfig.lua | UI Controller 設定結構（UIConfig.New / FullPage / HalfPage） |
| `UIControllerBase` | InheritedBase/UIControllerBase.lua | UI Controller 基底類別（生命週期介面代理模式） |

### Logic 層

| 模組 | 路徑 | 職責 |
|------|------|------|
| `Game` | Logic/Game.lua | 遊戲主邏輯入口（Init / Update / FixedUpdate / LateUpdate） |
| `LoginMgr` | Logic/Mgr/LoginMgr.lua | Lua 登入管理器，Facade 封裝 C# LoginManager，JSON 橋接 |

### UI 管理系統（Logic/Mgr/UI/）

| 模組 | 職責 |
|------|------|
| `UIMgr` | UI 管理器主入口（Facade，對外統一 API） |
| `UIModel` | 資料模型（Controllers 引用、Stage 狀態、Visible、OpenedList） |
| `UIStack` | 全版 UI 堆疊（Push / Pop / Peek / GetPrevious，支援返回上一頁） |
| `UILayer` | UI 層級管理（排序順序、ORDER_BASE 常數） |
| `UILifecycle` | 生命週期管理（OpenInternal / CloseInternal，非同步流程） |
| `UIOperationQueue` | UI 操作佇列（序列化開關操作，EnqueueOpen / EnqueueClose） |
| `UIGarbageCollector` | UI 資源回收（層級數量限制 + 自動銷毀，LAYER_LIMITS） |

### UI Controllers

| 模組 | 路徑 | 職責 |
|------|------|------|
| `Main_Controller` | UI/Main_Controller.lua | 主選單 Controller（含 VirtualScrollView 範例） |

---

## UI 層級常數（UILayer.lua）

| 層級 | ORDER_BASE |
|------|-----------|
| FullPage | 1000 |
| HalfPage | 3000 |
| Peak | 5000 |
| TopMost | 7000 |
| Debug | 9000 |

## UI 層級上限（UIGarbageCollector.lua）

| 層級 | 最大數量 |
|------|---------|
| HalfPage | 5 |
| FullPage | 3 |
| Peak | 3 |
| TopMost | 1 |
| Debug | 無限制（-1） |

---

## UI 生命週期（EUIStage，共 12 階段）

```
None → LoadingFromResourceMgr → UIObjLoaded → Initializing → Initialized →
Opening → DoingOpenAnimation → Opened →
Closing → DoingCloseAnimation → Closed →
Destroying → Destroyed
```

---

## 全域列舉（GEnums.lua）

| 列舉 | 值域說明 |
|------|---------|
| `EUIStage` | UI 生命週期 12 階段 |
| `EFormLayerType` | UI 形式分層（HalfPage_Left/Right/Center, FullPage, Peak, Debug） |
| `EUIOrderLayers` | UI 排序層常數 |
| `EUIOperation` | UI 操作類型（Open / Close 等） |
