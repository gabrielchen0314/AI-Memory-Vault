---
agent: agent
tools:
  - ai-memory-vault/sync_vault
description: "同步 Vault 向量資料庫索引。Use when: 手動新增或修改大量 .md 檔案後需要重建索引。"
---

使用 `sync_vault` 工具掃描 Vault 所有 `.md` 檔案，並將變更（新增 / 修改 / 刪除）同步至 ChromaDB 向量資料庫。

請執行同步，並將結果（掃描檔案數、新增 / 更新 / 刪除的 chunk 數量）呈現給使用者。

> 💡 一般情況下不需要手動執行此指令，`write_note` 工具會自動索引。  
> 只有在直接編輯 `.md` 檔案後才需要執行。
