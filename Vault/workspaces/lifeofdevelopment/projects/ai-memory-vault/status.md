---
type: status
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
last_updated: 2026.04.04
---

# ai-memory-vault 專案狀態

## 待辦事項

- [x] Scheduler Weekly/monthly 自動觸發（APScheduler，週一/月初自動生成）
- [x] Daily note AI 彙整（自動從 `conversations/` 摘要生成每日進度）
- [ ] Embedding 策略評估（chunk_size / overlap 調整，目前未調校）
- [ ] 混合搜尋比重優化（BM25 0.4 / Vector 0.6 未依實際查詢場景評估）
- [ ] v3 UI 開發（Tauri + React 聊天介面 + 搜尋 + 設定）

## 工作脈絡

**Phase 18（2026-04-04）完成項目：**
- `services/auto_scheduler.py`：APScheduler BackgroundScheduler，3 個 cron job ✅
  - Weekly Mon 08:00 → `generate_weekly_summary()`
  - Monthly 1st 08:00 → `generate_monthly_summary()`
  - Daily 22:00 → `generate_daily_summary()`（含 auto-digest）
- `main.py --scheduler`：守護模式進入點 ✅
- `services/scheduler.py`：`generate_daily_summary()` 加入 auto-digest ✅
  - `_scan_today_conversations(date)` 新增
  - `_render_daily_summary_template()` 加入「今日 AI 對話」區塊
- `auto_tasks.ps1`：修正 3 個已更名的 method（generate_daily/weekly/monthly_review → _summary）✅
- E2E Step 13（AutoScheduler，6 checks）→ 52/52 PASS ✅
- `apscheduler>=3.10` 加入 `requirements.txt` ✅

**兩套排程系統說明：**
- `.bat` + Windows Task Scheduler：主要使用（可設定、開機恢復）
- `main.py --scheduler` APScheduler：跨平台備用（Linux/Mac server 用）
- 兩套功能重疊但各司其職，日常以 `.bat` 系統為主
- `vscode_user_path` 欄位加入 `AppConfig` ✅
- `SetupService` Step 6：自動生成 VS Code 全域 instructions 檔 ✅
  - `vault-coding-rules.instructions.md`（動態發現，永不需手動更新）
  - `VaultWriteConventions.instructions.md`
- E2E Step 12（vscode integration，含冪等驗證）✅
- E2E 46/46 PASS ✅

**Phase 16（2026-04-04）完成項目（全部）：**
- `delete_note` MCP tool（VaultIndexer + VaultService + MCP server v3.5）✅
- E2E Step 11（delete 生命週期）✅
- `mcp.json` 清理（合一至全域，加入 `cwd`）✅
- Prompts cleanup（刪除 2 個舊檔，更新 2 個，新建 SOP 檔）✅
- `vault-coding-rules.instructions.md` 重構為動態發現（search_vault 自動找規則）✅
- `global-prompts-maintenance.instructions.md`（新增後必更新 SOP）✅
- 全規則合併至 `_global/rules/`（01–14），刪除 CHINESEGAMER + LIFEOFDEVELOPMENT 舊規則 ✅
- sync_vault 清理孤立向量（Deleted=22）✅

**Phase 15（2026-04-04）完成項目（已歸檔至 roadmap）**

## 技術債（目前最高優先）

| 項目 | 嚴重度 |
|------|------|
| Scheduler 無單元測試 | 中 |
| ChromaDB migration 機制 | 中 |
| CLI REPL 與 MCP 功能未對齊 | 低 |
| Token 分析欄位空白 | 低 |
