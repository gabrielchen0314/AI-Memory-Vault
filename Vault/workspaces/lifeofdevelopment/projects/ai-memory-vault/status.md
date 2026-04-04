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
- [x] Embedding 策略評估（chunk_size=500 / overlap=50 可調校）
- [x] 混合搜尋比重優化（keyword/semantic/balanced 三模式實作完成）
- [x] `generate_project_daily` 預填充（從 status.md pending todos 自動填入今日計畫）
- [x] CLI REPL 對齊 MCP 新工具（新增 5 個指令，E2E Step 18 106/106 PASS）
- [x] Scheduler 單元測試（`tests/test_scheduler.py` 42 個測試，E2E Step 17 90/90 PASS）
- [x] CLI 自動化同步（tools/registry.py 宣告式登記表，E2E Step 19 166/166 PASS）
- [x] Vault Git 版本控制（services/git_service.py + config.GitConfig，E2E Step 20 183/183 PASS）
- [x] 知識萃取自動化（services/knowledge_extractor.py，E2E Step 21 208/208 PASS）
- [x] Token 分析欄位（services/token_counter.py，E2E Step 22 224/224 PASS）
- [x] DB 覆蓋率稽核與清理（cleanup="full" + AutoScheduler 6 jobs，E2E 224/224 PASS）
- [ ] tests/test_knowledge_extractor.py 補單元測試
- [ ] ChromaDB migration 機制（技術債，中優先）
- [ ] v3 UI 開發（Tauri + React 聊天介面 + 搜尋 + 設定）

## 工作脈絡

**Phase 21 DB 稽核與清理（2026-04-04）完成項目：**

### 根本問題修正
- `core/indexer.py`：`sync()` 全量掃描改為 `cleanup="full"`（原 `incremental` 無法清孤立向量）✅
- 清除 76 個孤立向量（515 → 439 vectors）✅

### E2E 基礎強化
- `e2e_test.py`：cleanup section 加入 `VaultService.sync()` 自動清除測試殘留 ✅
- `e2e_test.py`：Step 2 唯一 marker 搜尋改用 `iMode="keyword"` 確保穩定性 ✅
- `e2e_test.py`：job_count 斷言 3 → 6 ✅

### Frontmatter 修正
- `conversations/2026-04-04-phase13.md`：`type: ai-conversation` → `type: conversation` ✅
- `conversations/2026-04-04_phase15-coding-rules-e2e-batch.md`：補完整 frontmatter ✅

### AutoScheduler 擴充（3 → 6 jobs）
- 新增 ai_weekly（週一 09:00 → `generate_ai_weekly_analysis()`）✅
- 新增 ai_monthly（月 1 日 09:00 → `generate_ai_monthly_analysis()`）✅
- 新增 weekly_full_sync（週日 02:00 → `VaultService.sync()`，清除靜態編輯孤立向量）✅

**E2E 最終狀態：224/224 PASS** ✅

---

**Phase 20c（2026-04-04）：**
- `services/token_counter.py`：TokenCounter 靜態工具 ✅
- 週報/月報模板 Token 分析欄位填入真實數值 ✅

**Phase 20b（2026-04-04）：знания extraction**
- `services/knowledge_extractor.py`：KnowledgeExtractor ✅（無 LLM 依賴）
- `mcp_app/server.py`：extract_knowledge MCP tool ✅
- `tools/registry.py`：11 個 ToolEntry ✅

**Phase 20a（2026-04-04）：**
- `services/git_service.py`：GitService + GitConfig ✅
- VaultService 3 個 git hook 點 ✅

## 技術債

| 項目 | 嚴重度 |
|------|------|
| ~~Scheduler 無單元測試~~ | ✅ 已解決 |
| ~~CLI REPL 與 MCP 功能未對齊~~ | ✅ 已解決 |
| ~~知識萃取自動化~~ | ✅ 已解決 |
| ~~Token 分析欄位空白~~ | ✅ 已解決 |
| ~~孤立向量堆積（cleanup=incremental bug）~~ | ✅ 已解決 |
| tests/test_knowledge_extractor.py 缺單元測試 | 低 |
| ChromaDB migration 機制 | 中 |
| v3 UI（Tauri + React） | 長期 |
