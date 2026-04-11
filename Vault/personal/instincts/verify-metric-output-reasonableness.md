---
id: "verify-metric-output-reasonableness"
trigger: 實作了任何產生數值/百分比/評分的功能，且第一次看到輸出結果時
confidence: 0.8
domain: workflow
source: "session-observation"
created: "2026-04-11"
sequence: 45
---

# 統計/評分功能需用實際數據驗證合理性

## 動作
實作評分/統計類功能時，完成後必須用**實際數據**驗證輸出結果是否「看起來合理」——不只是「有值」。特別注意：\n1. 平均值計算時，無數據的項目是否被當作 0 拉低結果\n2. 百分比/比率是否使用了正確的分母\n3. 評分邏輯是否區分了「數據不足」和「表現差」兩種狀態

## 證據
2026-04-11：weekly/monthly analysis 自動評分。avg_qa=0.6 因無 QA 資料的對話被當 0 計入平均，導致 Prompt 技巧給 5/5 假高分。問題解決率用 success_rate/20 概念錯誤。修正後：無 QA 時給中間值 3、問題解決率改為 solved_problems/total_problems。
