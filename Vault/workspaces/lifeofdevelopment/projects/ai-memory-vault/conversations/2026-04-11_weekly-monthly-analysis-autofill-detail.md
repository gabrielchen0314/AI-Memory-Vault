---
type: conversation-detail
date: 2026-04-11
session: weekly-monthly-analysis-autofill
project: ai-memory-vault
org: lifeofdevelopment
tags: [conversation, detail]
---

# 2026-04-11 weekly-monthly-analysis-autofill — 詳細對話紀錄

## 對話概要
- **主題**：AI 週報/月報自動填充實作

## 關鍵問答紀錄

### Q1: 為什麼週報/月報欄位都是空的？
- **AI 分析**：_render_ai_weekly_analysis_template 只接收檔名清單和 token 統計，從未解析 detail 檔的結構化內容
- **決策**：新增 _parse_all_conversation_details + _compute_analysis_metrics 方法鏈
- **替代方案**：在 log_ai_conversation 時預計算指標存入 frontmatter

### Q2: 評分邏輯哪裡有問題？
- **AI 分析**：問題解決率用 success_rate/20 概念錯誤（應用有解法的 problem 比率）；Prompt 技巧因 avg_qa=0.6（無 QA 資料被當 0）給假高分；溝通效率閾值太嚴
- **決策**：問題解決率改為 solved_problems/total_problems、Prompt 技巧無 QA 時給中間值 3、閾值調整
- **替代方案**：手動填分（但違反自動化目標）

### Q3: 為什麼對話數從 20 變 11？
- **AI 分析**：iProjectConvs 包含 *-detail.md 檔名，被計算為獨立對話。排除 detail 後只有 11 個主對話檔
- **決策**：在模板渲染中過濾 detail 檔、metrics 使用 _parse_all_conversation_details 的正確計數
- **替代方案**：在 _scan_all_project_conversations 中就排除 detail 檔

## 修改的檔案清單

| 檔案 | 操作 | 摘要 |
|------|------|------|
| `AI_Engine/services/scheduler.py` | 新增+修改 | 新增 _parse_all_conversation_details, _extract_detail_data, _compute_analysis_metrics, _auto_score, _extract_weekly_summary；修改 generate_ai_weekly/monthly_analysis 傳遞 metrics；重寫 _render_ai_weekly/monthly_analysis_template 使用 metrics 填充所有欄位 |

## 遇到的問題與解決

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| 對話數重複計算（含 detail 檔） | iProjectConvs 包含 *-detail.md 檔名 | 模板渲染時過濾 detail 檔、metrics 內部跳過 detail |
| 錯誤模式表根本原因/改進方式全是 — | error_patterns 只存 {pattern: count} 無上下文 | 改為 error_details 列表帶完整 problem/cause/solution |
| 評分邏輯不合理（問題解決率、Prompt 技巧假高分） | 問題解決率用 success_rate/20 概念錯誤；avg_qa 被無 QA 的對話拉低至 0.6 | 問題解決率改為有解法比率；平均 QA 只計有 QA 記錄的對話；無 QA 時 Prompt 技巧給中間值 3 |
| Token 表 Output Tokens 永遠為 — | 無法分離 input/output token | 簡化為單欄「預估 Token」 |

## 學到的知識

- detail 解析只用 Markdown 結構（## / ### / 表格行 / 列表），不依賴 frontmatter，鬆耦合
- 平均值需區分有無資料：無 QA 記錄的對話不納入平均輪數計算
- 錯誤模式要帶上下文：只存 pattern+count 不夠，要帶 cause/solution 才有分析價值
- gabrielchen0314 組織目錄已不存在，舊週報的快取檔案含過時資料需注意冪等設計
- 自動評分邏輯不宜太機械化，需要區分「資料不足」和「表現差」兩種情境

## 決策記錄

| 決策 | 選項 | 最終選擇 | 理由 |
|------|------|---------|------|
| 用 Markdown 結構解析 detail 而非 frontmatter | A. 解析 frontmatter YAML / B. 解析 Markdown 結構 | B | detail 的結構化資料在 Markdown body 而非 frontmatter（frontmatter 只有 type/date/session 等 metadata） |
