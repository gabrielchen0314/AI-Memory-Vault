---
id: "mcp-server-dist-exe-certifi-mcp"
trigger: MCP Server 使用舊 dist exe（certifi 路徑不存在），導致 MCP 工具全部失敗
confidence: 0.6
domain: "ai-memory-vault"
source: "auto-learn:LIFEOFDEVELOPMENT/ai-memory-vault"
created: "2026-04-12"
sequence: 57
---

# 問題：MCP Server 使用舊 dist exe（certifi 路徑不存在），導致 MCP 工具全部

## 動作
mcp.json 切回 venv 版本並加入 dist 版本為注解備用

## 證據
mcp.json 切換至 dist exe 測試後未切回 venv
