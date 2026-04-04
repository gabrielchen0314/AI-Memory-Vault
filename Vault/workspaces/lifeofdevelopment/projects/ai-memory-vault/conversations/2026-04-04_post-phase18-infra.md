---
type: conversation
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
date: 2026-04-04
session: post-phase18-infra
phase: 18
topics:
  - gitignore-merge
  - scheduler-architecture-review
  - load-vault-instructions-refactor
  - eod-checklist-fix
---

# Post-Phase-18 基礎設施修正

## 摘要

Phase 18 完成後發現兩個維護問題：`.gitignore` 缺少 ML/env 相關條目，以及
`end-of-day-checklist.md` 從未被注入到 MCP session，導致 AI 收工時漏掉 handoff 步驟。
兩者都已修正，並為後者建立了可擴充的 frontmatter-driven 機制。

---

## 對話重點

### 1. .gitignore 整合

**背景**：舊 repo `AI-Memory-Vault_OLD/.gitignore` 有新版本未含的條目。

**修正**：合併至 `d:\AI-Memory-Vault\.gitignore`，新增：
- `venv/`、`ENV/`（額外 venv 模式）
- `*.pth`、`*.onnx`（ML 模型檔，獨立成一節）
- `.env.*` + `!.env.example`（擴充 env 模式）
- `.obsidian/workspace.json`、`.obsidian/workspace-mobile.json`

---

### 2. 兩套排程系統討論

**問題**：APScheduler daemon 和 `.bat` + Windows Task Scheduler 功能重疊，要整合嗎？

**結論：不整合**
| 系統 | 用途 |
|------|------|
| `.bat` + Task Scheduler | 主要使用；Windows 專屬但可設定開機恢復 |
| `main.py --scheduler` APScheduler | 跨平台備用；Linux/Mac server 部署用 |

- `generate_*_summary()` 永遠覆寫，無狀態，重複執行無害
- 兩套各有存在理由，強制整合反而增加複雜度

---

### 3. `_load_vault_instructions()` 重構

**根本問題**：`mcp_app/server.py` 只 hardcode 注入 `nav.md` 和 `handoff.md` 兩個檔案。
`end-of-day-checklist.md` 加入 `_config/` 後從未被注入，AI 每次收工都不知道有 SOP。

**舊邏輯（問題版）：**
```python
for fname in ["nav.md", "handoff.md"]:
    content = read_note(f"_config/{fname}")
    ...
```

**新邏輯（frontmatter-driven）：**
```python
config_files = sorted(_config_path.glob("*.md"))
for fpath in config_files:
    raw = fpath.read_text(encoding="utf-8")
    if "inject: true" in _parse_frontmatter(raw):
        label = fpath.stem
        sections.append(f"### [{label}]\n{raw}")
```

**加入 `inject: true` 的檔案：**
- `_config/nav.md` ✅
- `_config/handoff.md` ✅  
- `_config/end-of-day-checklist.md` ✅（首次被注入）
- `_config/agents.md` — 刻意不加（太長，每次 session 注入浪費 context）

**好處**：
- 未來新增任何 `_config/` 指令檔，只需加 `inject: true`，零程式碼修改
- E2E 52/52 PASS 持續通過

---

## 架構決策記錄

| 決策 | 結論 | 理由 |
|------|------|------|
| `inject: true` vs hardcode | frontmatter-driven | 可擴充；新檔不需改程式碼 |
| agents.md 是否注入 | 否 | 太長，session context 浪費 |
| 兩套排程整合 | 不整合 | 各有平台定位，強制整合增複雜度 |

## 影響的檔案

| 檔案 | 修改類型 |
|------|---------|
| `AI_Engine/mcp_app/server.py` | `_load_vault_instructions()` 重構 |
| `Vault/_config/nav.md` | frontmatter 加 `inject: true` |
| `Vault/_config/handoff.md` | frontmatter 加 `inject: true` |
| `Vault/_config/end-of-day-checklist.md` | frontmatter 加 `inject: true` |
| `.gitignore` | 合併 OLD 專案缺失條目 |
