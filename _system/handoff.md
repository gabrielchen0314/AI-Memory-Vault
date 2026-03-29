---
type: system
domain: session-handoff
created: 2026-03-27
last_updated: 2026-03-29
ai_summary: "Session 交接檔：記錄上次 AI Session 的完成事項、待確認、延後項目和下一步。AI Session 啟動時的第 4 步必讀。"
---

# 🤝 Session Handoff

> **AI Session 啟動時的第 4 步必讀。**
> 每次 Session 結束前由 AI 更新，下次 Session 讀取。

---

## 📅 上次 Session

| 項目 | 內容 |
|------|------|
| **日期** | 2026-03-29（晚間）|
| **焦點** | v2.2 Messaging Gateway — LINE Bot 端到端串接 + Bot 回覆品質修正 + LLM 切換 |

---

## ✅ 本次完成

- [x] **Messaging Gateway v2.2**
  - `api/channels/base.py`：BaseChannel ABC（platform-agnostic）
  - `api/channels/line.py`：HMAC-SHA256 驗簽 + 訊息解析 + send_reply / send_ack / send_push
  - `api/chat_service.py`：ChatService（per-user 歷史 + 工具呼叫 + markdown 清除）
  - `api/app.py v2.2`：新增 `POST /webhook/line` 端點
- [x] **ngrok 3.37.3** 更新（ERR_NGROK_121 修正）
- [x] **LINE Webhook 驗證通過**（HMAC-SHA256 簽名正確）
- [x] **Bot 回覆品質修正**
  - `_strip_markdown()` + `_TOOL_LEAK_KEYWORDS` + `_LABEL_PATTERNS` regex
  - system prompt rules A-G + 1-10（繁中強制、禁 Markdown、禁自言自語）
- [x] **stop.ps1** 一鍵停止 port 8000/8001
- [x] **llm_factory.py 修正**：移除錯誤的 `stream=False`，補 `google_api_key`
- [x] **chat_service.py async 修正**：`_run_agent_turn` 改 `async def`，全用 `ainvoke`（避免阻塞 asyncio event loop）
- [x] **錯誤日誌修正**：`handle_message` 例外加 `logger.error`（之前靜默吞掉）
- [x] **PORT 衝突修正**：系統 Python 佔用 port 8000，統一改用 `venv/python main.py --mode api`
- [x] **LLM 切換評估**：Gemini 免費配額耗盡 → 目前使用 `llama3.1:8b`（Ollama 本地）

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
| FastAPI | v2.2，port 8000，用 `venv/python main.py --mode api` 啟動 |
| LLM | Ollama llama3.1:8b（Gemini 配額耗盡，待換新 key）|
| ngrok | 3.37.3，`ngrok http 8000` |
| LINE Webhook | 已驗證，URL 設定完成 |

---

## ➡️ 下一步建議

### 第四階段（剩餘）
1. **LINE Bot** — 串接已完成的 FastAPI，行動裝置存取 Vault
2. **雲端部署** — Railway / Render，多裝置共享記憶庫

---

## 🧠 學習紀錄

- `mcp[cli]` 需要 Python ≥3.10，3.9 無法安裝，需先升級 Python
- FastMCP `@mcp.tool()` 裝飾器用 docstring 作為 tool description，自動產生 inputSchema
- `.prompt.md` 可以作為 Agent 模板的「入口代理」——內容只寫「呼叫 read_note 載入真正的模板」，模板本身維護在 Vault，實現單一真相來源
- `Remove-Item .venv` 若 Python 程序仍在執行會出現 Access Denied，需先 Stop-Process
- FastMCP 官方 SDK 回傳的 `serverInfo.version` 是 SDK 版本（1.26.0），非自定義版本號

---

## ⚠️ AI 更新指引

Session 結束時：
1. 清空「本次完成」→ 寫入實際完成事項
2. 更新「需要確認」→ 移除已確認的
3. 更新「延後處理」
4. 更新「下一步建議」
5. 更新「學習紀錄」→ 列出新增的 Instinct
6. 更新 Frontmatter `last_updated`
7. 歸檔舊 handoff 到 `.ai_memory/logs/`

---

*最後更新：2026-03-29*

# 🤝 Session Handoff

> **AI Session 啟動時的第 4 步必讀。**
> 每次 Session 結束前由 AI 更新，下次 Session 讀取。

---

## 📅 上次 Session

| 項目 | 內容 |
|------|------|
| **日期** | 2026-03-28 |
| **焦點** | _AI_Engine v2.0 完整架構重建 |

---

## ✅ 本次完成

- [x] **v2.0 架構重建** — 單檔 400 行 → 13 模組化架構
  - `config.py` — Pydantic BaseSettings 全域設定
  - `core/embeddings.py` — 多語言向量模型 (multilingual-MiniLM-L12-v2)
  - `core/llm_factory.py` — LLM 工廠 (Ollama/Gemini 可插拔)
  - `core/vectorstore.py` — ChromaDB + RecordManager (langchain_chroma)
  - `core/indexer.py` — Frontmatter YAML 解析 → 切塊 → 標籤 → 增量同步
  - `core/retriever.py` — 語意搜尋 + 多維度 Metadata 過濾
  - `tools/` — sync/search/read/write 四工具薄封裝
  - `agents/base.py` — Agent ABC 介面
  - `agents/memory_agent.py` — 預設記憶 Agent
  - `agents/router.py` — @mention 路由器
  - `api/app.py` — FastAPI REST API (/health, /sync, /search)
  - `api/schemas.py` — Pydantic Request/Response
  - `cli/repl.py` — 互動終端（串流 + 工具呼叫）
  - `main.py` — 入口 (--mode cli | api, 自動處理 sys.path)
- [x] **向量庫完整重建** — 379 chunks, 28 files, 0 未分類
- [x] **技術債清理** — langchain_chroma、blake2b Hash、分類擴充
- [x] **文件同步** — ai-engine-progress.md + Roadmap + Repo Memory 全部更新

---

## 🔍 需要使用者確認

- [ ] **舊版清理**：`build_rag.py` 和 `agent_registry.py` 已被 v2.0 架構取代，是否刪除？
- [ ] **Ollama 模型**：是否已執行 `ollama pull llama3.2`？
- [ ] **第三階段優先順序**：專案索引 vs Hybrid Search vs 自動化排程，哪個先做？

---

## ⏳ 延後處理

| 項目 | 優先度 |
|------|:------:|
| 專案索引（.cs / .lua 語言感知切塊） | 🟠 高 |
| Hybrid Search（BM25 + Vector） | 🟠 高 |
| Windows Task Scheduler 自動同步 | 🟡 中 |
| 記憶分層（Recency Bias + Core Memory） | 🟡 中 |
| MCP Server（Copilot/Claude/Cursor 接入） | 🔵 低 |
| LINE Bot + REST API 串接 | 🔵 低 |

---

## ➡️ 下一步建議

### 第三階段（本週）
1. `.cs` / `.lua` 程式碼索引 — 語言感知切塊策略（RecursiveCharacterTextSplitter + Language）
2. Hybrid Search — BM25 + Vector + EnsembleRetriever
3. Windows Task Scheduler — 排程每日自動同步

### 第四階段（後續）
4. MCP Server — VS Code Copilot / Claude / Cursor 原生接入
5. LINE Bot — 串接已完成的 FastAPI

---

## 🧠 學習紀錄

- `llama3.2` 收到中文指令不一定會 tool call，必須用內建指令 `sync` 繞過
- ChromaDB `cleanup="incremental"` 靠 `source` key 追蹤，舊版無 source 記錄永遠無法自動清除
- `MarkdownHeaderTextSplitter` 切塊後 metadata 只有 Header 欄位，`source`/`category` 需手動注入
- `all-MiniLM-L6-v2` 是純英文模型，對繁體中文語意搜尋幾乎無效，必須用 `multilingual` 版本
- `langchain_community.vectorstores.Chroma` 已棄用，須改用 `langchain_chroma.Chroma`
- LangChain `index()` 的 `key_encoder` 預設 SHA-1，建議改用 `blake2b`
- YAML Frontmatter 中的 list（如 tags）不能直接存入 ChromaDB metadata，需轉為逗號分隔字串
- 背景終端的 cwd 總是工作區根目錄，`main.py` 需用 `sys.path.insert` + `os.chdir` 處理

---

## ⚠️ AI 更新指引

Session 結束時：
1. 清空「本次完成」→ 寫入實際完成事項
2. 更新「需要確認」→ 移除已確認的
3. 更新「延後處理」
4. 更新「下一步建議」
5. 更新「學習紀錄」→ 列出新增的 Instinct
6. 更新 Frontmatter `last_updated`
7. 歸檔舊 handoff 到 `.ai_memory/logs/`

---

*最後更新：2026-03-27*
