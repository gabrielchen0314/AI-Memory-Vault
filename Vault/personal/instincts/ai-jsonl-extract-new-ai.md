---
id: "ai-jsonl-extract-new-ai"
trigger: AI 文字無法從 JSONL 提取（extract_new 產生空 AI 文字）
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-12"
sequence: 54
---

# 問題：AI 文字無法從 JSONL 提取（extract_new 產生空 AI 文字）

## 動作
改為偵測 rk is None（無 kind 欄位），value 才是 AI markdown 字串

## 證據
原程式碼假設 AI 回應的 kind='?'，但實際格式是無 kind 欄位（kind=None）的 response item
