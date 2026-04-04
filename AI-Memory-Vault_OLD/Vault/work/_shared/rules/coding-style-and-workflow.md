---
type: rule
category: coding-style-and-workflow
workspace: _shared
applies_to: [all-languages, all-projects]
severity: must
created: 2026-03-31
last_updated: 2026-03-31
tags: [rule, coding-style, workflow, security, git, api-map, architecture]
ai_summary: "全語言共用編碼規範、命名規則、Git 工作流、安全、API Map、架構原則，所有專案皆須遵守，語言/領域補充請見各自 rules。"
---

# 共用 Coding Style & Workflow

> 本規範為所有專案、所有語言必須遵守的基礎規則。語言/領域專屬補充請見 work/_shared/rules/ 及各公司 rules/。

---

## 1. 命名規則（全語言共通）

| 類型 | 前綴 | 範例 |
|------|------|------|
| 成員變數 | `m_` | `m_Counter`, `m_IsReady` |
| 參數 | `i` | `iUserId`, `iAmount` |
| 區域變數 | `_` | `_Result`, `_TempList` |
| 靜態變數 | `s_`（可選） | `s_Instance` |
| 常數 | 全大寫 | `MAX_COUNT`, `DEFAULT_PATH` |
| 列舉/型別 | `E`/`I` | `EState`, `IDataProvider` |
| 例外變數 | `_Ex` | `except Exception as _Ex`/`catch (Exception _Ex)` |

- 布林變數：is_/can_/has_ 開頭（如 `m_IsActive`）
- 集合：標示型別（如 `m_List_Items`, `m_Dic_Cache`）
- 管理器/資料類型：Mgr/Data 結尾

---

## 2. 結構順序與格式

- 常數 → 靜態變數 → 成員變數 → 屬性/組件 → 初始化/建構 → 公開方法 → 私有方法 → 事件處理
- 使用區塊註解（# region / #endregion / region/endregion）分隔
- 每行 120 字以內，方法間空一行，變數一行一個
- 禁止魔術數字，請用常數/Enum

---

## 3. 註解規範

- 類別/模組需有作者、版本、日期、說明
- 公開方法/函式需有參數、回傳值說明
- 成員變數需有用途註解
- 例外處理必須記錄錯誤

---

## 4. Git Workflow & Commit

- Commit message 必須有 type 前綴（feat/fix/refactor/docs...）
- 多專案需同步依賴順序與批次操作
- Commit message 格式、scope、原子性請見 work/_shared/rules/git-conventions.md

---

## 5. 安全與敏感資訊

- 禁止硬編碼密鑰、密碼、Token
- 敏感資訊請用設定檔/環境變數
- Log 不得洩漏敏感資訊
- Client 永遠不可信，重要邏輯需 Server 驗證

---

## 6. API Map 與知識同步

- 程式專案必須建立 API_MAP.md 並與 Vault 雙向同步
- 詳細規則請見 work/_shared/rules/project-api-map-sync.md

---

## 7. 架構原則

- 嚴格分層，禁止跨層操作
- 各層責任明確，請見 work/_shared/rules/ai-engine-architecture.md

---

## 8. 語言/領域專屬補充

- C#：work/CHINESEGAMER/rules/01-csharp-coding-style.md
- Lua：work/CHINESEGAMER/rules/02-lua-coding-style.md
- Python：work/_shared/rules/python-coding-style.md
- VSCode Extension/AI Engine/安全/Tag/UI 綁定等，請見 work/_shared/rules/ 及各公司 rules/

---

> 本規範如有疑義，以 _shared/rules/ 及各專案 rules/ 最新內容為準。
