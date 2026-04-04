---
type: conversation
organization: LIFEOFDEVELOPMENT
project: ai-memory-vault
date: 2026-04-04
session: phase21-db-audit-and-cleanup
---

# AI 對話紀錄 — 2026-04-04 DB 稽核與清理

## 對話主題

Vault 層級自動更新覆蓋率稽核 + 發現問題全面修正

## 背景

Phase 20a/b/c 完成後，用戶要求稽核所有 Vault 目錄層級是否都有被自動同步到 ChromaDB，發現並修正 4 類問題。

## 關鍵決策

### 1. `cleanup="incremental"` → `cleanup="full"` for `sync()`
- **背景**：全量 sync 後仍有 76 個孤立向量殘留（E2E 測試刪除的磁碟檔案）
- **決策**：`Indexer.sync()` 改用 `cleanup="full"`，以全量掃描結果為快照清除孤立向量
- **影響**：`sync_single` / `sync_batch` 繼續用 `incremental`（只更新傳入的文件，不掃全 Vault）

### 2. AutoScheduler 擴充（3 → 6 jobs）
- 新增 AI 週月報排程（weekly AI + monthly AI）
- 新增每週日 02:00 全量 DB sync（防止靜態本地編輯累積孤立向量）

### 3. E2E Step 2 搜尋模式
- 唯一 marker token 改用 `iMode="keyword"`
- 語意向量無法表達無意義唯一碼，BM25 才是正確工具

## 問題與解法

| 問題 | 解法 | 檔案 |
|------|------|------|
| 全量 sync 無法清孤立向量 | `cleanup="incremental"` → `"full"` | `core/indexer.py` |
| E2E cleanup 不清 DB | cleanup section 加 `VaultService.sync()` | `e2e_test.py` |
| phase13 type 不一致 | `ai-conversation` → `conversation` | conversations/2026-04-04-phase13.md |
| phase15 conversation 缺 frontmatter | 補 `type: conversation` 等 | conversations/2026-04-04_phase15-coding-rules-e2e-batch.md |
| AI 分析無排程 | AutoScheduler 加 ai_weekly + ai_monthly | `services/auto_scheduler.py` |
| 靜態檔案孤立堆積 | AutoScheduler 加每週日 full sync | `services/auto_scheduler.py` |
| E2E search marker 排名不穩 | Step 2 改用 `iMode="keyword"` | `e2e_test.py` |

## 修改的檔案清單

- `core/indexer.py` — `cleanup="incremental"` → `"full"` for `sync()`
- `services/auto_scheduler.py` — 加入 3 個新 cron jobs（ai_weekly / ai_monthly / full_sync）
- `e2e_test.py` — cleanup 加 sync + Step 2 改 keyword mode + job_count 3→6
- `Vault/workspaces/lifeofdevelopment/projects/ai-memory-vault/conversations/2026-04-04-phase13.md` — type 修正
- `Vault/workspaces/lifeofdevelopment/projects/ai-memory-vault/conversations/2026-04-04_phase15-coding-rules-e2e-batch.md` — 補 frontmatter

## 最終狀態

- E2E：224/224 PASS ✅
- ChromaDB：439 vectors（清除 76 孤立 + type 全部正確）
- AutoScheduler：6 jobs（daily / weekly / weekly-AI / monthly / monthly-AI / full-sync）
