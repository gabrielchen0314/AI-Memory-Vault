---
type: rule
domain: coding
category: python-coding-style
workspace: _shared
applies_to: [python]
severity: must
created: 2026-03-31
last_updated: 2026-03-31
tags: [rule, python, naming, coding-style]
ai_summary: "Python 編碼規範：m_ 成員變數、i 參數、_ 區域變數、常數全大寫、類型前綴、禁止魔術數字、明確註解、PEP8 基本格式、類別/方法 docstring、區塊分區。"
---

# Python Coding Style — 共用規範

> 參考 C# / Lua 編碼規範，結合 PEP8 與團隊命名慣例，適用於所有 Python 專案。

---

## ⛔ 絕對禁止

| 禁止項目 | 原因 |
|----------|------|
| 魔術數字 | 降低可讀性，請改用常數或列舉 |
| 不明確命名 | 降低維護性 |
| 無註解/無 docstring | 降低可讀性 |
| 大量巢狀結構 | 降低可維護性 |

---

## 1. 命名規則

| 類型 | 前綴 | 範例 |
|------|------|------|
| 成員變數 | `m_` | `self.m_Counter`, `self.m_IsReady` |
| 參數 | `i` | `iUserId`, `iAmount` |
| 區域變數 | `_` | `_Result`, `_TempList` |
| 常數 | 全大寫 | `MAX_COUNT`, `DEFAULT_PATH` |
| 類型前綴 | `E`/`I` | `EState`, `IDataProvider` |
| 例外變數 | `_Ex` | `except Exception as _Ex` |

- 布林變數：用 is_/can_/has_ 開頭（如 `self.m_IsActive`）
- 集合：標示型別（如 `m_List_Items`, `m_Dic_Cache`）
- 類別/資料類型：以 Mgr/Data 結尾（如 `LoginMgr`, `UserData`）

---

## 2. 類別結構順序

```
常數定義 → 類別變數 → __init__ → 公開方法 → 私有方法 → 靜態方法
```
- 使用區塊註解（# region）分隔結構。

---

## 3. 格式規範

- 縮排：4 空格
- 每行 120 字以內
- 方法之間空一行
- 變數一行一個
- 遵循 PEP8 基本格式

---

## 4. 註解規範

### 類別

```python
"""
類別說明
@author gabrielchen
@version 1.0
@since [ProjectName] 版本
@date YYYY.MM.DD
"""
class MyClass:
    ...
```

### 方法

```python
    def do_something(self, iParam1):
        """
        方法說明
        :param iParam1: 參數1說明
        :return: 返回值說明
        """
        ...
```

### 成員變數

```python
    self.m_Counter = 0  # 計數器
```

---

## 5. 其他建議

- 盡量避免全域變數
- 善用型別註解（type hint）
- 例外處理時記錄詳細錯誤
- 測試程式可適度放寬命名規則

---

## 6. 範例

```python
"""
用戶管理器
@author gabrielchen
@version 1.0
@since ProjectX 1.0
@date 2026.03.31
"""
class UserMgr:
    # region 常數定義
    MAX_USERS = 1000
    # endregion

    def __init__(self):
        # region 成員變數
        self.m_List_Users = []  # 用戶清單
        self.m_IsInitialized = False  # 是否已初始化
        # endregion

    def add_user(self, iUserId: int) -> bool:
        """
        新增用戶
        :param iUserId: 用戶 ID
        :return: 是否成功
        """
        if len(self.m_List_Users) >= self.MAX_USERS:
            return False
        self.m_List_Users.append(iUserId)
        return True

    def _reset(self):
        """
        私有重設方法
        """
        self.m_List_Users.clear()
        self.m_IsInitialized = False
```
