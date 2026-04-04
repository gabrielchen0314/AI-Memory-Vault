---
agent: agent
tools:
  - ai-memory-vault/search_vault
description: "搜尋 Vault 知識庫。Use when: 需要查找記憶、筆記、規則、專案資料。"
---

使用 `search_vault` 工具搜尋 Vault 知識庫。

查詢內容：${input:query:要搜尋的內容（可用中文或英文）}

可選過濾（留空代表不過濾）：
- 分類 category：${input:category:work / life / knowledge（留空不過濾）}
- 類型 doc_type：${input:doc_type:rule / project / meeting（留空不過濾）}

請將搜尋結果整理後以易讀的格式呈現，並標示每筆結果的來源路徑。
