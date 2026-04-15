---
type: system
created: 2026.04.01
last_updated: 2026.04.12
inject: true
---

# 🗺️ Vault 導航地圖

## 目錄結構

| 目錄 | 說明 |
|------|------|
| `_config/` | AI 系統設定（導航/交接索引） |
| `workspaces/` | 工作空間（依組織分類） |
| `workspaces/_global/` | 全域共用（規則/片段/技術筆記/回顧連結） |
| `workspaces/_global/rules/` | 全域共用規則（組織規則可覆蓋） |
| `personal/` | 個人空間（日記/學習/目標/靈感/總進度） |
| `personal/reviews/daily/` | 每日總進度表（所有專案摘要） |
| `personal/ai-analysis/` | AI 對話週報與月報分析 |
| `personal/instincts/` | AI 直覺卡片（自主學習管道） |
| `knowledge/` | 永久知識卡片（概念萃取） |
| `templates/` | 模板系統 |
| `attachments/` | 附件存放 |

## 組織結構

```
workspaces/{organization}/
├── rules/              ← 組織專屬規則（覆蓋 _global/rules）
└── projects/
    └── {project}/
        ├── daily/           ← 專案每日詳細進度
        ├── notes/           ← 專案筆記 / 技術決策
        ├── meetings/        ← 專案會議紀錄
        ├── conversations/   ← AI 對話紀錄
        └── status.md        ← 專案狀態（待辦 + 工作脈絡）
```

## 進度分層

| 層級    | 路徑                                     | 內容             |
| ----- | -------------------------------------- | -------------- |
| 專案狀態  | `{org}/projects/{proj}/status.md`      | 待辦 + 工作脈絡 + 決策 |
| 專案詳細  | `{org}/projects/{proj}/daily/`         | 每日做了什麼、遇到什麼問題  |
| 專案對話  | `{org}/projects/{proj}/conversations/` | AI 工作對話紀錄      |
| 每日總結  | `personal/reviews/daily/`              | 所有專案重點摘要       |
| 每週總結  | `personal/reviews/weekly/`             | 當週進度彙整         |
| 每月總結  | `personal/reviews/monthly/`            | 當月進度彙整         |
| AI 週報 | `personal/ai-analysis/weekly/`         | 對話準確率、Token 分析 |
| AI 月報 | `personal/ai-analysis/monthly/`        | 趨勢、優化、評分       |
| 直覺卡片  | `personal/instincts/`                  | AI 自主學習直覺規則    |
| 月度復盤  | `personal/reviews/monthly/*-retrospective.md` | 月度復盤報告（含直覺系統分析） |

## _config/ 系統檔說明

| 檔案 | 用途 | inject |
|------|------|--------|
| `nav.md` | 本檔：Vault 目錄結構導航 | ✅ |
| `agents.md` | AI Agent 工具說明、SOP、工具清單 | ✅ |
| `end-of-day-checklist.md` | 收工檢查清單 | ✅ |
| `handoff.md` | 跨專案輕量索引（活躍專案清單 + 跨專案備註） | ❌ |
| `skills-rules-guide.md` | Skills vs Rules 分工指南 + 維護清單 | ❌ |

> **注意**：各專案的待辦事項與工作脈絡統一放在各專案的 `status.md`，不再使用全域 `todos.md`。
---

## 文件邊界定義

> **此專案特殊情況**：AI Memory Vault 本身往在開發的就是 MCP 工具，導致 `roadmap.md` 與 `agents.md` 看似重疊。下表明確割分职責。

### 進度相關文件三角

| 文件 | 受眾 | 更新時機 | 職責 |
|------|------|---------|------|
| `notes/roadmap.md` | 開發者（人讀） | 完成 Phase / 里程碑 | Phase 歷史、技術負債、長期展望 |
| `status.md` | AI + 開發者 | 每次收工 | 近期作戰狀態、待辦清單、重要決策 |
| `_config/agents.md` | AI（inject: true） | 工具上線後 | AI 工具操作說明、SOP、可用工具清單 |

**邊界原則**：
- MCP 工具清單（「AI 現在有哪些工具可用」）→ `agents.md`
- MCP 工具開發歷史（「哪個 Phase 加了什麼」）→ `roadmap.md`
- `roadmap.md` 不徤輪 `agents.md` 已有的工具列表，避免兩份剪輯 「唯一真實來源」原則