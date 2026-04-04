---
type: system
created: 2026.04.01
last_updated: 2026.04.04
inject: true
---

# 🤝 Session Handoff

> 記錄上次工作的活躍專案，供下次 AI 對話開場快速定位。
> 各專案詳細狀態（待辦 + 工作脈絡）見各專案的 `status.md`。

## 上次活躍專案

| 專案 | 組織 | 狀態 | 詳細 |
|------|------|------|------|
| ai-memory-vault | LIFEOFDEVELOPMENT | 進行中 | workspaces/lifeofdevelopment/projects/ai-memory-vault/status.md |

## 跨專案備註

- Phase 18 Items 1+2 已完成：52/52 E2E 通過
  - APScheduler daemon（`services/auto_scheduler.py`）+ `main.py --scheduler`
  - Daily note auto-digest（`_scan_today_conversations` + 今日 AI 對話區塊）
- MCP instructions 注入機制已改為 frontmatter-driven：`_config/*.md` 含 `inject: true` 者自動注入
  - `nav.md`、`handoff.md`、`end-of-day-checklist.md` 已加入 `inject: true`
  - 未來新增 `_config/` 指令檔只需加 `inject: true`，無需改程式碼
- `auto_tasks.ps1` 方法名已修正（_review → _summary）
- `.gitignore` 已整合 OLD 專案缺失條目（venv、ENV、ML 模型、Obsidian workspace）
- 兩套排程系統：`.bat` 為主（Windows），`--scheduler` 跨平台備用
- 下次優先處理：Phase 18 Item 3（Embedding 策略評估）或 Item 4（BM25/Vector 比重）

## 規則提醒

- 新功能必須確認有 DB 更新路徑（寫入型工具）
- 不重複接口：batch vs single 是不同用途，不算重複
- 新規則或工具加入後，必須更新 `_config/agents.md`
- 收工前必須先讀 `_config/end-of-day-checklist.md`（5 個必做步驟）
