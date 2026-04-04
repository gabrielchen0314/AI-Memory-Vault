---
type: project-overview
project: SpinWithFriends
workspace: d:\MyWork\SpinWithFriends
engine: Unity (XLua)
company: LIFEOFDEVELOPMENT
author: gabrielchen
version: 1.0
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "Unity + XLua 雙層架構遊戲；C# 負責 FSM 啟動/資源/登入，Lua 負責所有遊戲邏輯與 UI"
tags: [unity, xlua, lua, csharp, game]
---

# SpinWithFriends — 專案總覽

## 基本資訊

| 欄位 | 值 |
|------|-----|
| 專案名稱 | SpinWithFriends |
| 公司 | LIFEOFDEVELOPMENT |
| 引擎 | Unity + XLua |
| 作者 | gabrielchen |
| 本機路徑 | `d:\MyWork\SpinWithFriends` |
| 唯一場景 | `Assets/01.Scenes/Main.unity` |
| 第三方庫 | GameTools（內部庫）、XLua、Addressables、LINE SDK、Newtonsoft.Json |

---

## 整體架構

```
C# Runtime 層（系統/引擎）
  Main.cs : MonoSingleton
    ├── EStateOfGame FSM (15個狀態)
    ├── XLuaManager (LuaEnv, CustomLoader, GC Tick)
    ├── ResourceMgr (Addressables 載入)
    ├── LoginManager (ILoginProvider 策略)
    └── MainThreadDispatcher (非同步回調轉主執行緒)

Lua 邏輯層（遊戲/業務）
  GDefines.lua (C# 全域綁定)
  GEnums.lua (全域列舉定義)
  Game.lua (Init / Update / FixedUpdate / LateUpdate)
    ├── UIMgr (Facade + 6子模組)
    └── LoginMgr (登入 Facade)
```

### 層次說明

| 層次 | 職責 |
|------|------|
| **C# Runtime** | Unity 生命週期、資源管理、登入 SDK 橋接、LuaEnv 管理 |
| **Lua 啟動** | GDefines 綁定 → Game.Init → UIMgr.Init → UIMgr.Open("Main_Controller") |
| **UI 系統** | Facade(UIMgr) → Queue → Lifecycle → Model/Stack/Layer/GC |
| **登入系統** | LoginMgr.lua ↔ JSON ↔ LoginManager.cs ↔ ILoginProvider(Editor/Line) |
| **日誌系統** | LuaLogSystem.lua → C# SystemLogBase（附 Lua debug.traceback） |
| **Require** | RequireEx.lua（引用計數 + 系統級 UnRequire 批次釋放） |

### C# ↔ Lua 橋接方式

| 方向 | 機制 |
|------|------|
| Lua → C# | `[XLua.LuaCallCSharp]` 暴露類別，GDefines.lua 綁定全域 |
| C# → Lua | `ILuaReflection` interface（`[CSharpCallLua]`），Main.cs 取得 Lua function ref |
| 資料傳遞 | JSON 字串（C# Callback 傳 JSON → `cjson.decode` → Lua Table） |
| 非同步安全 | `MainThreadDispatcher.Enqueue()` 確保 Lua callback 在主執行緒執行 |

---

## EStateOfGame FSM 流程

```
UnityInitialize
  → ProjectMgr.Init + XLuaManager.Do
  → PlayCG (空)
  → CheckNetwork
  → LoadExeConfig (空)
  → ResourceInitialize                  ← ResourceMgr.Initialize (Addressables)
  → NetWorkInitialize (空，保留擴充)
  → LuaInitialize                       ← require "Logic/Game" + Game.Init(callback)
  → InitFinish
  → [Error]                             ← 任何失敗都跳此
```

> 注：PlayCG / LoadExeConfig / LoadExeUpdateInfo / FTPSelect / LuaAndAssetsDownload 是保留狀態架構，目前直接跳過。

---

## 專案目錄結構

```
Assets/
├── 01.Scenes/
│   └── Main.unity                     — 唯一場景
├── 02.Art/                            — 美術資源（Addressables）
├── 03.RunTimeScripts/                 — C# 腳本（8個）
│   ├── Main.cs                        — FSM 主入口 ©2025 CHINESE GAMER
│   ├── Auth/
│   │   ├── ELoginChannel.cs           — 渠道列舉（Editor=0, Line=1）
│   │   ├── EditorLoginProvider.cs     — Editor 模擬登入 (#if UNITY_EDITOR)
│   │   ├── LineLoginProvider.cs       — LINE 登入 (#if LINE_SDK)
│   │   └── LoginManager.cs            — 登入 Facade [LuaCallCSharp] ©2026 LIFEOFDEVELOPMENT
│   ├── Lua/
│   │   └── ILuaReflection.cs          — C#→Lua 介面映射 [CSharpCallLua] ©2024 CHINESE GAMER
│   ├── Manager/
│   │   └── XLuaManager.cs             — LuaEnv 單例（CustomLoader, GC Tick=1s） ©2024 CHINESE GAMER
│   └── ProjectData/
│       └── ProjectData_Default.cs     — 台版 CDN 設定（Debug/QA/Release） ©2022 CHINESE GAMER
├── 04.LuaScripts/                     — Lua 腳本（17個）
│   ├── Common/
│   │   ├── LuaDebug.lua               — Editor 除錯工具
│   │   └── RequireEx.lua              — Require 引用計數管理
│   ├── Global/
│   │   ├── GDefines.lua               — C# → Lua 全域綁定（70+ 項）
│   │   └── GEnums.lua                 — 全域列舉（EUIStage/EFormLayerType/EUIOrderLayers/EUIOperation）
│   ├── InheritedBase/
│   │   ├── LuaLogSystem.lua           — Lua 日誌（封裝 SystemLogBase + Lua 堆疊）
│   │   ├── UIConfig.lua               — UIController 設定工廠（FullPage/HalfPage/Peak/Loading）
│   │   └── UIControllerBase.lua       — UI Controller 基底工廠函數（ViewRef 存取等）
│   ├── Logic/
│   │   ├── Game.lua                   — 遊戲主邏輯入口
│   │   └── Mgr/
│   │       ├── LoginMgr.lua           — 登入 Facade
│   │       └── UI/                    — UI 管理系統（7個子模組）
│   └── UI/
│       └── Main_Controller.lua        — 主選單 UI Controller
└── Editor/                            — Unity 編輯器工具
```

---

## C# 核心類別

| 類別 | 命名空間 | 說明 | 版權 |
|------|---------|------|------|
| `Main` | `Program` | FSM 主入口 + Lua 生命週期橋接 | ©2025 CHINESE GAMER |
| `XLuaManager` | `(Global)` | LuaEnv 單例、CustomLoader、GC Tick | ©2024 CHINESE GAMER |
| `LoginManager` | `Game.Auth` | 登入 Facade [LuaCallCSharp] | ©2026 LIFEOFDEVELOPMENT |
| `ELoginChannel` | `Game.Auth` | 登入渠道列舉（Editor=0, Line=1） | ©2026 LIFEOFDEVELOPMENT |
| `EditorLoginProvider` | `Game.Auth` | Editor 模擬登入 | ©2026 LIFEOFDEVELOPMENT |
| `LineLoginProvider` | `Game.Auth` | LINE SDK 登入 | ©2026 LIFEOFDEVELOPMENT |
| `ILuaReflection` | `(Global)` | C#→Lua 介面標記 | ©2024 CHINESE GAMER |
| `ProjectData_Default` | `GameTools.Project` | 台版 CDN 設定 | ©2022 CHINESE GAMER |

## GameTools 外部庫依賴（C#）

| 類別 | 功能 |
|------|------|
| `MonoSingleton<T>` | Unity MonoBehaviour 單例基底 |
| `Singleton<T>` | 非 MonoBehaviour 單例基底 |
| `StateMachine<T>` | FSM 狀態機 |
| `BaseState<T>` | FSM 狀態基底 |
| `SystemLogBase` | 帶標籤 + 顏色的日誌系統 |
| `ProjectMgr` | 專案環境管理（IsRelease/IsEditor） |
| `ResourceMgr` | Addressables 資源管理器 |
| `AddressableLoader` | Addressables 實作 |
| `VersionMgr` | 版本管理 |
| `DownloadMgr` | 下載管理 |
| `MainThreadDispatcher` | 非同步→主執行緒轉發 |
| `ViewRefLite` | UI 視圖引用容器（Inspector 綁定） |
| `ComponentDisposableRegistry` | Component 清理注冊 |

---

## Lua 全域綁定總覽（GDefines.lua）

### UnityEngine 基礎

| Lua 全域 | C# 類別 |
|----------|---------|
| `GameObject` | `CS.UnityEngine.GameObject` |
| `Transform` | `CS.UnityEngine.Transform` |
| `Debug` | `CS.UnityEngine.Debug` |
| `Vector2/3/4` | `CS.UnityEngine.Vector2/3/4` |
| `Color`, `Mathf`, `Time`, `Input` | UnityEngine 基礎 |
| `Canvas` | `CS.UnityEngine.Canvas` |
| `WaitForSeconds` | Coroutine 工具 |

### TMPro

| Lua 全域 | C# 類別 |
|----------|---------|
| `TMP_Text`, `TMP_InputField`, `TextMeshProUGUI` | TMPro 文字元件 |

### GameTools 核心

| Lua 全域 | C# 類別 |
|----------|---------|
| `GDebug` | `CS.GameTools.Debug` |
| `EDebugType` | `CS.GameTools.EDebugType` |
| `SystemLogBase` | `CS.GameTools.SystemLogBase` |
| `LuaLogSystem` | `InheritedBase/LuaLogSystem.lua`（Lua wrap） |
| `ProjectMgr` | `CS.GameTools.Project.ProjectMgr` |
| `XLuaManager` | `CS.XLuaManager` |

### GameTools UIExtension

| Lua 全域 | C# 類別 |
|----------|---------|
| `ViewRefLite` | `CS.GameTools.UIExtension.ViewRefLite` |
| `ButtonBase`, `SelectableEx` | 自定義 Button 元件 |
| `ESelectionState`, `SelectionStateConfig` | Button 狀態設定 |
| `ButtonStateSetGroupColor/Sprite` | Button 狀態組 |
| `UIRenderCtrl`, `UIRenderChangeColor/Sprite` | Render 控制器 |
| `EScrollDirection`, `VirtualScrollView`, `VirtualScrollItem` | 虛擬捲動清單 |
| `EGradientType`, `UIGradient` | 漸變色控制 |

### GameTools Resource / Version / Download

| Lua 全域 | C# 類別 |
|----------|---------|
| `ResourceMgr` | `CS.GameTools.Resource.ResourceMgr.Inst`（單例） |
| `AddressableLoader`, `ResourcesLoader` | 資源載入器 |
| `VersionMgr` | `CS.GameTools.Version.VersionMgr` |
| `DownloadMgr` | `CS.GameTools.Download.DownloadMgr` |

### 遊戲專用

| Lua 全域 | C# 類別 |
|----------|---------|
| `LoginManager` | `CS.Game.Auth.LoginManager.Inst`（單例） |
| `ELoginChannel` | `CS.Game.Auth.ELoginChannel` |
| `EAuthState` | `CS.GameTools.Auth.EAuthState` |
| `EAuthErrorCode` | `CS.GameTools.Auth.EAuthErrorCode` |

---

## 已知問題 / BUG

> 來源：程式碼靜態分析 + UIMgr_Analysis_Report.md

| 嚴重度 | 問題 | 位置 |
|--------|------|------|
| ❌ BUG | `UILifecycle.Update()` 檢查 `_Controller.Update` 但 UIControllerBase 只定義 `OnUpdate`，導致 `OnUpdate` 永遠不被呼叫 | `UILifecycle.lua:Update()` |
| ❌ BUG | 關閉 UI 時 `PlayUIAnimation` 錯誤呼叫了 `OnOpenUIAnimation`（應為 `OnCloseUIAnimation`） | `UIAnimationMgr.PlayUIAnimation` |
| ❌ 問題 | `UIMgr.FixedUpdate()` 函式體為空，但 Main.cs 每幀呼叫 | `UIMgr.lua` |
| 🟡 中 | 硬編碼 UI 名稱字串（應使用常數或列舉） | `UILifecycle.lua` 載入邏輯 |
| 🟡 中 | `UILifecycle.Update()` 遍歷 `GetOpenedUIList()` 但 `OpenedList` 在 `Model` 中維護，建議合法性驗證 | `UILifecycle.lua` |
| 🟢 低 | 15+ 處被註解掉的程式碼需清理 | UI 系統各模組 |

---

## 分析文件清單（專案根目錄）

| 文件 | 主題 |
|------|------|
| `GUIController_Analysis.md` | 舊版 Unreal GUIController.uc 分析（歷史參考） |
| `UI_Analysis.md` | 舊版 UGUIManager.cs 分析（架構設計參考） |
| `UIMgr_Analysis_Report.md` | 現行 UIMgr.lua 模組化架構分析報告 |
| `UIMgr_Analysis.md` | 舊版 UIMgr.lua（3379行）分析 |
| `README.md` | 簡短標題（ProjectBase） |
