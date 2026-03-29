---
type: rule
domain: architecture
category: ai-engine-module-design
workspace: LIFEOFDEVELOPMENT
applies_to: [python, langchain, fastapi, mcp]
severity: must
source: _AI_Engine/ v2.0
created: 2026.03.29
last_updated: 2026.03.29
ai_summary: "_AI_Engine v2.0 的模組責任邊界、四層架構規範、LangChain Tool 封裝模式、Agent ABC 設計"
tags: [architecture, ai-engine, langchain, fastapi, mcp, rule]
---

# Rule 02 — AI Engine 架構規範

> **公司**：LIFEOFDEVELOPMENT  
> **適用**：`_AI_Engine/` 及所有以四層 RAG 架構為基礎的 Python AI 專案

---

## 1. 四層架構強制邊界

```
Layer 1: 資料採集層  →  只負責掃描與讀取原始檔案
Layer 2: 記憶加工層  →  向量化、切塊、索引、過濾（不應有業務邏輯）
Layer 3: 邏輯大腦層  →  Agent、工具呼叫、對話上下文（不應直接操作 ChromaDB）
Layer 4: 接入介面層  →  CLI / FastAPI / MCP（不應包含任何業務邏輯）
```

| 違反案例 | 正確做法 |
|----------|----------|
| FastAPI `app.py` 直接呼叫 ChromaDB | 透過 `core/retriever.py` |
| `repl.py` 直接操作 `VaultIndexer` | 透過 `tools/sync.py` |
| `mcp_server.py` 包含搜尋邏輯 | 呼叫 `VaultRetriever().search_formatted()` |

---

## 2. Core 層模組責任

| 模組 | 檔案 | 責任 | 禁止 |
|------|------|------|------|
| `embeddings.py` | `core/embeddings.py` | 初始化多語言向量模型 | 不含索引邏輯 |
| `vectorstore.py` | `core/vectorstore.py` | ChromaDB + RecordManager 初始化 | 不含掃描邏輯 |
| `indexer.py` | `core/indexer.py` | 掃描 → Frontmatter 解析 → 切塊 → 增量同步 | 不含查詢邏輯 |
| `retriever.py` | `core/retriever.py` | Hybrid Search + Metadata 過濾 + Recency Bias | 不含寫入邏輯 |
| `llm_factory.py` | `core/llm_factory.py` | LLM 可插拔初始化（Gemini / Ollama） | 不含 Agent 邏輯 |

---

## 3. LangChain Tool 封裝規範

`tools/` 只做**薄封裝**，不含業務邏輯：

```python
# ✅ 正確：Tool 只是橋接，核心邏輯在 core/
@tool
def search_notes( iQuery: str ) -> str:
    """..."""
    _Retriever = VaultRetriever()
    return _Retriever.search_formatted( iQuery )

# ❌ 錯誤：Tool 內含業務邏輯
@tool
def search_notes( iQuery: str ) -> str:
    _Client = chromadb.Client()                  # 直接操作 ChromaDB
    _Results = _Client.get_collection("vault")   # 不透過 core/
    ...
```

---

## 4. Agent ABC 設計規範

```python
# ✅ 必要結構
class BaseAgent( ABC ):
    @abstractmethod
    def run( self, iInput: str ) -> str: ...

class MemoryAgent( BaseAgent ):
    def __init__( self ):
        self.m_Tools   = [sync_notes, search_notes, read_note, write_note]
        self.m_History = ChatHistory()
    
    def run( self, iInput: str ) -> str: ...
```

- **新 Agent 必須繼承 `BaseAgent`**
- **工具集在 `__init__` 中宣告**，不在 `run()` 中動態建立
- **ChatHistory 在 Agent 內管理**，不在外部傳入

---

## 5. MCP Server 規範

```python
# ✅ 正確：工具執行時把 stdout 導向 stderr，防止污染 MCP 通道
with _StdoutToStderr():
    from core.retriever import VaultRetriever
    _Result = VaultRetriever().search_formatted( iQuery )

# ✅ write_note 後必須立即索引（sync_single）
_Stats = VaultIndexer().sync_single( _AbsPath )
```

- MCP Tools 命名：`search_vault` / `sync_vault` / `read_note` / `write_note`
- 啟動方式：`python main.py --mode mcp`（不直接執行 `mcp_server.py`）

---

## 6. 設定管理規範

```python
# ✅ 所有設定透過 Pydantic BaseSettings（config.py）
from config import VAULT_ROOT, USE_HYBRID_SEARCH, LLM_PROVIDER

# ❌ 禁止硬編碼路徑或直接讀取 os.environ
VAULT_PATH = "D:/AI-Memory-Vault"   # ❌
LLM = os.environ.get("LLM")         # ❌（改用 config.py 的 BaseSettings）
```

---

## 7. 安全規範

所有接受 `file_path` 的函式都必須套用路徑穿越防護：

```python
_AbsPath  = os.path.realpath( os.path.join( str( VAULT_ROOT ), iFilePath ) )
_VaultReal = os.path.realpath( str( VAULT_ROOT ) )
if not _AbsPath.startswith( _VaultReal ):
    return "Error: path traversal not allowed."
```

---

## 8. 向量庫重建觸發條件

| 情況 | 指令 |
|------|------|
| 一般新增/修改文件 | `sync_vault()`（增量，只處理變動） |
| 模型替換 / 大規模路徑變更 | ChromaDB 完整 cleanup + 重建 |
| 單一檔案 write 後立即索引 | `VaultIndexer().sync_single( absPath )` |
