---
type: rule
domain: architecture
category: ai-engine-module-design
workspace: _global
applies_to: [python, langchain, fastapi, mcp]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
ai_summary: "AI Engine 四層架構規範：資料採集/記憶加工/邏輯大腦/接入介面、LangChain Tool 封裝模式、Agent ABC 設計、MCP Server stdout 防污染、設定管理。"
tags: [architecture, ai-engine, langchain, fastapi, mcp, rule]
---

# AI Engine 架構規範

---

## 四層架構強制邊界

```
Layer 1: 資料採集層  →  只負責掃描與讀取原始檔案
Layer 2: 記憶加工層  →  向量化、切塊、索引（不應有業務邏輯）
Layer 3: 邏輯大腦層  →  Agent、工具呼叫（不應直接操作 ChromaDB）
Layer 4: 接入介面層  →  CLI / FastAPI / MCP（不應包含業務邏輯）
```

| 違反案例 | 正確做法 |
|----------|----------|
| FastAPI `app.py` 直接呼叫 ChromaDB | 透過 `core/retriever.py` |
| `mcp_server.py` 包含搜尋邏輯 | 呼叫 `VaultRetriever().search_formatted()` |

---

## LangChain Tool 封裝規範

`tools/` 只做**薄封裝**，不含業務邏輯：

```python
# ✅ 正確
@tool
def search_notes( iQuery: str ) -> str:
    return VaultRetriever().search_formatted( iQuery )

# ❌ 錯誤：Tool 內直接操作 ChromaDB
@tool
def search_notes( iQuery: str ) -> str:
    _Client = chromadb.Client()
    ...
```

---

## MCP Server 規範

```python
# ✅ stdout 導向 stderr，防止污染 MCP 通道
with _StdoutToStderr():
    _Result = VaultRetriever().search_formatted( iQuery )

# ✅ write_note 後必須立即索引
_Stats = VaultIndexer().sync_single( _AbsPath )
```

---

## 設定管理規範

```python
# ✅ 透過 config.py（Pydantic BaseSettings）
from config import VAULT_ROOT, LLM_PROVIDER

# ❌ 禁止硬編碼路徑或直接 os.environ
VAULT_PATH = "D:/AI-Memory-Vault"
```

---

## 向量庫重建觸發條件

| 情況 | 指令 |
|------|------|
| 一般新增/修改 | `sync_vault()`（增量） |
| 模型替換 | ChromaDB 完整 cleanup + 重建 |
| 單一 write 後 | `VaultIndexer().sync_single( absPath )` |
