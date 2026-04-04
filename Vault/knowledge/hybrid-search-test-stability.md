---
type: knowledge
tags: [search, bm25, vector, hybrid, testing]
date: 2026-04-04
---

# Hybrid Search（BM25 + Vector）搜尋測試穩定性

## 核心知識

混合搜尋（BM25 40% + Vector 60%，RRF 合併）的搜尋結果會因 **corpus size** 和 **token 語意** 而變化：

- **BM25**：精確 token 匹配，適合唯一碼、關鍵字、精確查詢
- **Vector**：語意相似度，適合自然語言查詢，無意義唯一碼分數近 0
- **RRF（Reciprocal Rank Fusion）**：BM25 rank + Vector rank 加權合併

## 問題表現

唯一 marker token（如 `vault_e2e_unique_marker_x7q9`）在不同 corpus size 下：
- DB 大（515 vectors）：BM25 rank=1 + Vector rank=低 → 合併後仍排前
- DB 小（439 vectors）：BM25 rank=1 + Vector rank=更低 → 合併後可能被其他語意相關文件推到 top_k 外

## 解法

E2E / 單元測試中，精確 token 測試應指定 `iMode="keyword"` 強制 BM25 主導：

```python
# ❌ 不穩定：corpus 變化會影響排名
result = search_formatted("unique_token_x7q9")

# ✅ 穩定：BM25 精確匹配，不受 corpus size 影響
result = search_formatted("unique_token_x7q9", iMode="keyword")
```

## 注意事項

- `iMode="semantic"` → Vector 權重大幅提升，BM25 降低
- `iMode="keyword"` → BM25 權重大幅提升，Vector 降低
- `iMode=""` (default) → 均衡模式，適合一般語意查詢
- 測試唯一 token 永遠用 `keyword`；測試語意相關性永遠用 `semantic` 或 default
