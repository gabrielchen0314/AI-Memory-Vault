---
id: "idempotent-hides-bugs"
trigger: 測試冪等功能（如排程任務、報表生成）時，看到成功結果但懷疑可能未走完整執行路徑
confidence: 0.7
domain: debugging
source: "session-observation"
created: "2026-04-11"
sequence: 53
---

# 冪等機制會掩蓋初始化 bug — 測試時先刪除輸出

## 動作
測試有寫入副作用的功能時，先刪除既有輸出檔案，強制觸發完整寫入路徑。不可只依賴「產出正確」來判斷通過。

## 正確模式
```bash\n# 正確：先刪除再測試\nRemove-Item *.md -Force\nvault-cli.exe --once --headless --task monthly-ai\n# 確認新檔案被建立\n\n# 錯誤：直接跑，看到 OK 就以為沒問題\nvault-cli.exe --once --headless --task monthly-ai\n# ✅ 可能只是冪等提前返回\n```

## 證據
2026-04-11: weekly-ai 在 frozen exe 中成功，因 2026-W15.md 已存在（冪等提前返回），完全沒觸發 vectorstore 寫入路徑。monthly-ai 因不存在而觸發寫入，才暴露 _bootstrap 缺失的 bug。
