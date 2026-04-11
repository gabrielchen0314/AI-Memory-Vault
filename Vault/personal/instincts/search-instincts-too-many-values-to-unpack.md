---
id: "search-instincts-too-many-values-to-unpack"
trigger: search_instincts too many values to unpack
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-11"
sequence: 30
---

# 問題：search_instincts too many values to unpack

## 動作
改用 dict 存取 _Hit.get('source')

## 證據
VaultService.search() 回傳 dict，InstinctService 假設是 (doc, score) tuple
