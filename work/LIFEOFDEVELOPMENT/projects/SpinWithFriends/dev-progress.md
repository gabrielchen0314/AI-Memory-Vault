---
type: dev-progress
project: SpinWithFriends
company: LIFEOFDEVELOPMENT
author: gabrielchen
recorded_date: 2026.03.29
last_updated: 2026.03.29
ai_summary: "SpinWithFriends 開發進度快照 v2：新增技術債、修正 OnUpdate BUG、補充版本欄位"
tags: [progress, status, todo, bugs, tech-debt]
---

# SpinWithFriends — 開發進度快照

> 記錄日期：2026.03.29（由 Architect Agent 靜態分析更新）

---

## 當前版本 / 迭代狀態

| 項目 | 值 |
|------|-----|
| 版本 | 1.0（XluaBase 基礎架構階段） |
| 迭代狀態 | **基礎架構完成** — 登入系統完成，UI 框架完成，等待遊戲功能開發 |
| 主要里程碑 | C# Runtime 架構 ✅ / Lua UI 框架 ✅ / 登入系統 ✅ / 遊戲業務邏輯 ⏳ |

---

## 整體進度概覽

| 系統 | 狀態 | 說明 |
|------|------|------|
| **C# Runtime 基礎** | ✅ 完成 | Main.cs FSM / XLuaManager / ResourceMgr |
| **Lua 啟動流程** | ✅ 完成 | GDefines → Game.Init → UIMgr.Init |
| **UI 管理系統** | ✅ 完成（有已知問題） | 模組化拆分完成（7個子模組），有 BUG |
| **登入系統** | ✅ 完成 | C# LoginManager + Lua LoginMgr |
| **日誌系統** | ✅ 完成 | LuaLogSystem + SystemLogBase 橋接 |
| **Require 管理** | ✅ 完成 | RequireEx 引用計數 + 系統級批次釋放 |
| **Main_Controller** | ✅ 完成 | 主選單 UI（含 VirtualScrollView 範例） |
| **遊戲玩法功能** | ⏳ 未開始 | 業務邏輯（Spin 機制等）尚未開發 |

---

## 最近完成功能

### C# 層

- [x] `Main.cs`：EStateOfGame FSM（15 種狀態，含保留狀態架構）
- [x] `XLuaManager.cs`：LuaEnv 單例、CustomLoader（Editor/Release 雙路徑）、GC Tick（1秒間隔）
- [x] `LoginManager.cs`：登入 Facade，支援 ILoginProvider 介面擴充，JSON 橋接
- [x] `EditorLoginProvider.cs`：Editor 模擬登入（`#if UNITY_EDITOR`）
- [x] `LineLoginProvider.cs`：LINE 登入整合（`#if LINE_SDK`）
- [x] `ILuaReflection.cs`：C#→Lua 介面映射（delegates + interface）
- [x] `ProjectData_Default.cs`：台版 CDN 設定（Debug/QA/Release 多節點）
- [x] `MainThreadDispatcher`：非同步回調轉主執行緒安全機制

### Lua 層

- [x] `GDefines.lua`：70+ C# 類別全域綁定（UnityEngine / GameTools / SDK）
- [x] `GEnums.lua`：全域列舉（EUIStage/EFormLayerType/EUIOrderLayers/EUIOperation）
- [x] `LuaLogSystem.lua`：Lua 日誌（SystemLogBase + debug.traceback Lua 堆疊）
- [x] `UIConfig.lua`：UI 設定工廠（New/FullPage/HalfPage/Peak/Loading + Setter 鏈）
- [x] `UIControllerBase.lua`：UI Controller 基底工廠（ViewRef 存取、生命週期 Hooks）
- [x] `Game.lua`：遊戲主邏輯（Init/Update/FixedUpdate/LateUpdate/ApplicationEvents）
- [x] `LoginMgr.lua`：登入 Facade（7 個公開 API，JSON 橋接）
- [x] `UIMgr.lua`：UI 主 Facade（Open/Close/Back/Preload/狀態查詢）
- [x] `UIModel.lua`：UI 資料模型（Controllers Map/Stage/Visible/LoadingCallbacks）
- [x] `UIStack.lua`：全版 UI 堆疊（Push/Pop/Peek/GetPrevious/Contains）
- [x] `UILayer.lua`：層級管理（5層 ORDER_BASE + MoveToTop + Transform 查找）
- [x] `UILifecycle.lua`：UI 生命週期（12 階段 EUIStage + SubUI 機制 + 異步開關）
- [x] `UIOperationQueue.lua`：操作序列化佇列（防並發開關衝突）
- [x] `UIGarbageCollector.lua`：UI 資源回收（LAYER_LIMITS + 超限自動 DestroyUI）
- [x] `RequireEx.lua`：Require 引用計數（系統級 Register/Release/UnloadPackage）
- [x] `LuaDebug.lua`：Editor 除錯工具
- [x] `Main_Controller.lua`：主選單 UI Controller

---

## 進行中 / 待辦

- [ ] 遊戲主要玩法功能（Spin 機制、賭注邏輯等）
- [ ] 更多 UI Controller 開發（遊戲介面、結算介面等）
- [ ] 修復下方 BUG（優先修 🔴）

---

## 已知問題 / BUG

| 優先度 | 問題描述 | 位置 | 來源 |
|--------|---------|------|------|
| 🔴 BUG | `UILifecycle.Update()` 條件判斷為 `if _Controller.Update then`，但 UIControllerBase 只定義 `OnUpdate` 不定義 `Update`，導致所有 Controller 的 `OnUpdate` **永遠不被呼叫** | `UILifecycle.lua` 第 Update 函式 | 靜態分析 |
| 🔴 BUG | 關閉 UI 動畫時呼叫 `OnOpenUIAnimation` 而非 `OnCloseUIAnimation` | `UIAnimationMgr.PlayUIAnimation` | Analysis Report |
| 🔴 問題 | `UIMgr.FixedUpdate()` / `UIMgr.LateUpdate()` 函式體為空，但 Main.cs 每幀呼叫 Lua FixedUpdate | `UIMgr.lua` | 靜態分析 |
| 🟡 中 | 硬編碼 UI 名稱字串（未使用常數或列舉統一管理） | `UILifecycle.lua` 載入相關 | Analysis Report |
| 🟡 中 | `UILifecycle.Update()` 遍歷所有 OpenedList，但需確認 List 在 UI 狀態異常時的合法性 | `UILifecycle.lua` | 靜態分析 |
| 🟢 低 | 15+ 處被註解掉的程式碼需清理 | UI 系統各模組 | Analysis Report |

---

## 技術債

| 類型 | 描述 | 建議處理時機 |
|------|------|------------|
| **架構** | UIScene（場景轉換）系統尚不存在，多場景遊戲時需補充 | 遊戲功能開發前 |
| **架構** | 保留狀態（PlayCG/FTPSelect/LuaAndAssetsDownload）目前空實作，需確認是否將來要填入 | 里程碑規劃時 |
| **效能** | `RequireEx.Require` 每次都 `pcall(require)` — 對已載入模組無效能問題，但需確認 Lua cache 機制正常運作 | Review 時確認 |
| **可維護性** | `ProjectData_Default.cs` 使用了 CHINESE GAMER CDN 設定，可能需替換為 LIFEOFDEVELOPMENT 設定 | 上線前 |
| **安全** | `ILoginProvider` 目前只有 Editor/Line，Apple/Google/Guest 已在列舉中預留（被 comment off）| 功能需求確認後 |
| **清理** | 15+ 處被 comment 的程式碼影響可讀性 | 下次重構 |

---

## 參考文件

| 文件 | 用途 |
|------|------|
| `UIMgr_Analysis_Report.md` | BUG 與改進建議 |
| `UI_Analysis.md` | 舊版 UGUIManager.cs 架構分析 |
| `GUIController_Analysis.md` | Unreal 舊版歷史參考 |

---

## Vault 索引

| 檔案 | 說明 |
|------|------|
| `work/LIFEOFDEVELOPMENT/projects/SpinWithFriends/project-overview.md` | 專案總覽、FSM 流程、C# 類別、GDefines 完整綁定 |
| `work/LIFEOFDEVELOPMENT/projects/SpinWithFriends/lua-module-catalog.md` | 17 個 Lua 模組清單與對外 API |
| `work/LIFEOFDEVELOPMENT/projects/SpinWithFriends/LoginMgr_APIMap.md` | LoginMgr 詳細 API Map |
| `work/LIFEOFDEVELOPMENT/projects/SpinWithFriends/architecture.md` | 架構決策記錄（ADR）+ 系統依賴圖 |
| `work/LIFEOFDEVELOPMENT/projects/SpinWithFriends/dev-progress.md` | 本文件 |
