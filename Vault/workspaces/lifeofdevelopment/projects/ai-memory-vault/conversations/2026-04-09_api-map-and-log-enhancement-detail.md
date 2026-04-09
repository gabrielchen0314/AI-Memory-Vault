---
type: conversation-detail
date: 2026-04-09
session: api-map-and-log-enhancement
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
tags: [conversation, detail]
---

# 2026-04-09 api-map-and-log-enhancement — 詳細對話紀錄

## 對話概要
- **主題**：API Map 規則整備 + log_ai_conversation 強化實作

## 關鍵問答紀錄

### Q1: 02 規則的程式碼專案判斷為什麼只列特定副檔名？
- **AI 分析**：原規則硬編碼 `.py/.cs/.lua/.ts/.js` 五種，但實際上任何程式語言都需要 API Map
- **決策**：改為通用判斷：包含任何程式語言原始碼即為程式碼專案，不逐一列舉
- **替代方案**：保留列舉但加更多副檔名 — 不採用，因為列表永遠不完整

### Q2: PersonalMemory_202603.instructions.md 是否要遷移入 Vault？
- **AI 分析**：用戶澄清這不是現有檔案，只是拿來展示可優化的方向
- **決策**：不遷移，僅作為格式參考
- **替代方案**：拆分為知識卡片+專案紀錄 — 用戶明確表示不需要

### Q3: 詳細聊天紀錄用方案 A 還是方案 B？
- **AI 分析**：用戶選方案 B（conversation summary），但也同意方案 A 可以順便實作
- **決策**：兩者合併：強化 log_ai_conversation（方案 A）+ AI 從 conversation summary 萃取 detail（方案 B）
- **替代方案**：方案 C（VS Code Extension 擷取）— 太複雜，暫不實作

### Q4: detail 格式是組織限定還是全域共用？
- **AI 分析**：用戶指出 PersonalMemory 格式可以是共用的，不限定組織
- **決策**：明確標註全域共用格式，適用所有組織與所有專案

## 修改的檔案清單

| 檔案 | 操作 | 摘要 |
|------|------|------|
| `AI_Engine/services/scheduler.py` | 修改 | `log_conversation` 新增 `iDetail` 參數；新增 `_render_conversation_detail` 渲染器（~100行） |
| `AI_Engine/mcp_app/tools/scheduler_tools.py` | 修改 | MCP `log_ai_conversation` 新增 `detail: Optional[dict]` 參數 |
| `Vault/workspaces/_global/rules/15-api-map-writing-guide.md` | 新增 | API Map 撰寫指南全域規則（模板+結構+命名） |
| `Vault/workspaces/_global/rules/02-project-api-map-sync.md` | 修改 | 移除硬編碼副檔名、加入專案側為主原則 |
| `Vault/_config/agents.md` | 修改 | 收工 SOP 6步→5步、log_ai_conversation v3.6 |
| `Vault/_config/end-of-day-checklist.md` | 修改 | 步驟合併、標註全域共用 |
| `User/prompts/global-prompts-maintenance.instructions.md` | 修改 | 規則清單加入 15-api-map-writing-guide.md |

## 執行的命令

| 命令 | 目的 | 結果 |
|------|------|------|
| `python -c "from services.scheduler import SchedulerService; print('OK')"` | 驗證程式碼無語法錯誤 | 成功 |
| `Remove-Item temp_inspect_vscdb.py` | 清理調查暫存腳本 | 成功 |

## 遇到的問題與解決

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| VS Code 無穩定 API 匯出完整對話內容 | 對話存在 `vscode-chat-session://` 內部 URI，無法直接讀取 | 改用 conversation summary（AI context 內可存取）作為詳細紀錄來源 |
| `log_ai_conversation` 首次呼叫 detail 未生成檔案 | `dict = None` 型別標註不完整，FastMCP 可能未正確處理 | 改為 `Optional[dict] = None` 並加入 `from typing import Optional` |

## 學到的知識

- VS Code `state.vscdb` (SQLite) 只存會話索引（ID/標題/時間戳），對話內容在 `vscode-chat-session://` 內部 URI
- `chatEditingSessions/` 目錄存的是 Agent 模式的檔案快照（git-like hash），不是對話文字
- conversation summary 是目前最完整且可存取的對話紀錄來源
- FastMCP 的 `dict` 型別參數需要搭配 `Optional` 才能正確處理可選參數

## 決策記錄

| 決策 | 選項 | 最終選擇 | 理由 |
|------|------|---------|------|
| APIMapGuide 存放位置 | `_global/rules/` vs `chinesegamer/rules/` | `_global/rules/15-api-map-writing-guide.md` | 模板結構通用，Lua 部分標記為範例 |
| 收工 SOP 步驟數 | 6步（摘要+詳細分開）vs 5步（合併） | 5步 | log_ai_conversation 已支援 detail 參數，一次呼叫完成 |
| 程式碼專案判斷 | 硬編碼副檔名 vs 通用判斷 | 通用判斷 | 列表永遠不完整，用原則性描述更好 |
