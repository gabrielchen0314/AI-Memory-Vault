# Phase 15 — Coding Rules + E2E + batch_write_notes + update_todo

## 對話摘要

**日期：** 2026-04-04  
**結果：** 成功，26/26 E2E 通過

## 主要任務

1. **建立規則架構（新增功能 DB 更新規則）**
   - 確認 `generate_project_status` 呼叫 `_sync_write()` → ChromaDB ✅
   - 確認 `list_projects` 純讀，不需 DB 更新 ✅
   - 更新 `_config/agents.md`：2 個新工具 + Coding 規則索引

2. **Coding 規則建立（3 層架構）**
   - `workspaces/_global/rules/01-coding-style-universal.md`（全語言通用）
   - `workspaces/Chinesegamer/rules/01-csharp-coding-style.md`（C# Unity）
   - `workspaces/Chinesegamer/rules/02-lua-coding-style.md`（Lua xLua）
   - `workspaces/lifeofdevelopment/rules/01-python-coding-style.md`（Python）

3. **Phase 15 E2E 測試**
   - 修復：`vectorstore.initialize()` 必須先於 `VaultService.initialize()`
   - 修復：PowerShell CP950 → ASCII `[PASS]`/`[FAIL]`
   - 基準 14/14 → 擴充至 **26/26**

4. **batch_write_notes 工具**
   - `core/indexer.py` 新增 `sync_batch(iAbsPaths: list)`（N 檔 → 1 次 langchain_index）
   - `services/vault.py` 新增 `batch_write_notes(iNotes: list)`
   - `mcp_app/server.py` 暴露 MCP 工具

5. **update_todo 工具**
   - `services/vault.py` 新增 `update_todo(iFilePath, iTodoText, iDone)`（checkbox toggle）
   - `mcp_app/server.py` 暴露 MCP 工具

## 技術決策
- `sync_batch` vs 多次 `sync_single`：效能優化，批量寫入時節省 N-1 次索引呼叫
- `update_todo` 只改 checkbox，不覆蓋全文：保護用戶手動編輯的其他內容

## 工具準確率
- 工具 15 個全數驗證通過（E2E 26 tests）
- 正確率：26/26 = 100%
