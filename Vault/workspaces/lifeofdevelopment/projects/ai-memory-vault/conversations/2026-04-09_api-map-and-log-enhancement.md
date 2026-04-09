## 對話摘要

### 主題
API Map 規則整備 + log_ai_conversation 強化

### 關鍵決策
1. APIMapGuide 存為全域規則 `15-api-map-writing-guide.md`（不限定組織）
2. `02-project-api-map-sync.md` 移除硬編碼副檔名，改為通用判斷
3. PersonalMemory 不遷移入 Vault，僅作為格式參考
4. `log_ai_conversation` 新增 `detail` 參數（方案 A），結合 conversation summary 萃取（方案 B）
5. 收工 SOP 步驟 2+3 合併為一次 `log_ai_conversation` 呼叫

### 修改的檔案
- `AI_Engine/services/scheduler.py` — 新增 `iDetail` 參數 + `_render_conversation_detail` 渲染器
- `AI_Engine/mcp_app/tools/scheduler_tools.py` — MCP 端新增 `detail` 參數
- `Vault/_config/agents.md` — 收工 SOP 更新、工具版本 v3.6
- `Vault/_config/end-of-day-checklist.md` — 步驟合併、標註全域共用
- `Vault/workspaces/_global/rules/15-api-map-writing-guide.md` — 新增
- `Vault/workspaces/_global/rules/02-project-api-map-sync.md` — 修正
- `User/prompts/global-prompts-maintenance.instructions.md` — 加入 rule 15
