---
id: "vscode-jsonl-ai-response-kind-none"
trigger: 從 VS Code chatSessions JSONL 解析 AI 回應文字
confidence: 0.9
domain: vscode
source: "session-observation"
created: "2026-04-12"
sequence: 62
---

# VS Code JSONL — AI 回應的 kind 是 None 而非 '?'

## 動作
檢查 response 陣列中 kind=None（`r.get('kind') is None`）且 value 為字串的項目，才是 AI markdown；不要找 kind='?'

## 證據
驗證於 ea20f4c8 JSONL，修正後正確提取 17 個 AI 回應；修正前全空白
