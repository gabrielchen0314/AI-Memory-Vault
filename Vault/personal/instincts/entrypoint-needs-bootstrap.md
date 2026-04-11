---
id: "entrypoint-needs-bootstrap"
trigger: 新增或修改 main.py 中的模式進入點（CLI/MCP/Scheduler/API），或發現 RuntimeError('record_manager 尚未初始化') 或嵌入模型未載入的錯誤
confidence: 0.8
domain: python
source: "session-observation"
created: "2026-04-11"
sequence: 52
---

# 所有 main.py 進入點都需要 _bootstrap()

## 動作
確認該進入點在建立 AutoScheduler/VaultService 等核心服務前，已呼叫 _bootstrap(_Config) 初始化 vectorstore/embeddings。不可依賴「其他模式會初始化」的假設。

## 正確模式
```python\n# 正確\ndef _start_scheduler_task(task_name):\n    _Config = ConfigManager.load()\n    _bootstrap(_Config)  # ← 必須有\n    _Sched = AutoScheduler(_Config)\n    _Sched.run_task(task_name)\n\n# 錯誤\ndef _start_scheduler_task(task_name):\n    _Config = ConfigManager.load()\n    _Sched = AutoScheduler(_Config)  # ← 缺少 _bootstrap\n    _Sched.run_task(task_name)  # → RuntimeError\n```

## 證據
2026-04-11: monthly-ai 在 frozen exe 中失敗（record_manager 尚未初始化），因 _start_scheduler_task() 未呼叫 _bootstrap()。weekly-ai 因冪等機制（檔案已存在、提前返回）僥倖成功，掩蓋了同樣的 bug。
