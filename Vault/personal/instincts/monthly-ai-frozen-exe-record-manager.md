---
id: "monthly-ai-frozen-exe-record-manager"
trigger: "monthly-ai 在 frozen exe 中失敗：record_manager 尚未初始化"
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-11"
sequence: 46
---

# 問題：monthly-ai 在 frozen exe 中失敗：record_manager 尚未初始化

## 動作
在三個 scheduler 進入點加入 _bootstrap(_Config)

## 證據
_start_scheduler_task() 未呼叫 _bootstrap() 初始化 vectorstore/embeddings
