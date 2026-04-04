---
agent: agent
tools:
  - ai-memory-vault/read_note
description: "讀取 Vault 中指定筆記的完整內容。Use when: 需要查看某個特定檔案的原始內容。"
---

使用 `read_note` 工具讀取 Vault 中指定筆記的完整內容。

筆記路徑（相對於 Vault 根目錄）：${input:file_path:例如 _system/core-memory.md 或 knowledge/my-note.md}

請完整呈現讀取到的內容，並在最後標示檔案路徑。
