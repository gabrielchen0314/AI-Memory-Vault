---
type: conversation-detail
date: 2026-04-11
session: build-spec-cleanup-bootstrap-fix
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
tags: [conversation, detail]
---

# 2026-04-11 build-spec-cleanup-bootstrap-fix — 詳細對話紀錄

## 對話概要
- **主題**：Build.spec 清理 + _bootstrap 修復 + Frozen exe 驗證

## 關鍵問答紀錄

### Q1: build.spec 哪些依賴可以移除？
- **AI 分析**：torch stub 已在 main.py 攔截所有 import torch；_OnnxEmbeddings 繞過 sentence_transformers。frozen 模式不需要 torch/sentence_transformers/langchain_huggingface。
- **決策**：移除 collect_all('sentence_transformers')、torch hidden imports，加入 excludes 清單
- **替代方案**：保留但不打包（僅 excludes） vs 同時移除 hidden imports + excludes（選擇後者更徹底）

### Q2: monthly-ai 在 frozen exe 失敗的原因？
- **AI 分析**：AutoScheduler → run_task → _sync_write → VaultIndexer.sync_single → get_record_manager → 需要 vectorstore。但 _start_scheduler_task() 未呼叫 _bootstrap() 初始化。weekly-ai 因冪等成功（檔案已存在、提前返回）。
- **決策**：在 _start_scheduler_task/once/daemon 三處加入 _bootstrap(_Config)
- **替代方案**：在 AutoScheduler.__init__ 中初始化 vs 在 main.py 進入點初始化（選擇後者，與其他模式一致）

## 修改的檔案清單

| 檔案 | 操作 | 摘要 |
|------|------|------|
| `AI_Engine/packaging/build.spec` | 修改 | 移除 sentence_transformers collect_all、torch hidden imports；新增 excludes 清單 |
| `AI_Engine/main.py` | 修改 | 三個 scheduler 進入點加入 _bootstrap(_Config) 呼叫 |

## 執行的命令

| 命令 | 目的 | 結果 |
|------|------|------|
| `pyinstaller build.spec --noconfirm` | 建置 frozen exe（兩次：清理前後） | 成功，395 MB |
| `vault-cli.exe --once --headless --task monthly-ai` | 測試月報任務 | 第一次失敗（record_manager 未初始化），修復後成功（13.2 秒） |
| `vault-cli.exe --once --headless --task weekly-ai` | 測試週報任務 | 成功（4.1 秒） |
| `python -m pytest tests/ -x -q --tb=short` | 修復後跑測試 | 247 passed |

## 遇到的問題與解決

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| monthly-ai 在 frozen exe 中失敗：record_manager 尚未初始化 | _start_scheduler_task() 未呼叫 _bootstrap() 初始化 vectorstore/embeddings | 在三個 scheduler 進入點加入 _bootstrap(_Config) |
| weekly-ai 成功掩蓋了 bug | 冪等機制：檔案已存在時提前返回，未觸及寫入路徑 | 需刪除既有檔案才能測出寫入路徑的問題 |

## 學到的知識

- 所有 main.py 進入點都需要 _bootstrap()，不能漏掉 scheduler 路徑
- 冪等機制會掩蓋初始化 bug，測試時應刪除既有輸出再跑
- build.spec excludes 清單是防止被其他套件拖入依賴的雙重保險
- 移除 torch + sentence_transformers 可讓 exe 從 790 MB 降至 395 MB（減半）

## 決策記錄

| 決策 | 選項 | 最終選擇 | 理由 |
|------|------|---------|------|
| 在 main.py 進入點加 _bootstrap 而非 AutoScheduler 內部 | A: main.py 進入點 / B: AutoScheduler.__init__ | A | 與 MCP、CLI 模式進入點一致，職責清晰 |
| excludes 加入 torch/sentence_transformers/langchain_huggingface | 僅移除 hidden imports vs 同時加 excludes | 同時加 excludes | 雙重保險防止被其他套件（如 transformers）間接拖入 |
