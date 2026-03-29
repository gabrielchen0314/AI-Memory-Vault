---
type: architecture
project: SpinWithFriends
company: LIFEOFDEVELOPMENT
author: gabrielchen
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "SpinWithFriends 架構決策記錄（ADR）：XLua 雙層架構、JSON 橋接、UI Facade 模組化、RequireEx 引用計數"
tags: [architecture, adr, design-patterns, unity, xlua]
---

# SpinWithFriends — 架構設計文件

---

## 高階架構圖

```
┌─────────────────────────────────────────────────────┐
│  Unity Engine                                        │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  C# Runtime Layer                             │   │
│  │                                               │   │
│  │  Main (MonoSingleton)                         │   │
│  │    ├─ EStateOfGame FSM ──→ LuaInitialize      │   │
│  │    ├─ XLuaManager (LuaEnv + CustomLoader)     │   │
│  │    ├─ ResourceMgr (Addressables)              │   │
│  │    ├─ LoginManager (ILoginProvider策略)       │   │
│  │    └─ MainThreadDispatcher                    │   │
│  │                                               │   │
│  │  GameTools 外部庫（FSM/Log/Resource/Auth）    │   │
│  └──────────────────────────────────────────────┘   │
│             ▲ [LuaCallCSharp] / JSON CB              │
│             ▼ [CSharpCallLua]                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  Lua Logic Layer                              │   │
│  │                                               │   │
│  │  GDefines (全域綁定) → GEnums (列舉)          │   │
│  │                                               │   │
│  │  Game.lua (Init/Update/Lifecycle)             │   │
│  │    ├─ UIMgr (Facade)                          │   │
│  │    │    ├─ UIModel (資料)                     │   │
│  │    │    ├─ UIStack (導航)                     │   │
│  │    │    ├─ UILayer (排序)                     │   │
│  │    │    ├─ UIOperationQueue (序列化)           │   │
│  │    │    ├─ UILifecycle (生命週期)              │   │
│  │    │    └─ UIGarbageCollector (GC)             │   │
│  │    └─ LoginMgr (登入 Facade)                  │   │
│  │                                               │   │
│  │  UI Controllers (Main_Controller...)          │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 元件職責一覽

| 元件 | 層次 | 職責 | 依賴 |
|------|------|------|------|
| `Main` | C# | FSM + 生命週期橋接到 Lua | XLuaManager, ResourceMgr, LoginManager |
| `XLuaManager` | C# | LuaEnv 管理，解析 Lua 腳本路徑 | Unity Application |
| `LoginManager` | C# | 登入渠道管理，JSON 橋接 | ILoginProvider, MainThreadDispatcher |
| `Game` | Lua | 遊戲主入口，呼叫所有 Mgr.Init | GDefines, UIMgr, LoginMgr |
| `UIMgr` | Lua | UI 系統 Facade，統一對外 API | 6個 UI 子模組 |
| `UILifecycle` | Lua | 非同步開關流程，12 階段管理 | UIModel, UIStack, UILayer, ResourceMgr |
| `UIGarbageCollector` | Lua | 超限 UI 自動銷毀 | UIModel |
| `RequireEx` | Lua | Lua 模組引用計數，避免記憶體洩漏 | LuaLogSystem |

---

## ADR（架構決策記錄）

### ADR-001：採用 XLua 作為 Lua 腳本層

**背景**：需要遊戲邏輯熱更（OTA），C# 不能直接熱更。

**決策**：C# 處理引擎/系統層，XLua 作為邏輯腳本層，全部遊戲業務邏輯以 Lua 實作。

**後果**：
- ✅ Lua 腳本可通過 OTA 更新、無須重新發版
- ✅ C# 只需確保橋接介面穩定
- ⚠️ 除錯難度增加（Lua 堆疊 + C# 堆疊）→ 用 `LuaLogSystem.debug.traceback` 緩解
- ⚠️ 效能稍低於純 C#，但遊戲業務邏輯可接受

**狀態**：✅ 已接受

---

### ADR-002：C# ↔ Lua 資料傳遞使用 JSON 字串

**背景**：Lua callback 接收 C# 複雜物件（AuthResult）需要選擇傳遞方式。

**選項**：
1. 直接暴露 C# class → 大量 XLua Wrap 代碼、Bundle 增大
2. **JSON 字串** → Lua 側 `cjson.decode` 還原為 table

**決策**：採用 JSON 字串，C# 使用 Newtonsoft.Json 序列化，Lua 使用 cjson 解碼。

**後果**：
- ✅ 減少 XLua Wrap 代碼膨脹
- ✅ C# 類別設計不受 Lua 綁定污染
- ⚠️ 序列化/反序列化有一定開銷（對登入流程可接受，不適合高頻呼叫）

**狀態**：✅ 已接受

---

### ADR-003：UI 系統採用 Facade + 模組化拆分

**背景**：舊版 UIMgr.lua 為 3379 行 God Class，維護困難。

**決策**：拆分為 7 個職責單一模組（Facade / Model / Stack / Layer / Lifecycle / Queue / GC），UIMgr 作為 Facade 對外。

**後果**：
- ✅ 每個子模組 < 250 行，職責清晰
- ✅ 可獨立測試各子模組
- ✅ 子模組依賴注入（Init 參數傳遞），低耦合
- ⚠️ 模組間引用稍複雜（Lifecycle 同時依賴 Model/Stack/Layer/GC）

**狀態**：✅ 已接受

---

### ADR-004：RequireEx 引用計數管理 Lua 模組生命週期

**背景**：Lua `require` 自帶快取（`package.loaded`），但無法管理多系統重用同一模組的釋放時機。

**決策**：實作 `RequireEx`，以「系統名稱」為粒度記錄引用，`UnRequire(systemName)` 批次釋放，引用歸零自動 `package.loaded[path] = nil`（並呼叫 `Dispose`）。

**後果**：
- ✅ 模組生命週期明確，避免記憶體洩漏
- ✅ 系統卸載（如 Game.OnApplicationQuit）可批次釋放所有相關模組
- ⚠️ 開發者需遵守「透過 RequireEx 載入」慣例，否則引用計數不準確

**狀態**：✅ 已接受

---

### ADR-005：ILoginProvider 策略模式

**背景**：需支援多種登入渠道（Editor/Line，未來可能 Apple/Google），各平臺 SDK 差異大。

**決策**：定義 `ILoginProvider` interface（Init/Login/Logout/IsInitialized/ChannelName），各渠道實作，`LoginManager` 以 `Dictionary<string, ILoginProvider>` 管理。

**後果**：
- ✅ 新增渠道只需實作 `ILoginProvider` + 在 `RegisterProviders` 加一行
- ✅ `LoginMgr.lua` 不需感知具體渠道實作
- ⚠️ `LoginManager.InitChannel` 在 `#if UNITY_EDITOR` 時自動呼叫（非 Lua 控制），需注意時序

**狀態**：✅ 已接受

---

### ADR-006：UIOperationQueue 序列化 UI 操作

**背景**：快速連點按鈕可能觸發並發 Open/Close，導致 UI 狀態錯亂。

**決策**：所有 `UIMgr.Open/Close` 必須通過 `UIOperationQueue` 排隊，`IsProcessing` 期間後續操作等待。

**後果**：
- ✅ 防止 UI 操作並發導致的狀態問題
- ✅ 操作順序保證 FIFO
- ⚠️ 大量快速操作時佇列可能積累，應視需求清空（`ClearQueue`）

**狀態**：✅ 已接受

---

## C# 初始化序列（Main.cs FSM）

```
1. UnityInitialize
   ├── Screen / Application 設定
   ├── ProjectMgr.Init(ProjectData_Default)
   └── XLuaManager.Inst.Do()

2. PlayCG     → 直通（保留架構）
3. CheckNetwork → 驗證 NetworkReachability
4. LoadExeConfig → 直通（保留架構）
5. ResourceInitialize
   └── ResourceMgr.Initialize(AddressableLoader, callback)

6. NetWorkInitialize → 直通（保留架構）
7. LuaInitialize
   ├── DoString("require 'Logic/Game'")
   ├── GetInPath<Action<Action>>("Game.Init")
   ├── 取得所有 Lua 生命週期函式 ref
   └── Game.Init(LuaInitFinish)

8. InitFinish
   └── m_IsLuaInited = true → 開始每幀呼叫 Lua Update
```

---

## UI 開啟流程（完整非同步序列）

```
UIMgr.Open("ControllerName")
  → UIOperationQueue.EnqueueOpen(controller, params)
    → UILifecycle.OpenInternal
      ├─ [首次開啟] StartLoad → LoadResource (Addressables InstantiateAsync)
      │     → OnResourceLoaded → DoInit → Stage: Initializing → Initialized
      │           → DoOpen → Stage: Opening → DoingOpenAnimation? → Opened
      ├─ [已 Initialized] DoOpen 直接
      ├─ [正在載入中] AddLoadingCallback（載入完成後執行）
      └─ [已 Opened] DoReopen（呼叫 OnReopen，不重建）
  → UIGarbageCollector.RecordOpen(controller)
    → CheckAndClean(layer) → [超限] DestroyUI(oldest m_CanAutoDestroy=true)
  → Queue.OnOperationComplete → TryProcessNext
```

---

## 應用退出流程

```
OnApplicationQuit (C#)
  → ComponentDisposableRegistry.DisposeAll()
  → ForceDisposeAllComponents (Reflection 清除所有 UnityEvent)
  → XLuaManager.DoString("Game.OnApplicationQuit()")
    → UIMgr.Dispose()
    → RequireEx.UnRequireAll("Game")
      → 所有模組 package.loaded = nil + Dispose()
  → XLuaManager.Destroy()
    → FullGC() × 3 (Tick + GC + GC.Collect)
    → m_LuaEnv.Dispose()
```
