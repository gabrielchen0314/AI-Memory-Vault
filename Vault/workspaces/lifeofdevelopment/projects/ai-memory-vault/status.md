# AI Memory Vault — 專案狀態

last_updated: 2026.04.12

## 工作脈絡

v3.7.0 核心功能完整（40 MCP 工具、Agent/Skill/Instinct 三大系統 + 零Token 對話提取）。

### Session 1-2（torch 修復 + 40 工具測試）
- Torch Stub（main.py）攔截所有 `import torch` 呼叫
- _OnnxEmbeddings（embeddings.py）繞過 sentence_transformers，用 onnxruntime 直接推理
- 40/40 MCP 工具自動化測試全通過

### Session 3（週報/月報自動填充 + 評分修正）
- scheduler.py 新增 5 個方法
- 修正對話數量雙算、評分邏輯、錯誤模式表格欄位問題

### Session 4（build.spec 清理 + _bootstrap 修復）
- build.spec：移除 torch/sentence_transformers 依賴，exe 790MB → 395MB
- 修復 monthly-ai frozen exe 失敗（scheduler 進入點缺 `_bootstrap()`）
- 247 tests 通過

### Session 5（Session Extractor + SOP 優化）
- `session_extractor.py` 完善：
  - bug 修復：AI 文字 kind=None（非 '?'）、watermark 路徑改用 DATA_DIR
  - `extract_metadata()` 掃描所有 kind=2 快照取完整 files_changed + commands
  - `extract_script()` 提取 terminal 指令為 PS1/Python 腳本
- `log_ai_conversation` 優化：新增 `vscode_session_id` → 自動填充 files_changed + commands（~60% token 節省）
- 新增 `extract_session_script` MCP 工具（0 Token 流程固化）
- `auto_tasks.ps1`：Save-Tasks 保留 format_version；-List 新增孤兒偵測
- 刪除 v2 孤兒排程 `AI-MemoryVault-Project Daily Progress`
- `config.json` 寫入 `vscode_chat_dir`
- `mcp.json` 切回 venv 版本（dist exe certifi 失效）
- 247 tests 全通過

## 重要決策

- Torch stub 動態模組注入（11 子模組）+ _OnnxEmbeddings 零 torch 依賴
- `VAULT_DATA_DIR` 在 config.py 統一提取
- build.spec excludes 策略：明確列出套件名防止間接拖入
- JSONL extract_metadata 掃描所有 kind=2 並以 toolCallId 去重（確保完整性）
- mcp.json 維持 venv 為主版本，dist exe 為注解備用

## 待辦清單

### 進行中
（無）

### 待處理
- [ ] Docker image 建置與測試（需先安裝 Docker Desktop）
- [ ] 考慮 `vault-cli.exe --setup-section data` 以 CLI 方式設定資料目錄
- [ ] 重建 frozen exe 包含最新修改（session_extractor、auto_scheduler 等）
- [ ] 為 session_extractor.py 補充單元測試

### 已完成（本週）
- [x] Session Extractor 完善（AI 文字解析、watermark 路徑、完整提取）
- [x] log_ai_conversation vscode_session_id 自動填充
- [x] extract_session_script MCP 工具（0 Token 腳本固化）
- [x] auto_tasks.ps1 孤兒偵測 + Save-Tasks 保留 format_version
- [x] 刪除 v2 孤兒排程
- [x] config.json 寫入 vscode_chat_dir
- [x] agents.md 收工 SOP 手動觸發規則
- [x] build.spec 清理 + exe 體積減半（790→395 MB）
- [x] 修復 scheduler 進入點 _bootstrap bug
- [x] 週報/月報 AI 分析欄位自動填充
- [x] Frozen exe torch 崩潰修復
- [x] 40/40 MCP 工具自動化測試全通過
- [x] README.md 完整重寫
- [x] 247 tests 全數通過
