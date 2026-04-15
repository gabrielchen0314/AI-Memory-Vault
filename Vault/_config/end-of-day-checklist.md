---
type: system
created: 2026.04.04
last_updated: 2026.04.12
inject: true
---

# 🔚 收工檢查清單（End-of-Day Checklist）

> 每次工作結束時，AI 與使用者應依序完成以下項目。
> 詳細步驟與工具呼叫參數：`load_skill("Vault_EndOfDay_Skill")`

---

## 檢查項目

| # | 項目 | 條件 | 路徑 |
|---|------|------|------|
| 1 | 專案每日進度 | 必須（每個活躍專案） | `{org}/projects/{project}/daily/YYYY-MM-DD.md` |
| 2 | 對話紀錄（摘要+詳細） | 必須 | `{org}/projects/{project}/conversations/` |
| 3 | 直覺萃取 | 有犯錯/學到新知/被糾正時 | `personal/instincts/` |
| 4 | 知識卡片 | 有值得保留的概念時 | `knowledge/{topic-slug}.md` |
| 5 | 專案狀態更新 | 必須（每個活躍專案） | `{org}/projects/{project}/status.md` |
| 6 | 交接索引更新 | 必須 | `_config/handoff.md` |
| 7 | 每日總回顧 | 必須（最後寫） | `personal/reviews/daily/YYYY-MM-DD.md` |
| 8 | Roadmap 更新 | 完成 Phase / 里程碑時 | `{org}/projects/{project}/notes/roadmap.md` |

## 執行順序

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8（條件性）
```

> **依賴關係**：`status.md`(5) 必須在 daily(1) + conversations(2) 之後；每日總回顧(7) 最後寫（它是總表）。

## 備註

- 所有寫入透過 `write_note` MCP 工具，自動索引至向量資料庫
- 此清單本身不需每次更新，除非流程有調整
