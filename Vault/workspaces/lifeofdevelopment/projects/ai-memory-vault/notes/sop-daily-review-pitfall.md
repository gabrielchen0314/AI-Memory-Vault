---
type: note
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
created: 2026.04.04
topic: SOP 流程問題 — generate_daily_review 設計陷阱
---

# SOP 問題：generate_daily_review 的正確使用方式

## 問題描述

**場景**：同一天執行兩次收工 SOP（跨 session），第二次呼叫 `generate_daily_review` 後 daily review 未更新。

## 根本原因

1. **冪等設計**：`generate_daily_summary()` 檢查 `if not os.path.exists(absPath)` — 檔案已存在直接跳過
2. **無 projects 參數**：MCP tool 簽名 `generate_daily_review(date: str = "")` 不接受 projects 資料，傳入會被靜默忽略
3. **只生成空白模板**：即使首次建立，也只是空白框架，不包含任何今日工作內容

## 正確 SOP 流程

```
1. 首次收工（一天第一次）：
   - 呼叫 generate_daily_review → 建立空白模板存根
   - 立刻呼叫 write_note(overwrite) → 填入當天完成內容

2. 後續收工（同天多次）：
   - 直接呼叫 write_note(overwrite) → 覆寫為最新完整內容
   - 不要再呼叫 generate_daily_review（冪等會跳過）
```

## 改進方向（未來 Phase）

- `generate_daily_review` 應改為**永遠覆寫**（daily review 不是用戶長期手動編輯的檔案）
- 或新增 `force: bool = False` 參數繞過冪等
- 或重新設計：daily review 由 AI 在一天結束時自動彙整 conversations/ 內容生成

## 受影響的同類工具

`generate_weekly_review` / `generate_monthly_review` 可能有相同冪等問題。
同一週/月底若多次跨 session 收工，同樣需要用 `write_note(overwrite)` 補寫。
