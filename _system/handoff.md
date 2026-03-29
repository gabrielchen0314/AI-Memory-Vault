---
type: system
domain: session-handoff
created: 2026-03-27
last_updated: 2026-03-30
ai_summary: "Session 交接檔：記錄上次 AI Session 的完成事項、待確認、延後項目和下一步。AI Session 啟動時的第 4 步必讀。"
---

# 🤝 Session Handoff

> **AI Session 啟動時的第 4 步必讀。**
> 每次 Session 結束前由 AI 更新，下次 Session 讀取。

---

## 📅 上次 Session

| 項目 | 內容 |
|------|------|
| **日期** | 2026-03-30 |
| **焦點** | 啟動穩定化 + 模式預檢系統 v1.2（env_setup.py 大幅擴充） |

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
