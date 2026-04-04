---
type: conversation
organization: LIFEOFDEVELOPMENT
project: ai-memory-vault
date: 2026-04-04
session: phase20b-20c-token-knowledge
---

# 對話紀錄 — Phase 20b + 20c 實作

## 對話主題

1. DB sync 清理（26 孤立向量）
2. Phase 20b：知識萃取自動化
3. Phase 20c：Token 分析欄位

## 關鍵決策

### KnowledgeExtractor 設計
- **決定**：不呼叫 LLM，改為掃描 Markdown 標題與條列萃取骨架
- **理由**：無網路依賴、瞬間完成、知識卡片設計為草稿供人工審閱
- **冪等**：已存在卡片時追加來源連結而非覆蓋

### TokenCounter 演算法
- **決定**：`len(text) // 4`（CJK + 英文混合通用公式）
- **理由**：不需載入 tiktoken 等套件，估算略高適合做成本上限預測
- **格式**：`format_k()` 自動切換 `850` / `2.4k` 顯示

### CLI 整合方式
- `extract` 指令透過 `SchedulerService.extract_knowledge()` 委派，不直接呼叫 `KnowledgeExtractor`
- 原因：repl.py 呼叫慣例是 `sched.*`，保持一致

## 問題與解法

| 問題 | 解法 |
|------|------|
| E2E TOOL_REGISTRY 計數 FAIL (10→11) | 手動更新 check 數字 |
| registry.py lambda 需要 KnowledgeExtractor | 改用 sched.extract_knowledge() 委派 |

## 修改的檔案清單

- `services/knowledge_extractor.py` （新建）
- `services/token_counter.py` （新建）
- `services/scheduler.py` （新增方法 + 模板更新）
- `mcp_app/server.py` （新增 extract_knowledge tool）
- `tools/registry.py` （新增 ToolEntry extract/ex，計數 10→11）
- `e2e_test.py` （Step 21 + Step 22，計數 183→224）
