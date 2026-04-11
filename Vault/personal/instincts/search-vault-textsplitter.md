---
id: "search-vault-textsplitter"
trigger: search_vault TextSplitter 匯入失敗
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-11"
sequence: 29
---

# 問題：search_vault TextSplitter 匯入失敗

## 動作
移除 hack，改用正常 import

## 證據
舊的假 langchain_text_splitters 套件 hack 與 torch stub 衝突
