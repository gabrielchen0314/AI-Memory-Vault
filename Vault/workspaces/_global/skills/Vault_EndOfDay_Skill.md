---
type: skill
id: vault-end-of-day
title: 收工 SOP — 結束工作日流程
domain: workflow
created: 2026-04-12
last_updated: 2026-04-12
ai_summary: "AI Memory Vault 每日收工的完整操作流程與 MCP 工具呼叫順序"
applicable_agents: [GitCommitter, LearnTrigger, Planner]
---

# 收工 SOP — 結束工作日流程

> **觸發條件**：使用者說「收工」時才執行。不可在對話中途自動執行。

---

## 執行順序

```
Step 1 → 專案日報（每個活躍專案）
Step 2 → 對話紀錄（摘要 + 詳細，一次呼叫）
Step 3 → 萃取直覺（從 detail 判斷）
Step 4 → 各活躍專案 status.md 更新
Step 5 → _config/handoff.md 更新
Step 6 → 每日總回顧（最後寫，它是總表）
Step 7 → roadmap.md（完成 Phase / 里程碑才更新）
```

---

## Step 1：專案每日進度

**工具**：`generate_project_daily(org, project, date?)`  
**路徑**：`workspaces/{org}/projects/{project}/daily/YYYY-MM-DD.md`  
**內容**：今日完成、遇到的問題、明日計畫、學到的事  
**注意**：有實作的專案各一份，冪等（已存在不覆寫）

---

## Step 2：對話紀錄

**工具**：`log_ai_conversation(organization, project, session_name, content, vscode_session_id?, detail?)`

```python
log_ai_conversation(
    organization      = "LIFEOFDEVELOPMENT",
    project           = "ai-memory-vault",
    session_name      = "描述性名稱（kebab-case）",
    content           = "## 對話摘要\n...",           # 簡短摘要
    vscode_session_id = "從系統提示 UUID 取得",        # 自動填充 files/commands
    detail = {
        "topic":    "主題描述",
        "problems": [{"problem": "...", "cause": "...", "solution": "..."}],
        "learnings": ["..."],
        "decisions": [{"decision": "...", "options": "A/B", "chosen": "A", "reason": "..."}],
        "interaction_issues": [
            {
                "type":        "misunderstanding|correction|ambiguity|over-action|missed-intent",
                "description": "發生了什麼",
                "user_intent": "使用者原本想要",
                "ai_behavior": "AI 實際做了什麼",
                "root_cause":  "為什麼誤判",
                "resolution":  "如何解決",
                "prevention":  "未來如何避免"
            }
        ]
        # qa_pairs / files_changed / commands → 由 vscode_session_id 自動提取，不需手填
    }
)
```

**如何取得 session_id**：系統提示 `VSCODE_TARGET_SESSION_LOG` 路徑中的 UUID

---

## Step 3：萃取直覺

從 `detail` 欄位判斷是否需要建立 Instinct：

| 觸發條件 | 動作 |
|---------|------|
| `detail.problems` 有可避免錯誤 | `create_instinct(...)` |
| `detail.learnings` 有值得記住的模式 | `create_instinct(...)` |
| `detail.interaction_issues` 有使用者糾正 | `create_instinct(...)`（記錄正確做法） |
| 已有相關直覺被驗證成功 | `update_instinct(confidence_delta=+0.1)` |
| 已有相關直覺被驗證失敗 | `update_instinct(confidence_delta=-0.1)` |

初始信心度：0.6。信心 ≥ 0.7 下次自動提醒。

---

## Step 4：專案狀態更新

**工具**：`write_note("workspaces/{org}/projects/{project}/status.md", content, "overwrite")`  
**內容**：
- 工作脈絡（更新最近 Session 摘要）
- 待辦清單（進行中 / 待處理 / 已完成）
- 重要決策

---

## Step 5：交接索引

**工具**：`edit_note("_config/handoff.md", old_text, new_text)`  
**內容**：更新「上次活躍專案」清單 + 跨專案備註

---

## Step 6：每日總回顧

**工具**：`generate_daily_review(date?)`  
**路徑**：`personal/reviews/daily/YYYY-MM-DD.md`  
**內容**：今日活躍專案、各專案重點一句話、明日接續  
**注意**：永遠覆寫（不是冪等），最後才寫

---

## Step 7：Roadmap 更新（條件性）

**觸發條件**：完成一個 Phase / 版本號提升 / 重要里程碑才更新  
**不觸發**：日常功能實作、小 Bug 修復  
**工具**：`edit_note("workspaces/{org}/projects/{project}/notes/roadmap.md", old, new)`  
**動作**：將完成的 Phase 標記 ✅，補完成細節；更新「進行中」段落
