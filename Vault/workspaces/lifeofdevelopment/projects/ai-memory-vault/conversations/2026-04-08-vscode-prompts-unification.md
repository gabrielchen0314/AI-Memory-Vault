---
project: ai-memory-vault
org: lifeofdevelopment
date: 2026-04-08
session: vscode-prompts-unification
type: conversation
---

# 對話紀錄 — 2026-04-08（VS Code Prompts 架構統一）

## 對話主題

分析現有 VS Code prompts 架構的重複問題，確立「唯一橋接入口」原則，並完成實作。

## 關鍵決策

| 決策 | 說明 |
|------|------|
| `vault-bridge.instructions.md` 是唯一橋接入口 | 不允許新增額外橋接 `.instructions.md` |
| vault-bridge 只保留語言規定 + MCP call 指標 | 實質內容全在 Vault |
| `agents.md` 加 `inject: true` | MCP client 連線時自動注入 |
| 不需要 `.vscode/copilot-instructions.md` | `applyTo: "**"` 已全域覆蓋 |
| 未來新增指示 → 寫 Vault | `vault-bridge.instructions.md` 不動 |

## 問題與解法

| 問題 | 解法 |
|------|------|
| 兩個橋接檔內容重疊 | 合併為一個 vault-bridge.instructions.md |
| vault-bridge 複製了 Vault 內容 | 第二輪精簡，移除規則表格和路徑邏輯 |
| agents.md 無 inject:true | 加入 frontmatter |
| 架構原則沒有文字記錄 | 加入 global-prompts-maintenance 分層表格 |

## 修改的檔案

- `User/prompts/vault-bridge.instructions.md` — **新建**（合併自舊 2 檔）
- `User/prompts/vault-coding-rules.instructions.md` — **刪除**
- `User/prompts/VaultWriteConventions.instructions.md` — **刪除**
- `User/prompts/global-prompts-maintenance.instructions.md` — 更新：新增架構原則表
- `Vault/_config/agents.md` — 加 inject:true，更新 VS Code 整合說明
