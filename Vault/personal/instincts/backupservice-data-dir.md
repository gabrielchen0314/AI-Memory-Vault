---
id: "backupservice-data-dir"
trigger: BackupService 測試 DATA_DIR 洩漏
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-10"
sequence: 2
---

# 問題：BackupService 測試 DATA_DIR 洩漏

## 動作
monkeypatch DatabaseConfig 實例的 get_chroma_path 方法

## 證據
get_chroma_path() 使用全域 DATA_DIR，不受 tmp_path 影響
