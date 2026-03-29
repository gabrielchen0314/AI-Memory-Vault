---
type: project-overview
project: SpinWithFriends
workspace: d:\MyWork\SpinWithFriends
engine: Unity (XLua)
company: LIFEOFDEVELOPMENT
author: gabrielchen
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "Unity + XLua 雙層架構遊戲，C# 負責系統層，Lua 負責遊戲邏輯層"
tags: [unity, xlua, lua, csharp, game]
---

# SpinWithFriends 專案總覽

## 基本資訊

| 欄位 | 值 |
|------|-----|
| 專案名稱 | SpinWithFriends |
| 公司 | LIFEOFDEVELOPMENT |
| 引擎 | Unity + XLua |
| 作者 | gabrielchen |
| 本機路徑 | `d:\MyWork\SpinWithFriends` |
| 場景 | `Assets/01.Scenes/Main.unity`（唯一場景） |

---

## 整體架構

```
C# Runtime 層
  Main.cs (EStateOfGame FSM)
    └── XLuaManager (LuaEnv 管理)
          └── Lua 邏輯層
                ├── GDefines.lua  (C# 類別綁定至 Lua 全域)
                ├── GEnums.lua    (全域列舉)
                └── Game.lua      (Init → UIMgr.Init → UIMgr.Open)
```

### 層次說明

| 層次 | 說明 |
|------|------|
| **C# Runtime** | Main.cs (FSM) → XLuaManager → LuaEnv |
| **Lua 啟動** | GDefines → Game.Init → UIMgr.Init → UIMgr.Open("Main_Controller") |
| **UI 系統** | Facade(UIMgr) → Queue → Lifecycle → Model/Stack/Layer/GC |
| **登入系統** | LoginMgr.lua ↔ JSON ↔ LoginManager.cs ↔ ILoginProvider |
| **日誌系統** | LuaLogSystem.lua → C# SystemLogBase（附加 Lua 堆疊資訊） |
| **Require** | RequireEx.lua（引用計數 + UnRequire 自動釋放） |

### C# ↔ Lua 橋接方式
- **Lua Call C#**：透過 `[XLua.LuaCallCSharp]` 屬性暴露類別
- **資料傳遞**：JSON 字串（避免生成大量 XLua Wrap 代碼）
- **C# Call Lua**：透過 `ILuaReflection.cs` interface（`[CSharpCallLua]`）

---

## 專案目錄結構

```
Assets/
├── 01.Scenes/          — 場景（Main.unity）
├── 02.Art/             — 美術資源
├── 03.RunTimeScripts/  — C# 腳本
│   ├── Main.cs                    — 遊戲主入口 FSM
│   ├── Auth/                      — 登入系統
│   │   ├── ELoginChannel.cs
│   │   ├── EditorLoginProvider.cs
│   │   ├── LineLoginProvider.cs
│   │   └── LoginManager.cs
│   ├── Lua/
│   │   └── ILuaReflection.cs      — C# Call Lua 介面映射
│   ├── Manager/
│   │   └── XLuaManager.cs         — XLua 環境 Singleton
│   └── ProjectData/
│       └── ProjectData_Default.cs — 台版 CDN 設定
├── 04.LuaScripts/      — Lua 腳本（主要邏輯層）
│   ├── Common/         — RequireEx, LuaDebug
│   ├── Global/         — GDefines, GEnums
│   ├── InheritedBase/  — LuaLogSystem, UIConfig, UIControllerBase
│   ├── Logic/
│   │   ├── Game.lua
│   │   └── Mgr/
│   │       ├── LoginMgr.lua
│   │       └── UI/     — UI 管理系統（7個模組）
│   └── UI/
│       └── Main_Controller.lua
└── Editor/             — Unity 編輯器工具
```

---

## C# 核心類別

| 類別 | 路徑 | 說明 |
|------|------|------|
| `Main` | 03.RunTimeScripts/Main.cs | FSM 主入口（EStateOfGame） |
| `XLuaManager` | 03.RunTimeScripts/Manager/XLuaManager.cs | LuaEnv 單例管理 |
| `LoginManager` | 03.RunTimeScripts/Auth/LoginManager.cs | 登入 Facade [LuaCallCSharp] |
| `ILuaReflection` | 03.RunTimeScripts/Lua/ILuaReflection.cs | C# Call Lua 介面 |
| `ProjectData_Default` | 03.RunTimeScripts/ProjectData/ | 台版 CDN 設定 |

## Lua 全域綁定（GDefines.lua）

| Lua 全域 | C# 類別 |
|----------|---------|
| `ProjectMgr` | `CS.GameTools.Project.ProjectMgr` |
| `SystemLogBase` | `CS.GameTools.SystemLogBase` |
| `LoginManager` | `CS.LoginManager`（MonoSingleton） |

---

## 分析文件清單（根目錄）

| 文件 | 說明 |
|------|------|
| `GUIController_Analysis.md` | 舊版 Unreal GUIController.uc 分析（4504行 God Class） |
| `UI_Analysis.md` | 舊版 UGUIManager.cs 分析（1800行，參考優化方向） |
| `UIMgr_Analysis_Report.md` | 現行 UIMgr.lua 模組化架構分析 |
| `UIMgr_Analysis.md` | 舊版 UIMgr.lua（3379行）分析 |
| `README.md` | 簡短標題（ProjectBase） |

---

## 已知問題（來自 UIMgr_Analysis_Report.md）

- ❌ **BUG**：`UIAnimationMgr.PlayUIAnimation` 關閉時錯誤呼叫 `OnOpenUIAnimation`（應為 `OnCloseUIAnimation`）
- ❌ `UIMgr.FixedUpdate()` 被呼叫但無實作
- ❌ 硬編碼 UI 名稱（未使用 `EUIPrefabName`）
- ⚠️ `Update()` 每幀遍歷所有 Controller（應維護已開啟 UI 列表）
- ⚠️ 15+ 處被註解掉的程式碼
