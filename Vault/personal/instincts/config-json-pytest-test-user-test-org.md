---
id: "config-json-pytest-test-user-test-org"
trigger: config.json 被 pytest 污染（test_user/TEST_ORG 路徑）
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-11"
sequence: 9
---

# 問題：config.json 被 pytest 污染（test_user/TEST_ORG 路徑）

## 動作
從 config.json.bak 還原

## 證據
測試沒有妥善 teardown
