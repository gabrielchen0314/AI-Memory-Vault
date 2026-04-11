# Core 層 API Map

> **目錄**：`core/`
> **用途**：基礎設施層 — 嵌入模型、向量資料庫、文件索引、搜尋引擎、日誌、遷移
> **最後更新**：2026.04.10

---

## 1. 模組概覽

| 模組 | 檔案 | 職責 | 對外方法數 |
|------|------|------|-----------|
| embeddings | `core/embeddings.py` | HuggingFace 嵌入模型單例 | 2 |
| errors | `core/errors.py` | VaultError 例外階層 | 7 types |
| frontmatter | `core/frontmatter.py` | YAML Frontmatter 解析/渲染 | 3 |
| indexer | `core/indexer.py` | .md → ChromaDB 增量同步 | 4 |
| logger | `core/logger.py` | vault.* 命名空間日誌 | 2 |
| migration | `core/migration.py` | 索引設定遷移管理 | 3 |
| retriever | `core/retriever.py` | 語意搜尋（Hybrid BM25+Vector） | 3 |
| vectorstore | `core/vectorstore.py` | ChromaDB + RecordManager 單例 | 3 |

### 架構說明

Core 層提供所有模組共用的基礎設施，**不依賴 Service 層**。依賴方向：

```
Service 層 → Core 層 → 外部套件（langchain, chromadb, sentence-transformers）
```

---

## 2. core/embeddings — 嵌入模型

> 管理多語言向量嵌入模型的單例載入

**相依性**：`functools`, `langchain_huggingface`

| 函式 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `initialize(iModelName)` | `str` — 模型名稱 | `None` | 設定模型（須在首次 `get_embeddings` 前呼叫） |
| `get_embeddings()` | — | `HuggingFaceEmbeddings` | 取得嵌入模型單例（`lru_cache`） |

**注意**：
- `initialize` 必須先於 `get_embeddings` 呼叫，否則使用預設模型
- 模型切換需清除 `lru_cache`（通常只在 migration 時發生）
- **Lazy Import**：`langchain_huggingface` 在函式內 import，避免啟動時載入 torch

---

## 3. core/errors — 例外階層

> 定義 VaultError 基礎例外與所有衍生錯誤類型

```
VaultError (VAULT_ERROR)
├── PathTraversalError   (PATH_TRAVERSAL)     路徑遍歷攻擊
├── FileNotFoundError_   (NOT_FOUND)          檔案不存在
├── ExtensionError       (EXTENSION)          不允許的副檔名
├── NotInitializedError  (NOT_INITIALIZED)    服務未初始化
├── TodoNotFoundError    (TODO_NOT_FOUND)     找不到 Todo 項目
├── NoteAlreadyExistsError (ALREADY_EXISTS)   目標路徑已有檔案
└── EditMatchError       (EDIT_NO_MATCH /     edit_note 文字比對失敗
                          EDIT_MULTI_MATCH)
```

每個例外類別都有 `code: str` 屬性，MCP 工具層用此識別錯誤類型並回傳對應訊息。

---

## 4. core/frontmatter — Frontmatter 解析

> 統一 YAML Frontmatter 解析與渲染

**相依性**：`re`, `yaml`, `core.logger`

| 函式 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `parse(iContent)` | `str` — raw markdown | `tuple[dict, str]` | 解析 YAML frontmatter → (metadata, body) |
| `render(iMeta)` | `dict` — metadata | `str` | 渲染 frontmatter 字串（含 `---` 標記） |
| `has_field(iContent, iField, iValue="")` | content, field, value | `bool` | 快速檢查是否含指定欄位 |

---

## 5. core/indexer — VaultIndexer

> Vault .md 掃描 → Frontmatter 解析 → Markdown 切塊 → ChromaDB 增量同步

**相依性**：`config (CATEGORY_MAP, EXCLUDE_DIRS, FRONTMATTER_FIELDS)`, `core.vectorstore`, `core.logger`, `langchain_community`, `langchain_text_splitters`

**常數**：`HEADERS_TO_SPLIT: list[tuple]` — Markdown 標題切塊設定（`#`, `##`, `###`）

### VaultIndexer

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `__init__(iVaultRoot, iChunkSize=500, iChunkOverlap=50)` | vault 路徑, chunk 設定 | — | 建立索引器 |
| `sync()` | — | `dict` | 全量增量同步（cleanup=`"full"`） |
| `sync_single(iAbsPath)` | `str` — 絕對路徑 | `dict` | 單一檔案增量索引（cleanup=`"incremental"`） |
| `delete_source(iAbsPath)` | `str` — 絕對路徑 | `dict` | 移除指定 source 的向量記錄 |
| `sync_batch(iAbsPaths)` | `list[str]` — 路徑 list | `dict` | 批次增量索引 |

**回傳 dict 結構**：
```python
{
    "index_stats": {...},        # langchain index 統計
    "category_summary": {...},   # 分類計數
    "type_summary": {...},       # 文件類型計數
    "total_chunks": int,         # 總 chunk 數
    "total_files": int           # 總檔案數
}
```

---

## 6. core/logger — 日誌模組

> 統一日誌取得介面，所有模組使用 `vault.*` 命名空間

**相依性**：`logging`

| 函式 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `configure(iLevel=INFO, iLogFile="")` | level, log file | `None` | 設定全域 handler（僅首次生效） |
| `get_logger(iName)` | `str` — 模組名稱 | `logging.Logger` | 取得 `vault.{name}` 子 logger |

**使用範例**：
```python
from core.logger import get_logger
log = get_logger("vault_service")  # → vault.vault_service
```

---

## 7. core/migration — MigrationManager

> 偵測索引設定變更（模型、chunk_size 等），需要時觸發完整重建

**相依性**：`config (AppConfig, DATA_DIR, CATEGORY_MAP, FRONTMATTER_FIELDS)`, `hashlib`, `json`, `shutil`, `pathlib`

**管理檔案**：`DATA_DIR / "vault_meta.json"` — 儲存上次索引時的設定快照

### MigrationManager（靜態方法）

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `check(iConfig)` | AppConfig | `tuple[bool, list[tuple[str, Any, Any]]]` | 比較設定與 meta → (needs_reindex, changes) |
| `reset_index(iConfig)` | AppConfig | `tuple[bool, str]` | 清除 ChromaDB + RecordManager + 更新 meta |
| `describe_changes(iChanges)` | changes list | `str` | 變更轉為人類可讀說明 |

---

## 8. core/retriever — VaultRetriever

> 封裝語意搜尋，支援三種模式：Pure Vector / Hybrid BM25+Vector / Recency Bias

**相依性**：`config (AppConfig, CATEGORY_UNKNOWN)`, `core.vectorstore`, `langchain_core`, `langchain_community.retrievers`, `langchain_classic.retrievers.ensemble`

### VaultRetriever

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `__init__(iConfig)` | AppConfig | — | 以設定建立檢索器 |
| `invalidate_bm25_cache()` | — | `None` | 使 BM25 語料快取失效（sync/write/delete 後必須呼叫） |
| `search(iQuery, iCategory="", iDocType="", iTopK=None, iMode="")` | 查詢, 過濾器, 模式 | `list[dict]` | 執行搜尋 |
| `search_formatted(iQuery, iCategory="", iDocType="", iMode="")` | 查詢, 過濾器, 模式 | `str` | 搜尋→格式化文字結果 |

**search 回傳結構**：
```python
[{
    "content": str,      # 文件內容
    "source": str,       # 相對路徑
    "category": str,     # 分類標籤
    "doc_type": str,     # 文件類型（frontmatter type）
    "domain": str,       # 領域
    "tags": list,        # 標籤
    "ai_summary": str    # AI 摘要
}]
```

**搜尋模式（iMode）**：

| 值 | 說明 |
|----|------|
| `""` (預設) | 依 SearchConfig 設定的混合權重 |
| `"keyword"` | 偏重 BM25（keyword_bm25_weight） |
| `"semantic"` | 偏重向量（semantic_bm25_weight） |

---

## 9. core/vectorstore — ChromaDB 管理

> ChromaDB 連線 + SQLRecordManager 增量追蹤的單例管理

**相依性**：`functools`, `langchain_chroma`, `langchain_community.indexes`, `core.embeddings`

| 函式 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `initialize(iChromaDir, iRecordDbUrl, iCollectionName="vault_main")` | 路徑設定 | `None` | 注入路徑（清除 lru_cache） |
| `get_vectorstore()` | — | `Chroma` | ChromaDB 實例（lru_cache 單例） |
| `get_record_manager()` | — | `SQLRecordManager` | RecordManager 實例（lru_cache 單例） |

**注意**：
- `initialize` 清除快取後，下次 `get_*` 呼叫會重新建立連線
- RecordManager 用於追蹤哪些文件已索引（增量同步的基礎）
- ChromaDB 資料目錄 = `DatabaseConfig.get_chroma_path()`

---

## 10. 設計注意事項

### 10.1 Lazy Import 原則

所有 ML/DL 相關依賴（torch, transformers, langchain_community, langchain_huggingface）必須在**函式內** import，避免 CLI/MCP 啟動時載入數秒。

### 10.2 BM25 快取一致性

`VaultRetriever` 的 BM25 語料在首次搜尋時快取。任何 write/delete/sync 操作後，必須呼叫 `invalidate_bm25_cache()` 使快取失效。VaultService 已在內部自動處理此邏輯。

### 10.3 lru_cache 單例模式

`embeddings.get_embeddings()` 和 `vectorstore.get_*()` 使用 `@lru_cache` 實現單例。初始化時呼叫 `initialize()` 設定參數並清除快取。不可直接呼叫 `cache_clear()`。
