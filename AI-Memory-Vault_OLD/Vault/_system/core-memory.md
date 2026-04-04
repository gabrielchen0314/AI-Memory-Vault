---
type: core-memory
date: 2026.03.30
ai_summary: AI 每次對話開始時自動注入的核心事實，無需搜尋即可知悉的使用者關鍵背景。
---

# Core Memory — 核心記憶

> 此檔案在每次 AI 對話啟動時自動注入 System Prompt。
> 請保持條列簡潔，每條不超過一行。內容越精確，AI 表現越好。
> 更新此檔案後，AI 下次啟動即生效（不需重新 sync）。

---

## 使用者身份

- 姓名：gabrielchen
- 公司：LIFEOFDEVELOPMENT
- 聯絡：0917579661

## 主要專案

- **CHINESEGAMER**：Unity 手遊專案，C# 底層 + Lua 腳本，ECS 架構
- **AI Memory Vault**：Obsidian + RAG 個人第二大腦，Python 引擎 v2.3，LINE Bot 已串接，ngrok 自動啟動

## 技術偏好

- 架構：ECS 優先於傳統 OOP，模組化、低耦合、單一職責
- 語言：C#（底層邏輯）、Lua（上層腳本）、Python（工具/AI）
- Git：多 remote 策略，commit 格式遵循 Conventional Commits
- 命名：m_ 成員變數、i 參數、_ 區域變數（詳見 CHINESEGAMER 規範）

## 編碼規範快速參考

- 大括號：Allman style（獨立一行）
- 括號內側加空格：`if( condition )`
- 禁用：`var`（除匿名型別）、`goto`、魔術數字

## 目前重點（定期更新）

- v2.3 完成：模式預檢系統（套件/Ollama/ngrok）+ ngrok 自動啟動
- 待辦：Gemini API key 更換（新 project）、Telegram Channel、雲端部署
- 啟動方式：**必須用 venv Python**（`_AI_Engine\.venv\Scripts\python.exe main.py --mode api`）

## 重要決策記錄

- 2026.03.28：Embedding 改用 multilingual-MiniLM-L12-v2（多語言支援）
- 2026.03.29：Messaging Gateway v2.2，LINE Bot 端到端串接完成
- 2026.03.30：env_setup.py v1.2，三模式啟動預檢（套件/Ollama/ngrok 自動啟動）
- 2026.03.30：系統 Python 常佔 port 8000，統一用 venv python 啟動
