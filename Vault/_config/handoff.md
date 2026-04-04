---
type: system
created: 2026.04.01
last_updated: 2026.04.04
---

# 🤝 Session Handoff

> 記錄上次工作的活躍專案，供下次 AI 對話開場快速定位。
> 各專案詳細狀態（待辦 + 工作脈絡）見各專案的 `status.md`。

## 上次活躍專案

| 專案 | 組織 | 狀態 | 詳細 |
|------|------|------|------|
| ai-memory-vault | LIFEOFDEVELOPMENT | 進行中 | workspaces/LIFEOFDEVELOPMENT/projects/ai-memory-vault/status.md |

## 跨專案備註

- Phase 15 已完成：26/26 E2E 通過，batch_write_notes + update_todo 已上線
- 下次優先處理：Vault integrity check（偵測孤立 ChromaDB 向量無對應 .md 檔案）
- MCP 工具現為 15 個，所有工具均已 E2E 驗證
- Coding 規則已建立（`_global/rules/` + `Chinesegamer/rules/` + `lifeofdevelopment/rules/`）

## 規則提醒

- 新功能必須確認有 DB 更新路徑（寫入型工具）
- 不重複接口：batch vs single 是不同用途，不算重複
- 新規則或工具加入後，必須更新 `_config/agents.md`
