---
type: knowledge
tags: [sop, workflow, vault, end-of-day]
created: 2026-04-04
---

# 收工 SOP — status.md 必須最後更新

## 核心規則

收工文件的寫入順序有依賴關係，**status.md 必須在 daily 和 conversations 都寫完之後才更新**。

## 錯誤模式

在架構重構完成後立刻寫 `status.md`，然後再補 daily、conversations → status.md 沒有反映最終完成狀態，待辦項目未正確標記。

## 正確順序

```
1. daily（今日技術細節）
2. conversations（AI 對話決策紀錄）
3. knowledge（有新東西才寫）
4. status.md ← 此時才知道今天真正完成了什麼
5. _config/handoff.md（跨專案索引）
6. personal/reviews/daily（最後，做總表）
```

## 原因

`status.md` 的「已完成」區段依賴 daily + conversations 的內容才能確認。若先寫 status.md，等於在沒有掌握全貌的狀態下標記完成度。

`reviews/daily` 最後寫是因為它是其他所有文件的總結，必須等全部寫完才能準確彙整。
