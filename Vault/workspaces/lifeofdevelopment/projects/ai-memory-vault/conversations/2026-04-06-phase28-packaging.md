---
type: conversation
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
date: 2026-04-06
session: phase28-packaging
topics: [打包就緒, pyproject.toml, PyInstaller, 分發策略]
---

# 2026-04-06 — Phase 28 打包修復與分發策略

## 對話主題

1. 繼上次 pre-packaging audit，執行全部修復項目
2. 平台腳本保留原位的設計決策
3. 非技術人員分發方案評估（PyInstaller / Inno Setup / Tauri）

## 關鍵決策

### 1. pyproject.toml [project.scripts] 決定移除
- 問題：`vault = "main:main"` 要求 `main` 是已安裝 package 的模組路徑
- main.py 是腳本根目錄非 package，`pip install .` 後 console script 會 ModuleNotFoundError
- 決策：移除，目前啟動方式維持 `python main.py`

### 2. 平台腳本保留原位
- `.bat` 用 `%~dp0` 引用同目錄 → 移動到 `scripts/` 後 `.venv` 路徑計算會錯
- `.ps1` 用 `$ScriptDir` 同理
- `tasks.json` 是 `auto_tasks.ps1` 的資料庫，不能刪
- 決策：保留原位，透過 `[tool.setuptools.exclude-package-data]` 排除出 wheel

### 3. 分發架構分層
- **pip install**：只含 5 個 Python package（核心，跨平台）
- **git clone**：完整（含平台腳本，Windows only 的部分就是 Windows only）
- **排程**：跨平台用 APScheduler daemon；Windows 進階用 `.bat`

### 4. PyInstaller 優先於 Tauri
- Tauri 學習成本高（Rust + 重構整個 UI 層）
- PyInstaller 0.5 天完成，立即解決非技術人員使用門檻
- 時程：Phase 4 PyInstaller → Phase 5 Inno Setup → Phase 6 Tauri（長期）

## 修改的檔案

| 檔案 | 變更 |
|------|------|
| `AI_Engine/pyproject.toml` | dependencies 填入 20 項；移除 [project.scripts]；新增 [tool.setuptools] |
| `AI_Engine/tools/__init__.py` | 新建；匯出 TOOL_REGISTRY 三個符號 |
| `.gitignore` | 補 `AI_Engine/*.bak` 和 `.pytest_cache/` |
| `AI_Engine/docs/` | 空目錄移除 |
| `README.md` | Phase 3 標記完成；新增 Phase 4/5/6 說明（含工時評估） |
| Vault `status.md` | 待辦更新；Phase 28 工作脈絡 |

## 測試狀態
101/101 PASS（所有改動後驗證）
