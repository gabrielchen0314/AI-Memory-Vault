---
type: index
domain: meta
category: rules-index
workspace: CHINESEGAMER
created: 2026-03-27
last_updated: 2026-03-28
tags: [index, rules, CHINESEGAMER]
ai_summary: "CHINESE GAMER 工作域的所有規則索引，包含 10 個 Rule 檔案，涵蓋 C#/Lua 編碼、Protocol 協定、ViewRef UI 綁定、Tag 系統、遊戲安全、Git 提交、VS Code Extension 開發、混淆驗證、多專案管理。"
---

# 📋 Rules Index — CHINESE GAMER

> 所有工作規範的單一索引，涵蓋遊戲開發（Unity + C# + XLua）和工具開發（VS Code Extension + TypeScript）

---

## 規則清單

| # | 檔案 | 領域 | 嚴重度 | 適用技術 | 說明 |
|---|------|------|:------:|---------|------|
| 01 | [[01-csharp-coding-style]] | Coding | Must | C#, Unity | C# 命名規範、Region 結構、XML 註解、GC 防護 |
| 02 | [[02-lua-coding-style]] | Coding | Must | Lua, XLua | Lua 模組結構、LuaDoc 註解、Data 型別驗證 |
| 03 | [[03-protocol-implementation]] | Networking | Must | Lua, XLua | Client↔Server 封包格式、編號規則、型別對照 |
| 04 | [[04-viewref-binding]] | UI | Must | Lua, Unity | ViewRef 綁定、Component 映射、Button.New 規則 |
| 05 | [[05-tag-system]] | System | Must | Lua, Unity | Tag 枚舉、Bit Array 預處理、TagUtils API |
| 06 | [[06-security-game]] | Security | Critical | C#, Lua | 作弊防護、Server 驗證、敏感資訊保護 |
| 07 | [[07-git-conventions]] | Workflow | Must | All | Commit Type、Message 格式、路徑分類 |
| 08 | [[08-vscode-extension]] | Coding | Must | TypeScript, VS Code API | Extension 架構、TS 命名、webpack、生命週期 |
| 09 | [[09-obfuscation-guide]] | Security | Must | TypeScript, webpack | 程式碼混淆、公司網路驗證、雙版本打包 |
| 10 | [[10-multi-project-git]] | Workflow | Should | Git, TypeScript | 4 個 Extension 專案的批次 Git 管理 |

---

## 依開發領域分類

### 🎮 遊戲開發（Unity + C# + XLua）
- [[01-csharp-coding-style]] — C# 命名、結構、Unity 規範
- [[02-lua-coding-style]] — Lua 命名、模組結構、Data 型別
- [[03-protocol-implementation]] — 封包讀寫
- [[04-viewref-binding]] — UI 物件綁定
- [[05-tag-system]] — Tag 系統開發

### 🔌 工具開發（VS Code Extension + TypeScript）
- [[08-vscode-extension]] — Extension 架構、TypeScript 命名
- [[09-obfuscation-guide]] — 混淆與驗證
- [[10-multi-project-git]] — 多專案 Git 管理

### 🔗 跨領域通用
- [[06-security-game]] — 安全審查（C# + Lua + TS）
- [[07-git-conventions]] — Git 提交規範（遊戲端格式）

---

## 依 Agent 對應

| Agent | 相關 Rule |
|-------|----------|
| `@CodeReviewer` | 01, 02, 03, 04, 05, 08 |
| `@SecurityReviewer` | 06, 09 |
| `@GitCommitter` | 07, 10 |
| `@Architect` | 01, 02, 05, 08 |
| `@BuildErrorResolver` | 01, 02, 08 |
| `@DocUpdater` | 03, 04, 05 |

---

## ⚠️ 命名風格差異速查

| 元素 | C#（遊戲端） | Lua（遊戲端） | TypeScript（Extension） |
|------|:------------:|:------------:|:---------------------:|
| 成員變數 | `m_PlayerName` | `private.m_PlayerName` | `_playerName` |
| 參數 | `iAmount` | `iAmount` | `amount`（無前綴） |
| 區域變數 | `_TempValue` | `local _TempValue` | `tempValue` |
| 常數 | `MAX_COUNT` | `MAX_COUNT` | `MAX_COUNT` |
| 列舉 | `EItemType` | `EItemType` | `ItemType`（無 E 前綴） |

> ⚠️ **寫 Extension 時不要用遊戲端的 `m_`、`i` 前綴！**

---

*最後更新：2026-03-27*
