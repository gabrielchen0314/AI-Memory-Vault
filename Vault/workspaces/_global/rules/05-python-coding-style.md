---
type: rule
domain: coding
category: python-coding-style
workspace: _global
applies_to: [python]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, python, naming, coding-style, type-hint, security]
ai_summary: "Python 編碼規範補充：snake_case 方法名、型別標注必填、括號內側空格、路徑穿越防護、dataclass 欄位語意、模組 docstring 格式。通用命名規則見 _global/rules/01-coding-style-universal.md。"
---

# Python Coding Style

> 本規範為 `workspaces/_global/rules/01-coding-style-universal.md` 的 Python 補充。  
> 通用命名（m_/i/_ 前綴、常數、布林、集合）請見全域規則。

---

## ⛔ Python 特定禁止

| 禁止項目 | 原因 |
|---------|------|
| 裸 `except:` | 必須是 `except Exception as _Ex:` |
| `self` 以外用途 | `self` 保留給 instance method 第一參數 |
| 在 `except` 中靜默吞掉錯誤 | 至少 return 錯誤訊息或 log |

---

## 1. 方法命名（Python 與 C#/Lua 的差異）

Python 方法使用 **snake_case**（與 C# PascalCase / Lua camelCase 不同）：

```python
# ✅ 正確
def sync_notes( self ) -> dict: ...
def read_note( self, iFilePath: str ) -> str: ...
def _validate_path( self, iPath: str ) -> bool: ...   # 私有方法加 _ 前綴

# ❌ 錯誤
def SyncNotes( self ): ...
def ReadNote( self, filePath ): ...
```

---

## 2. 類別結構順序

```
常數定義（class level）
→ 類別變數 / 靜態變數
→ __init__（成員變數初始化）
→ 私有方法（_ 前綴）
→ 公開方法
→ 靜態方法 / 類別方法
```

使用 `# region / # endregion` 分區：

```python
class VaultIndexer:

    # region 常數定義
    MAX_RETRIES: int = 3
    # endregion

    def __init__( self ):
        # region 成員變數
        self.m_IsInitialized: bool = False
        self.m_List_Chunks: list = []
        # endregion
```

---

## 3. 型別標注（公開方法必填）

```python
# ✅ 公開方法必填型別標注
def search( self, iQuery: str, iCategory: str = "" ) -> list[dict]:
    ...

# ✅ 私有方法建議填
def _build_filter( self, iCategory: str ) -> dict | None:
    ...
```

---

## 4. 格式規範（Python 特定）

```python
# ✅ 括號內側空格（與 C# 統一風格）
if( not _AbsPath.startswith( _VaultReal ) ):
    return "error"

with open( _AbsPath, "r", encoding="utf-8" ) as _File:
    return _File.read()

# ❌ Python 預設寫法（此專案不採用）
if not _AbsPath.startswith(_VaultReal):
    return "error"
```

---

## 5. 模組/類別文件字串格式

```python
"""
模組或類別說明（一行）。

詳細說明（可選）。

@author gabrielchen
@version 1.0
@since [ProjectName] 1.0
@date YYYY.MM.DD
"""
```

---

## 6. 安全規範（Python 路徑穿越防護）

```python
# ✅ 路徑穿越防護（必要）
_AbsPath = os.path.realpath( os.path.join( str( VAULT_ROOT ), iFilePath ) )
_VaultReal = os.path.realpath( str( VAULT_ROOT ) )
if not _AbsPath.startswith( _VaultReal ):
    return None, "Error: path traversal not allowed."

# ✅ 只允許 .md
if not _AbsPath.endswith( ".md" ):
    return None, "Error: only .md files are allowed."
```

---

## 7. Dataclass 語意設計原則

```python
# ❌ 錯誤：型別暗示限制
organization: str = ""       # 暗示只能屬於一個組織

# ✅ 正確：型別表達真實語意
organizations: list = field( default_factory=list )  # 可屬於多個組織
```

`field( default_factory=list )` 確保 mutable 預設值不在實例間共享。
