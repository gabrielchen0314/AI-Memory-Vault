# CLAUDE.md

> ⚡ **本檔案是 AI 每次 Session 啟動時的第一份必讀文件。**
> 請在開始任何工作前，完整讀取本檔案。

---

## 👤 關於使用者

| 項目        | 內容                                               |
| --------- | ------------------------------------------------ |
| **姓名**    | 陳鼎翰                                              |
| **角色**    | 軟體工程師                                            |
| **公司**    | CHINESE GAMER(上班的地方), LIFEOFDEVELOPMENT(自己的專案) |
| **溝通語言**  | 繁體中文                                             |
| **程式碼語言** | 英文                                               |

### 技術棧

| 類別 | 技術 |
|------|------|
| **主力語言** | C#, Lua (XLua/toLua), TypeScript |
| **其他語言** | C++, Pascal, Go |
| **遊戲引擎** | Unity |
| **工具開發** | VS Code Extension (TypeScript + Node.js) |
| **版本控制** | Git |

### 工作內容

工作分屬兩間公司，共用資源集中於 `_shared/`：

| 公司 | 說明 | 路徑 |
| --- | --- | --- |
| **CHINESE GAMER** | 上班的地方 | `work/CHINESEGAMER/` |
| **LIFEOFDEVELOPMENT** | 自己的專案 | `work/LIFEOFDEVELOPMENT/` |

#### CHINESE GAMER 開發領域

| 領域          | 說明                   | 核心技術                           |
| ----------- | -------------------- | ------------------------------ |
| 🎮 **遊戲開發** | 線上遊戲 Client 端        | Unity + C# + XLua/toLua        |
| 🔌 **工具開發** | 內部 VS Code Extension | TypeScript + Node.js + webpack |

> ⚠️ 兩個領域的**命名風格不同**！遊戲端用 `m_`/`i`，Extension 端用標準 TypeScript 慣例。詳見下方速查表。

---

## 📂 Vault 結構導航

```
AI-Memory-Vault/
│
├── 📋 _system/                          ← 你正在讀的地方
│   ├── CLAUDE.md                        ← 本檔案（AI 入口指令）
│   ├── AGENTS.md                        ← Vault 架構文件（給 AI 看）
│   ├── vault-nav.md                     ← 導航地圖（所有入口）
│   ├── action-register.md               ← 待辦事項總表
│   ├── handoff.md                       ← 上次 Session 的交接
│   └── ai-engine-progress.md            ← AI Engine 進度追蹤
│
├── 🔧 work/                             ← 工作域（以公司分類）
│   ├── _shared/                         ← 跨公司共用資源
│   │   ├── skills/                      ← AI 技能檔
│   │   ├── snippets/                    ← 程式碼片段（csharp/lua/typescript）
│   │   └── tech-stack/                  ← 技術棧知識庫
│   ├── CHINESEGAMER/                    ← 上班的地方
│   │   ├── rules/                       ← 編碼規範（10 條 Rule）
│   │   ├── projects/                    ← 專案控制塔
│   │   ├── meetings/                    ← 會議紀錄
│   │   ├── people/                      ← 人物檔案
│   │   └── working-context/             ← 當前工作上下文
│   └── LIFEOFDEVELOPMENT/                ← 自己的專案
│       ├── projects/                    ← 專案
│       └── working-context/             ← 當前工作上下文
│
├── 🌱 life/                             ← 生活域
│   ├── learning/                        ← 學習筆記（扁平，frontmatter type 區分）
│   ├── journal/                         ← 日記 & 週回顧
│   ├── goals/                           ← 目標管理
│   └── ideas/                           ← 靈感收集
│
├── 📚 knowledge/                        ← 永久知識卡片
│
├── 🧠 .ai_memory/                       ← 記憶系統（含 Instinct）
│   ├── YYYY/MM/DD.md                    ← 日記
│   ├── instincts/                       ← 直覺檔案
│   ├── instinct_config.json             ← Instinct 設定
│   ├── sequence.txt                     ← 全域流水號
│   └── logs/                            ← Session Log & Chat History
│
├── 📎 attachments/                      ← 附件
└── 🧩 templates/                        ← 模板
```

---

## 🚀 Session 啟動協議

每次 Session 開始時，**依序**讀取以下檔案：

```
Step 1 → 讀取 _system/CLAUDE.md          （本檔案）
Step 2 → 讀取 _system/vault-nav.md       （導航地圖）
Step 3 → 讀取 _system/action-register.md  （待辦總表）
Step 4 → 讀取 _system/handoff.md          （上次 Session 的交接）
Step 5 → 如果有特定專案焦點（根據公司自動判斷路徑）：
         → CHINESE GAMER：讀取 work/CHINESEGAMER/working-context/{project}-context.md
         → LIFEOFDEVELOPMENT：讀取 work/LIFEOFDEVELOPMENT/working-context/{project}-context.md
Step 6 → 如果涉及編碼：
         → 讀取 work/CHINESEGAMER/rules/index.md（載入相關規範）
```

### 開發領域自動識別

根據對話中的關鍵字自動判斷要載入哪些 Rule：

| 偵測到的關鍵字 | 領域 | 載入 Rule |
|:-------------|:-----|:---------|
| Unity, C#, XLua, toLua, Protocol, ViewRef, Tag, 串檔, Mgr, 角色, 技能 | 🎮 遊戲開發 | 01~07 |
| VS Code, Extension, TypeScript, webpack, WorkPilot, Synapse, Shared | 🔌 工具開發 | 08~10 |
| Security, 安全, 金幣, 驗證 | 🔒 安全 | 06, 09 |
| Git, commit, push | 📦 版本控制 | 07, 10 |

---

## 🤖 AI 行為規範

### 基本規則

1. **先讀 index.md 再行動** — 進入任何資料夾前，先讀該資料夾的 `index.md`
2. **不要刪除檔案** — 除非使用者明確要求
3. **保持簡潔** — 回應精準，不冗長
4. **繁體中文溝通** — 程式碼用英文，說明用繁體中文
5. **遵循命名規範** — 寫 C#/Lua 用遊戲端規範，寫 TypeScript 用 Extension 規範
6. **主動關聯** — 發現筆記間有關聯時，建議新增 `[[雙向連結]]`

### 維護規則

- **建立新檔案時** → 更新該資料夾的 `index.md`
- **刪除檔案時** → 更新該資料夾的 `index.md`
- **完成重要任務時** → 詢問是否更新 `.ai_memory` 記憶檔
- **發現新規則模式時** → 詢問是否建立新的 Rule 或 Instinct
- **Session 結束時** → 更新 `_system/handoff.md`

### 嚴禁事項

- ❌ 不要在 Vault 外建立檔案
- ❌ 不要修改 `_system/CLAUDE.md` 除非使用者要求
- ❌ 不要擅自合併或重組現有筆記
- ❌ 不要在程式碼中使用 `goto`（C# 和 Lua 都禁止）

---

## 🏷️ 命名規範速查表

### ⚠️ 兩套命名風格

| 元素 | C#（遊戲端 Rule 01） | Lua（遊戲端 Rule 02） | TypeScript（Extension Rule 08） |
|------|:-------------------:|:--------------------:|:-----------------------------:|
| 成員變數 | `m_PlayerName` | `private.m_PlayerName` | `_playerName` |
| 參數 | `iAmount` | `iAmount` | `amount`（無前綴） |
| 區域變數 | `_TempValue` | `local _TempValue` | `tempValue` |
| 常數 | `MAX_COUNT` | `MAX_COUNT` | `MAX_COUNT` |
| 靜態變數 | `s_Instance` | N/A | N/A |
| 列舉 | `EItemType` | `EItemType` | `ItemType`（無 E 前綴） |
| 模組引用 | N/A | `local this = Mod` | N/A |
| 介面 | `IDataProvider` | N/A | `IDataProvider` |

### 禁止項目

| 禁止 | C# | Lua | TypeScript |
|:----:|:--:|:---:|:----------:|
| `goto` | ✅ 禁止 | ✅ 禁止 | N/A |
| `var` | ✅ 禁止 | N/A | N/A |
| `self` | N/A | ✅ 禁止 | N/A |
| 省略 `local` | N/A | ✅ 禁止 | N/A |
| 空 `catch` | ✅ 禁止 | N/A | ✅ 禁止 |

---

## 🤖 Agent 編排速查

### 可用 Agents

| Agent | 觸發 | 用途 |
|-------|------|------|
| **Planner** | `@Planner` | 功能規劃與任務分解 |
| **Architect** | `@Architect` | 系統架構設計（自動識別 Unity / Extension） |
| **TddGuide** | `@TddGuide` | TDD 測試先行引導 |
| **CodeReviewer** | `@CodeReviewer` | 程式碼品質審查 |
| **SecurityReviewer** | `@SecurityReviewer` | 遊戲安全 + Extension 安全審查 |
| **BuildErrorResolver** | `@BuildErrorResolver` | 建置錯誤最小差異修正 |
| **RefactorCleaner** | `@RefactorCleaner` | 重構與死碼清理 |
| **DocUpdater** | `@DocUpdater` | 文件與 API Map 更新 |
| **GitCommitter** | `@GitCommitter` | Git 提交規範 |
| **LearnTrigger** | `@LearnTrigger` | 學習觸發與記憶更新 |

### 常見工作流

```
新功能：@Planner → @Architect（如需） → @TddGuide（可選） → 實作 → @CodeReviewer → @SecurityReviewer（如涉及敏感） → @GitCommitter
Bug 修正：分析 → @TddGuide（寫失敗測試） → 修正 → @CodeReviewer → @GitCommitter
重構：@Architect → @RefactorCleaner → 實作 → @CodeReviewer → @GitCommitter
```

---

## 🧠 Instinct 直覺系統摘要

### 信心分數

| 範圍 | 意義 | AI 行為 |
|:----:|------|--------|
| 0.7 – 0.9 | 高度確信 | 直接應用，不需確認 |
| 0.5 – 0.7 | 中等確信 | 預設應用，可能提及 |
| 0.3 – 0.5 | 初步觀察 | 詢問確認後再應用 |
| < 0.3 | 不確定 | 需要明確指示 |

### 分數調整

| 事件 | 變化 |
|------|------|
| 首次觀察 | +0.3 |
| 重複觀察 | +0.1 |
| 被使用者修正 | −0.2（必須寫錯誤反思） |
| 每隔 10 個序號差 | ×0.95（衰減） |

### 觸發學習

- 使用者說「記下這個」→ 觸發 `@LearnTrigger`
- 完成重要功能 → 詢問是否記錄
- 犯錯被修正 → 必須記錄 + 錯誤反思

---

## 📝 Session 結束協議

每次 Session 結束前，更新 `_system/handoff.md`：

```markdown
## ✅ 本次完成
## 🔍 需要人工確認
## ⏳ 延後處理
## ➡️ 下一步
## 🧠 學習紀錄
```

---

## 🔧 Coding Style 檢查流程

實作完成後，依據開發領域的規範進行檢查：

| 領域 | 語言 | Rule |
|------|------|------|
| 🎮 遊戲 | C# | `rules/01-csharp-coding-style.md` |
| 🎮 遊戲 | Lua | `rules/02-lua-coding-style.md` |
| 🎮 遊戲 | Protocol | `rules/03-protocol-implementation.md` |
| 🎮 遊戲 | UI | `rules/04-viewref-binding.md` |
| 🎮 遊戲 | Tag | `rules/05-tag-system.md` |
| 🔒 安全 | 遊戲 | `rules/06-security-game.md` |
| 📦 Git | 遊戲端 | `rules/07-git-conventions.md` |
| 🔌 Extension | TypeScript | `rules/08-vscode-extension.md` |
| 🔒 安全 | Extension | `rules/09-obfuscation-guide.md` |
| 📦 Git | Extension | `rules/10-multi-project-git.md` |

---

## 💡 自主學習開關

| 功能 | 狀態 |
|------|:----:|
| 自主評估新增指示檔 | `On` |
| 自主更新記憶檔 | `On` |
| Instinct 直覺學習 | `On` |
| Skills 主動查閱 | `On` |

---

*本檔案最後更新：2026-03-27*
