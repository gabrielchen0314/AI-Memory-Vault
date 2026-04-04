---
type: knowledge
tags: [langchain, vectorstore, chromadb, indexing]
date: 2026-04-04
---

# LangChain `langchain_index` cleanup 參數語意

## 核心知識

LangChain 的 `langchain_index()` 有三種 `cleanup` 模式，語意差異重要：

| cleanup 模式 | 行為 | 適用情境 |
|-------------|------|---------|
| `None` | 只新增/更新，從不刪除 | 永久只增不刪的場景 |
| `incremental` | 只處理本次傳入的文件；**不刪**不在本次清單的舊向量 | 單檔/批次即時更新 |
| `full` | 以本次傳入為完整快照；**刪除** DB 中不在清單的所有向量 | 全量掃描同步 |

## 問題表現

- 使用 `cleanup="incremental"` 做全量掃描後，已刪磁碟的檔案對應向量仍殘留在 ChromaDB
- `langchain_index(chunks, ..., cleanup="incremental")` 中的 chunks = 本次掃描到的所有文件
  - 但它不知道**哪些是「應該被刪的舊向量」**，因此不會刪除
  - 需要用 `cleanup="full"` 才會把「不在本次清單中的向量」全部清除

## 解法

```python
# 全量掃描 sync → 用 full
langchain_index(all_chunks, record_manager, vectorstore, cleanup="full", ...)

# 單檔/批次即時更新 → 繼續用 incremental（只影響傳入的文件）
langchain_index(single_chunk, record_manager, vectorstore, cleanup="incremental", ...)
```

## 注意事項

- `full` 模式代價較高（需要完整掃描所有 DB 記錄），不適合頻繁呼叫
- 建議：daily 寫入用 `incremental`，weekly 定期全量 sync 用 `full`
- RecordManager（SQLite）記錄每個 chunk 的 hash 與 source_id，cleanup 的判斷依此進行
