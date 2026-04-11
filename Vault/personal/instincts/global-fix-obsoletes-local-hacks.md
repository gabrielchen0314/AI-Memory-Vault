---
id: "global-fix-obsoletes-local-hacks"
trigger: "引入全域性解決方案（stub、monkey-patch 等）修復某類問題後"
confidence: 0.7
domain: architecture
source: "session-observation"
created: "2026-04-11"
sequence: 36
---

# 全域修復後清除舊有局部 hack

## 動作
引入全域解法（如 torch stub）後，回頭檢查是否有舊的局部 hack 針對同一問題。舊 hack 可能與新方案衝突，應移除以減少複雜度。

## 證據
2026-04-11：indexer.py 舊的假 langchain_text_splitters 套件 hack 與 torch stub 方案衝突，導致 search_vault 的 TextSplitter import 失敗。移除 hack 改用正常 import 後解決。
