---
agent: agent
tools:
  - ai-memory-vault/write_note
description: "寫入或更新 Vault 筆記。Use when: 需要儲存知識、記錄筆記、建立文件。"
---

使用 `write_note` 工具將筆記寫入 Vault，並自動索引至向量資料庫。

目標路徑（相對於 Vault 根目錄）：${input:file_path:例如 knowledge/my-note.md 或 life/journal/2026-03-30.md}

筆記內容：
${input:content:筆記的完整內容（Markdown 格式）}

**路徑規則：**
- 公司專案筆記 → `work/{公司名稱}/projects/{ProjectName}/`
- 永久知識卡片 → `knowledge/`
- 日記週記 → `life/journal/`
- 學習筆記 → `life/learning/`
- 共用技術筆記 → `work/_shared/`

⚠️ 此工具會覆蓋已存在的檔案，請確認路徑正確。
