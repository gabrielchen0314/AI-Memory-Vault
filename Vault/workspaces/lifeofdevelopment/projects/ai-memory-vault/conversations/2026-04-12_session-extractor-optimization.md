## 對話摘要

Session 5（跨兩個 conversation）：完善零 Token 對話提取機制與收工 SOP 優化。

### 主要工作

**承接 Session 4 的未完成項目：**
1. `auto_tasks.ps1` — `Save-Tasks()` 保留 `format_version`；`-List` 新增 `Get-OrphanedWinTasks()` 孤兒偵測
2. 刪除 v2 孤兒排程 `AI-MemoryVault-Project Daily Progress`（以管理員權限）
3. `agents.md` 收工 SOP 加入觸發條件警告（「僅使用者說收工時執行」）
4. `config.json` 寫入 `vscode_chat_dir`

**session_extractor.py 兩個 bug 修復：**
- AI 文字解析：`kind='?'` → 無 `kind` 欄位（`rk is None`）才是 AI markdown
- watermark 路徑：`vault_root.parent` → `DATA_DIR`

**log_ai_conversation 優化（~60% Token 節省）：**
- 新增 `vscode_session_id` 參數
- 自動從 JSONL 提取 `files_changed` + `commands`
- AI 只需填 `topic / problems / learnings / decisions / interaction_issues`

**新增 `extract_session_script` MCP 工具（0 Token 腳本固化）：**
- 從 chatSession 提取所有 terminal 指令 → PS1 / Python 腳本
- `output_to_file=True` 可寫入 `Vault/scripts/`
- `extract_metadata()` 改為掃描所有 kind=2 快照（非只最後一個），提取完整 29 檔案 + 362 指令

**修正 mcp.json：** 切回 venv 版本（dist exe 的 certifi 路徑失效）
