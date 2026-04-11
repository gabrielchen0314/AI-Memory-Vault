---
id: prompt
trigger: 評分邏輯不合理（問題解決率、Prompt 技巧假高分）
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:lifeofdevelopment/ai-memory-vault"
created: "2026-04-11"
sequence: 39
---

# 問題：評分邏輯不合理（問題解決率、Prompt 技巧假高分）

## 動作
問題解決率改為有解法比率；平均 QA 只計有 QA 記錄的對話；無 QA 時 Prompt 技巧給中間值 3

## 證據
問題解決率用 success_rate/20 概念錯誤；avg_qa 被無 QA 的對話拉低至 0.6
