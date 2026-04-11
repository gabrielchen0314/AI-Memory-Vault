---
id: "fakedtype-nameerror"
trigger: _FakeDtype NameError
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-11"
sequence: 28
---

# 問題：_FakeDtype NameError

## 動作
不 del _FakeDtype 和 _FakeTensor

## 證據
del _FakeDtype 刪除了 __getattr__ 運行時需要的類別
