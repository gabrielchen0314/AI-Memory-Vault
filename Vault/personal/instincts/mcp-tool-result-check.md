---
id: "mcp-tool-result-check"
trigger: "呼叫任何 MCP write 工具（write_note, edit_note, log_ai_conversation 等）後"
confidence: 0.8
domain: workflow
source: "session-observation"
created: "2026-04-11"
sequence: 20
---

# MCP 工具呼叫後必須確認回傳結果，ERROR 立即處理

## 動作
呼叫 MCP 工具後立即確認回傳結果，出現 ERROR 立即處理，不能繼續下一步

## 證據
2026-04-11：write_note 用錯參數名稱（path → file_path），工具回報 ERROR 但 AI 繼續執行收工流程，導致日報空白，直到使用者發現才補寫
