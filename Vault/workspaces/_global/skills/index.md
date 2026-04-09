---
type: skill-index
category: skills
created: 2026-04-10
last_updated: 2026-04-10
ai_summary: "AI Memory Vault Skills 知識包索引 — 列出所有可用技能包及其適用場景"
---

# 🎯 Skills 知識包索引

> Skills 是可被 Agent 即時載入的可重用知識包。
> 使用 `list_skills` 查看清單，`load_skill` 載入完整內容。

## 可用技能包

| 技能包 | 適用場景 | Agent |
|--------|----------|-------|
| `VaultWriteConventions_Skill.md` | 撰寫 Vault 筆記時確認格式規範 | 全體 |
| `Debug_Skill.md` | 除錯流程 + 逐步收縮法 | Architect, CodeReviewer |
| `ApiMap_Skill.md` | 建立 API Map 文件格式 | DocUpdater, Architect |

## 使用方式

```
# AI 工作前
list_skills()                          → 查看可用技能包
load_skill("Debug_Skill")              → 載入除錯知識包
dispatch_agent("@Architect")           → 切換至架構師模式
```
