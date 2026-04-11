---
id: "post-write-hooks"
trigger: "post-write hooks 定義但未註冊"
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-10"
sequence: 3
---

# 問題：post-write hooks 定義但未註冊

## 動作
在 mcp_app/server.py 新增 _on_vault_write 並在 lifespan 註冊

## 證據
VaultService 有 hook 基礎建設但無實際 hook 被 register
