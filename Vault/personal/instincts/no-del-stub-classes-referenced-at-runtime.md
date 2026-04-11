---
id: "no-del-stub-classes-referenced-at-runtime"
trigger: 在 Python 模組中設定 stub/mock 物件後，考慮用 del 清理暫時變數時
confidence: 0.8
domain: python
source: "session-observation"
created: "2026-04-11"
sequence: 35
---

# 不要刪除運行時被引用的 stub 類別

## 動作
不要 del 被 __getattr__ 或其他運行時機制引用的類別。即使 stub setup 已完成，這些類別在模組的 __getattr__ 被呼叫時仍會被存取。改用下劃線前綴命名暗示私有即可。

## 正確模式
```python\n# ✅ 保留 stub 類別\ndel _types, _ModSpec, _TorchStub\n# _FakeDtype, _FakeTensor 不可 del\n\n# ❌ 錯誤\ndel _FakeDtype, _FakeTensor  # __getattr__ 運行時還需要\n```

## 證據
2026-04-11：main.py torch stub 中 del _FakeDtype 導致 frozen exe NameError，_TorchStub.__getattr__ 在模組屬性存取時仍需要 _FakeDtype 類別
