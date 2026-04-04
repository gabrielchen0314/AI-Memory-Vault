---
type: system
domain: session-handoff
created: 2026-03-27
last_updated: 2026-03-31
ai_summary: "Session 交接檔：記錄上次 AI Session 的完成事項、待確認、延後項目和下一步。AI Session 啟動時的第 4 步必讀。"
---

# 🤝 Session Handoff

> **AI Session 啟動時的第 4 步必讀。**
> 每次 Session 結束前由 AI 更新，下次 Session 讀取。

---

## 📅 上次 Session

| 項目 | 內容 |
|------|------|
| **日期** | 2026-03-31 |
| **焦點** | VS Code 全域設定自動化（WorkspaceSetupService）+ MCP tool 擴充 |

---

## ✅ 本次完成

- [x] **WorkspaceSetupService 新建**（`services/workspace_setup.py`）
  - 偵測 VS Code 全域 prompts 目錄（跨平台：Windows / macOS / Linux，含 Insiders）
  - YAML frontmatter 解析：從 `mcp_tools` / `editor_tools` 動態產生工具清單，無 hardcode
  - 掃描 `work/*/rules/*.md` 產生 `vault-coding-rules.instructions.md`
  - **Ask_ 前置規則**：`editor_tools` 中無 `edit` 動作時，輸出 `.agent.md` 加 `Ask_` 前置
  - 冪等設計：目標檔案已存在則跳過，不覆蓋使用者手動修改
- [x] **mcp_server.py v2.1 → v2.2**
  - 新增第 5 個 MCP tool `setup_workspace()` — 可手動觸發 VS Code 設定同步
  - `run_mcp_server()` pre-warm 加入 `WorkspaceSetupService.setup()`（MCP 啟動時自動執行一次）
- [x] **templates/agents/*.md frontmatter 全部修正**（10 個檔案）
  - `mcp_tools` 改為正確名稱（search_vault / sync_vault / read_note / write_note）
  - 新增 `editor_tools: [read, edit, search, execute, todo]` 欄位

---

## 🔍 需要使用者確認

- [ ] **Gemini API key**：在 https://aistudio.google.com/apikey 新建 key（新 project，獨立配額）更新 `.env`
- [ ] **LINE Bot 品質測試**：llama3.1:8b 工具呼叫是否穩定？如不穩定考慮換回 Gemini
- [ ] **WorkspaceSetupService 首次執行測試**：MCP 啟動後確認 VS Code prompts 目錄是否正確建立 `.agent.md`

---

## ⏳ 延後處理

| 項目 | 優先度 |
|------|:------:|
| Gemini API key 更換（新 project 獲取獨立配額） | 🔴 緊急 |
| Telegram Channel (`api/channels/telegram.py`) | 🟠 高 |
| 雲端部署（多裝置共享） | 🟡 中 |

---

## 🔧 目前環境狀態

| 項目 | 值 |
|------|-----|
| FastAPI | v2.2，port 8000，啟動：`venv/python main.py --mode api` |
| MCP Server | v2.2，5 tools（search/sync/read/write/setup_workspace） |
| LLM | Ollama llama3.1:8b（Gemini 配額耗盡，待換新 key）|
| ngrok | 3.37.x，API 模式啟動時自動在背景啟動，Public URL 自動印出 |
| LINE Webhook | 已驗證，URL = ngrok Public URL + `/webhook/line` |
| 預檢系統 | v1.2：套件檢查 + Ollama 連線 + ngrok 自動啟動（三模式皆啟用）|
| WorkspaceSetupService | v1.0，MCP 啟動時自動執行，冪等寫入 VS Code prompts 目錄 |

---

## ➡️ 下一步建議

1. **Gemini API key** — 換新 project key，測試回應品質是否優於 llama3.1:8b
2. **WorkspaceSetupService 測試** — 啟動 MCP，確認 VS Code prompts 是否自動建立 agent 檔案
3. **LINE Bot 壓力測試** — 連續問答 5+ 輪，確認工具呼叫穩定性
4. **Telegram Channel** — `api/channels/telegram.py`（BaseChannel 子類別）

---

## 🧠 學習紀錄

- `start_api()` 裡同時 import `check_api_prerequisites` 舊名 + 呼叫 `check_mode_prerequisites` 新名，會造成 Pylance 未定義錯誤；需確保 import 名稱與呼叫名稱一致
- `editor_tools` 無 `edit` 動作的 Agent 應命名為 `Ask_{name}.agent.md`，避免 Copilot 自動執行破壞性操作

---

## ✅ 本次完成

- [x] **port 8000 衝突反覆修正**：系統 Python（非 venv）再次佔用 port，統一解法已確立（`Stop-Process` + venv python）
- [x] **ngrok 自動啟動**（`env_setup.py`）
  - 新增 `_launch_ngrok(iExe, iPort)`：先查 `localhost:4040/api/tunnels`，已在執行則印 URL，否則 `Popen` 啟動背景程序，等待 5 秒取得 Public URL 後印出
  - `_check_ngrok()` 改為：authtoken 已設定 → 直接呼叫 `_launch_ngrok()`（不再只是印提示訊息）
  - `check_api_prerequisites()` 傳入 `iPort` 參數
- [x] **模式預檢系統 v1.2**（`env_setup.py` + `main.py`）
  - 新增常數：`_BASE_PACKAGES`、`_LLM_PACKAGES`（gemini/ollama）、`_MODE_EXTRA_PACKAGES`（cli/api/mcp）
  - 新增 `check_mode_prerequisites(iMode, iPort)` — 統一 pre-flight 入口，依模式組合需要檢查的套件
  - 新增 `_check_packages(iPackages)` — 逐一 `importlib.util.find_spec` 檢查，缺少者詢問是否自動 `pip install`，安裝逐個回報成功/失敗
  - 新增 `_check_ollama_service(iBaseUrl)` — `GET /api/tags` 連線測試，失敗顯示安裝/啟動說明
  - `main.py` 三模式（cli / api / mcp）全部改為呼叫 `check_mode_prerequisites()`

---

## 🔍 需要使用者確認

- [ ] **Gemini API key**：在 https://aistudio.google.com/apikey 新建 key（新 project，獨立配額）更新 `.env`
- [ ] **LINE Bot 品質測試**：llama3.1:8b 工具呼叫是否穩定？如不穩定考慮換回 Gemini

---

## ⏳ 延後處理

| 項目 | 優先度 |
|------|:------:|
| Gemini API key 更換（新 project 獲取獨立配額） | 🔴 緊急 |
| Telegram Channel (`api/channels/telegram.py`) | 🟠 高 |
| 雲端部署（多裝置共享） | 🟡 中 |

---

## 🔧 目前環境狀態

| 項目 | 值 |
|------|-----|
| FastAPI | v2.2，port 8000，啟動：`venv/python main.py --mode api` |
| LLM | Ollama llama3.1:8b（Gemini 配額耗盡，待換新 key）|
| ngrok | 3.37.x，**API 模式啟動時自動在背景啟動**，Public URL 自動印出 |
| LINE Webhook | 已驗證，URL = ngrok Public URL + `/webhook/line` |
| 預檢系統 | v1.2：套件檢查 + Ollama 連線 + ngrok 自動啟動（三模式皆啟用）|

---

## ➡️ 下一步建議

1. **Gemini API key** — 換新 project key，測試回應品質是否優於 llama3.1:8b
2. **LINE Bot 壓力測試** — 連續問答 5+ 輪，確認工具呼叫穩定性
3. **Telegram Channel** — `api/channels/telegram.py`（BaseChannel 子類別）

---

## 🧠 學習紀錄

- `start_api()` 裡同時 import `check_api_prerequisites` 舊名 + 呼叫 `check_mode_prerequisites` 新名，會造成 Pylance 未定義錯誤；需確保 import 名稱與呼叫名稱一致
- `subprocess.CREATE_NEW_PROCESS_GROUP`（Windows）讓 ngrok 不受父程序 Ctrl+C 影響，獨立背景存活
- `importlib.util.find_spec(module_name)` 是最輕量的套件存在性檢查，不執行 import，不觸發初始化錯誤
- ngrok 啟動後 local API 需 ~0.5–1 秒才準備好，輪詢等待比 fixed sleep 可靠
- `Start-Process .\.venv\Scripts\python.exe main.py` 在背景執行時 terminal 的 cwd 不繼承，需明確指定 `-WorkingDirectory`

---

## ⚠️ AI 更新指引

Session 結束時：
1. 清空「本次完成」→ 寫入實際完成事項
2. 更新「需要確認」→ 移除已確認的
3. 更新「延後處理」
4. 更新「下一步建議」
5. 更新「學習紀錄」→ 列出新增的 Instinct
6. 更新 Frontmatter `last_updated`

---

*最後更新：2026-03-30*
