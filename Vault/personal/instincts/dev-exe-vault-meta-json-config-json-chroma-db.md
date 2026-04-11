---
id: "dev-exe-vault-meta-json-config-json-chroma-db"
trigger: dev 和 exe 的 vault_meta.json / config.json / chroma_db 不同步
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-11"
sequence: 22
---

# 問題：dev 和 exe 的 vault_meta.json / config.json / chroma

## 動作
統一 DATA_DIR 到 %APPDATA%\AI-Memory-Vault\

## 證據
DATA_DIR 分離：dev = AI_Engine/，frozen = %APPDATA%
