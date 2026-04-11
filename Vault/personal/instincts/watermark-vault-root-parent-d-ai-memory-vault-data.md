---
id: "watermark-vault-root-parent-d-ai-memory-vault-data"
trigger: "watermark 路徑存到 vault_root.parent（D:\AI-Memory-Vault）而非 DATA_DIR（%APPDATA%\AI-Memory-Vault）"
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-12"
sequence: 55
---

# 問題：watermark 路徑存到 vault_root.parent（D:\AI-Memory-Vaul

## 動作
修正為 DATA_DIR / watermark_filename，確保放在可寫資料目錄

## 證據
設計時混淆了 vault_root（D 槽）與 DATA_DIR（AppData）兩個路徑概念
