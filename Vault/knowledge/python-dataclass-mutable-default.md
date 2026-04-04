---
type: knowledge
tags: [python, dataclass, mutable-default, architecture]
created: 2026-04-04
---

# Python Dataclass 可變預設值 與 欄位語意設計

## 可變預設值

```python
# ❌ 錯誤：所有實例共享同一 list
@dataclass
class Config:
    items: list = []

# ✅ 正確：每個實例獨立 list
from dataclasses import dataclass, field

@dataclass
class Config:
    items: list = field( default_factory=list )
```

## 欄位語意設計

欄位型別必須反映真實語意：

- `organization: str` → 隱含「只能屬於一個組織」
- `organizations: list` → 正確表達「可屬於多個組織」

型別選擇不只是技術問題，是**領域建模**的決定。錯誤的型別會讓所有下游程式碼（UI、序列化、驗證）都走歪。

## 向後相容 Migration

改欄位名時在 `load()` 加 migration shim：

```python
_Raw = dict( data.get("user", {}) )
if "organization" in _Raw and "organizations" not in _Raw:
    _Old = _Raw.pop("organization")
    _Raw["organizations"] = [_Old] if _Old else []
```
