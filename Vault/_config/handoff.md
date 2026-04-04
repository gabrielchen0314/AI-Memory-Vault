---
type: system
created: 2026.04.04
last_updated: 2026.04.04
inject: true
---

# 🤝 Session Handoff

> 記錄上次工作的活躍專案，供下次 AI 對話開場快速定位。
> 各專案詳細狀態（待辦 + 工作脈絡）見各專案的 `status.md`。

## 上次活躍專案

| 專案 | 組織 | 狀態 | 詳細 |
|------|------|------|------|
| ai-memory-vault | LIFEOFDEVELOPMENT | 進行中 | workspaces/lifeofdevelopment/projects/ai-memory-vault/status.md |

## 跨專案備註

- **E2E 224/224 PASS**（最新狀態）
- Phase 21 完成：DB 覆蓋率稽核 + 清理
  - `core/indexer.py` `sync()` 改 `cleanup="full"` → 清除 76 孤立向量（515→439）
  - `AutoScheduler` 3→6 jobs（+ ai_weekly / ai_monthly / weekly_full_sync）
  - E2E cleanup 加 `VaultService.sync()`；Step 2 改 `iMode="keyword"`
  - Phase13/15 conversation frontmatter 修正完成
- 目前 DB：**439 vectors**，type 分布全部正確（無 [none] / [test] / [ai-conversation]）
- `tools/registry.py` 目前有 11 個 ToolEntry（alias: sy/gs/da/rv/wk/mo/la/aw/am/ex/ig）

## 下次接續建議

1. `tests/test_knowledge_extractor.py` — 補 KnowledgeExtractor 單元測試
2. Phase 22：評估 v3 UI（Tauri + React）可行性
3. ChromaDB migration 機制（技術債，中優先）

## 規則提醒

- 新功能必須確認有 DB 更新路徑（寫入型工具）
- 不重複接口：batch vs single 是不同用途，不算重複
- 新規則或工具加入後，必須更新 `_config/agents.md`
- 收工前必須先讀 `_config/end-of-day-checklist.md`（必做步驟）
