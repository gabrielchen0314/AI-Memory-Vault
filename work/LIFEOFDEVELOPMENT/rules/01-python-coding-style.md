---
type: rule
domain: coding
category: python-naming
workspace: LIFEOFDEVELOPMENT
applies_to: [python]
severity: must
source: CodingStyle.instructions.md
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "Python 命名規範：沿用與 C#/Lua 相同的前綴系統，適配 Python 語言慣例"
tags: [python, naming, coding-style, rule]
---

# Rule 01 — Python 命名規範

> **公司**：LIFEOFDEVELOPMENT  
> **適用**：所有 Python 程式碼（`_AI_Engine/` 及未來 Python 專案）

---

## ⛔ 絕對禁止

| 禁止項目 | 原因 |
|----------|------|
| 魔術數字 | 改用常數或 Enum |
| 裸 `except:` | 一律 `except Exception as _Ex:` |
| `self` 以外用途 | `self` 保留給 instance method 的第一參數 |
| 在 `except` 中靜默吞掉錯誤 | 至少 return 錯誤訊息或 log |

---

## 1. 命名前綴規則

與 C#/Lua 編碼規範保持一致：

| 類型 | 前綴 | Python 範例 |
|------|------|-------------|
| 成員變數（instance） | `m_` | `self.m_Counter`, `self.m_IsReady` |
| 參數 | `i` | `iFilePath`, `iQuery`, `iMode` |
| 區域變數 | `_` | `_Result`, `_AbsPath`, `_Dir` |
| 靜態/類別變數 | `s_`（可選） | `s_Instance` |
| 常數 | 全大寫 | `MAX_RETRIES`, `VAULT_ROOT` |
| 例外變數 | `_Ex` | `except Exception as _Ex:` |

```python
# ✅ 正確
class VaultIndexer:
    def sync( self, iForceRebuild: bool = False ) -> dict:
        _Stats = { "total_files": 0 }
        try:
            _Result = self._process()
        except Exception as _Ex:
            return { "error": str( _Ex ) }
        return _Stats

# ❌ 錯誤（無前綴，不符規範）
class vaultIndexer:
    def sync( self, force_rebuild = False ):
        stats = {}
        try:
            result = self._process()
        except:
            pass
```

### 布林前綴

```python
self.m_IsInitialized: bool = False
self.m_CanSync: bool = True
self.m_HasError: bool = False
```

### 集合命名

```python
self.m_List_Chunks: list = []
self.m_Dict_FileHash: dict = {}
```

---

## 2. 類別命名

| 類型 | 規則 | 範例 |
|------|------|------|
| 一般類別 | PascalCase | `VaultIndexer`, `MemoryAgent` |
| 管理器 | `Mgr` 後綴（可選） | `AgentRouter` |
| 資料類別 | `Data` 後綴（可選） | `SearchResultData` |
| 抽象基底類別 | `Base` 前綴或 ABC | `BaseAgent` |
| 例外類別 | `Error` / `Exception` 後綴 | `VaultPathError` |

---

## 3. 函式命名

Python 函式使用 **snake_case**（與 C# PascalCase 不同）：

```python
# ✅ 正確
def sync_notes( self ) -> dict: ...
def read_note( self, iFilePath: str ) -> str: ...
def _validate_path( self, iPath: str ) -> bool: ...   # 私有加 _

# ❌ 錯誤
def SyncNotes( self ): ...
def ReadNote( self, filePath ): ...
```

---

## 4. 模組結構規範

每個 Python 模組頂部必須有 docstring：

```python
"""
模組說明（一行）。
詳細說明（可選）。

@author gabrielchen
@version 1.0
@since {ProjectName} {版本}
@date YYYY.MM.DD
"""
```

### 類別結構順序

```
常數定義
→ 類別變數 / 靜態變數
→ __init__（成員變數初始化）
→ 私有方法（_ 前綴）
→ 公開方法
→ 靜態方法 / 類別方法
```

---

## 5. 型別標注

公開方法必須加型別標注，私有方法建議加：

```python
def search( self, iQuery: str, iCategory: str = "" ) -> list[dict]:
    ...

def _build_filter( self, iCategory: str ) -> dict | None:
    ...
```

---

## 6. 格式規範

- **縮排**：4 空格
- **括號內側**：加空格 → `func( arg1, arg2 )`
- **條件句**：`if( condition ):` 括號內側加空格

```python
# ✅ 正確
if( not _AbsPath.startswith( _VaultReal ) ):
    return "❌ 安全限制"

with open( _AbsPath, "r", encoding="utf-8" ) as _File:
    return _File.read()

# ❌ 錯誤
if not _AbsPath.startswith(_VaultReal):
    return "error"
```

---

## 7. 安全規範

```python
# ✅ 路徑穿越防護（必要）
_AbsPath = os.path.realpath( os.path.join( str( VAULT_ROOT ), iFilePath ) )
_VaultReal = os.path.realpath( str( VAULT_ROOT ) )
if not _AbsPath.startswith( _VaultReal ):
    return "❌ 安全限制：不允許讀取 Vault 目錄以外的檔案。"

# ✅ 只允許 .md（write_note）
if not _AbsPath.endswith( ".md" ):
    return "❌ 只允許寫入 .md 格式"
```
