---
type: conversation-detail
date: 2026-04-11
session: interaction-issues-schema-design
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
tags: [conversation, detail]
---

# 2026-04-11 interaction-issues-schema-design — 詳細對話紀錄

## 對話概要
- **主題**：log_ai_conversation detail 新增 interaction_issues 雙向互動品質欄位（B 方案）

## 修改的檔案清單

| 檔案 | 操作 | 摘要 |
|------|------|------|
| `_config/agents.md` | 修改 | detail 參數新增 interaction_issues 欄位定義（6 子欄位 + 5 種 type）、收工 SOP 步驟 3 新增 interaction_issues → create_instinct、建立 Instinct 時機新增 correction/misunderstanding 兩點、AI 使用指南新增萃取說明 |
| `_config/end-of-day-checklist.md` | 修改 | 步驟 2 新增 interaction_issues 回顧指引，說明 AI 應主動回顧整段對話識別互動問題 |

## 學到的知識

- log_ai_conversation detail 的 interaction_issues 欄位可記錄溝通問題雙方視角（使用者意圖 / AI 行為 / 根本原因 / 預防方式）
- 獨立欄位比混在 problems 裡更適合未來趨勢分析
- type 分類：misunderstanding / correction / ambiguity / over-action / missed-intent

## 決策記錄

| 決策 | 選項 | 最終選擇 | 理由 |
|------|------|---------|------|
| interaction_issues 欄位設計方案 | A: 放在 problems 加 type:interaction / B: 獨立 interaction_issues 欄位 / C: 再加 collaboration_score 量化評分 | B | 職責分離（技術問題 vs 溝通問題），未來可做互動品質趨勢分析；量化評分初期資料量不足暫不加 |
