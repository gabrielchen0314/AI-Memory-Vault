---
type: conversation-detail
date: 2026-04-10
session: vaultservice-refactor-tests
project: AI-Memory-Vault
org: gabrielchen0314
tags: [conversation, detail]
---

# 2026-04-10 vaultservice-refactor-tests — 詳細對話紀錄

## 對話概要
- **主題**：VaultService 拆分及測試修護

## 修改的檔案清單

| 檔案 | 操作 | 摘要 |
|------|------|------|
| `tests/conftest.py` | modified | 修復 scheduler 模組針對 VaultService 的 monkeypatch 實作 |
| `tests/test_rename_note.py` | modified | 修復 MCP tool 的直接抓取，修正 Error assertion mock 字串 |
| `tests/test_list_notes.py` | modified | 修復 MCP tool fn 抓取 |
| `tests/test_server_tools.py` | modified | 修復 check_index_status / reindex_vault MCP tool fn 抓取 |

## 執行的命令

| 命令 | 目的 | 結果 |
|------|------|------|
| `pytest tests/ -v` | 驗證全專案 152 個測試 | 100% 通過 |

## 遇到的問題與解決

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| 高達 40+ 的測試發生 ImportError 及 AttributeError | VaultService 分拆及 MCP 工具移入 tools 子目錄，導致舊測試繼續引用已不存在的 module scope 變數 | 更新測試目標路徑與 mcp._tool_manager 抽取邏輯 |

## 學到的知識

- FastMCP 工具不再 top-level export 後，單元測試需自 `mcp._tool_manager._tools[name].fn` 提取原始函式
- 當待測試檔案於函式內動態載入相依模組時，Monkeypatch 需要鎖定最原先宣告該相依的模組，而非呼叫點模組

## 決策記錄

| 決策 | 選項 | 最終選擇 | 理由 |
|------|------|---------|------|
| 解決 test_scheduler.py 中 VaultService mock 失敗問題 | ['直接覆寫 module 屬性', '用 sys.modules 動態篡改'] | 在 conftest.py 改變 monkeypatch 目標為 `services.vault.VaultService` | 由於 scheduler 在各函式內部動態載入（防禦性 imports），從 root import 進行 patch 可以同時覆蓋所有延遲載入的作用域 |
| 解決 MCP Tool 測試找不到 direct export 的問題 | ['修改 vault_tools 以提供全域方法', '使用 mcp 內部 registry 提取 fn 測試'] | 從 `mcp._tool_manager._tools['xxx'].fn` 中萃取函式進行測試 | 保持 tools module 現有的封裝乾淨度，並尊重 FastMCP 預設機制 |
