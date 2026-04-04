---
type: system
created: 2026.04.01
last_updated: 2026.04.04
---

# 🤖 Agent 架構文件

> 此文件描述 AI Memory Vault 的 Agent 設定與能力。

## 可用工具（18 個）

| 工具 | 說明 | DB 更新 | 版本 |
|------|------|---------|------|
| `search_vault` | 搜尋記憶庫（BM25 + 向量混合） | No | v1 |
| `read_note` | 讀取指定筆記原始內容 | No | v1 |
| `write_note` | 寫入/更新筆記（自動索引） | Yes | v1 |
| `sync_vault` | 全量增量同步至向量庫 | Yes | v1 |
| `delete_note` | 刪除 .md 筆記並移除 ChromaDB 向量 | Yes | v3.5 |
| `batch_write_notes` | 批次寫入多筆，單次 ChromaDB 索引 | Yes | v3.3 |
| `update_todo` | 更新 .md 檔中 todo 的勾選狀態（不全文覆蓋） | Yes | v3.3 |
| `check_vault_integrity` | 偵測孤立 ChromaDB 向量（無對應 .md 檔案） | No | v3.3 |
| `get_project_status` | 讀取 status.md 回傳結構化資料（待辦 + 完成數 + 工作脈絡） | No | v3.4 |
| `generate_project_daily` | 生成指定專案的每日詳細進度模板（冪等） | Yes | v3 |
| `generate_project_status` | 生成指定專案的 status.md 模板（冪等，已存在不覆蓋） | Yes | v3.2 |
| `list_projects` | 列出所有組織及其專案，顯示 status.md 狀態 | No | v3.2 |
| `generate_daily_review` | 生成每日總進度表（永遠覆寫；支援 projects 參數） | Yes | v3 |
| `generate_weekly_review` | 生成每週總進度表（永遠覆寫） | Yes | v3 |
| `generate_monthly_review` | 生成每月總進度表（永遠覆寫） | Yes | v3 |
| `log_ai_conversation` | 記錄 AI 對話至專案 conversations/ | Yes | v3 |
| `generate_ai_weekly_analysis` | 生成 AI 對話週報（準確率/Token/評分） | Yes | v3 |
| `generate_ai_monthly_analysis` | 生成 AI 對話月報（趨勢/優化/評分） | Yes | v3 |

## 工具使用原則

- **不重複接口**：相同功能只有一個工具，不建立多個入口
- **DB 更新自動觸發**：所有寫入類工具都會自動更新 ChromaDB
- **冪等例外**：`generate_project_status` / `generate_project_daily` 已存在不覆蓋；`generate_*_review` 永遠覆寫
- **get vs read**：`get_project_status` 回傳結構化資料（AI 直接使用）；`read_note` 回傳原始 Markdown
- **delete_note 配對 check_vault_integrity**：先用 integrity 找孤立項目，再用 delete_note 清理

## 收工 SOP 標準流程

```
1. generate_project_daily(org, project)      → 建立今日進度模板（冪等）
2. log_ai_conversation(...)                  → 記錄本次對話
3. write_note(status.md, overwrite)         → 更新待辦事項（status.md 最後寫）
4. generate_daily_review(date, projects=[]) → 更新每日總進度（永遠覆寫）
5. write_note(_config/handoff.md)           → 更新跨專案索引
```

## Coding 規則索引

> 所有規則集中在 `workspaces/_global/rules/`（全域）與 `workspaces/{組織}/rules/`（組織特例）。
> 使用 `search_vault(query="type:rule", top_k=30)` 動態發現最新規則清單，不需手動維護此索引。

**規則套用邏輯：**
- frontmatter `workspace: _global` → 永遠套用（所有組織）
- frontmatter `workspace: {ORG}` → 僅套用於該組織的專案

## VS Code 整合（Setup 自動生成）

在 `config.json` 設定 `vscode_user_path` 後，`SetupService.run_setup()` 會在
`{vscode_user_path}/prompts/` 自動生成以下 instructions 檔（冪等，已存在不覆蓋）：

| 檔案 | 用途 |
|------|------|
| `vault-coding-rules.instructions.md` | 動態規則發現（search_vault 查詢，永不過期） |
| `VaultWriteConventions.instructions.md` | write_note 路徑規範 |
