---
id: "vscode-jsonl-kind2-scan-all-lines"
trigger: 從 VS Code chatSessions JSONL 提取 files_changed 或 commands
confidence: 0.85
domain: vscode
source: "session-observation"
created: "2026-04-12"
sequence: 63
---

# VS Code JSONL — kind=2 需掃描全部行才能取得完整 session 記錄

## 動作
JSONL 的 kind=2 是每個 request 完成後的增量快照，需掃描所有行並以 toolCallId 去重，不能只看最後一行

## 證據
只讀最後一行只有 1 個 files_changed + 1 個 command；掃描所有行得到 29 + 362 個完整記錄
