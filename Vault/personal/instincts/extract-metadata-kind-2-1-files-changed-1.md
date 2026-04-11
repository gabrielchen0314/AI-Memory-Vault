---
id: "extract-metadata-kind-2-1-files-changed-1"
trigger: "extract_metadata 只讀最後一個 kind=2 快照，只有 1 個 files_changed 和 1 個 command"
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-12"
sequence: 56
---

# 問題：extract_metadata 只讀最後一個 kind=2 快照，只有 1 個 files_cha

## 動作
改為掃描所有 kind=2 行，用 toolCallId 去重，最終正確提取 29 個檔案 + 362 個指令

## 證據
JSONL 的 kind=2 是增量快照，每個 request 完成後都新增一行，只讀最後一行等於只看最後一個 request
