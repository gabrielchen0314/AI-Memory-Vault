# Config 層 API Map

> **檔案**：`config.py`
> **用途**：應用程式設定集中管理，含 config.json 讀寫與資料結構定義
> **最後更新**：2026.04.10

---

## 1. 模組概覽

| 屬性 | 值 |
|------|-----|
| **模組名稱** | `config` |
| **檔案路徑** | `config.py` |
| **用途** | 統一設定管理（config.json + dataclass 結構 + 路徑常數） |
| **設計模式** | Static ConfigManager + Dataclass 嵌套 |
| **語言** | Python 3.12 |

### 1.1 架構說明

config.py 是整個系統的設定核心，負責：
- 定義 `ENGINE_DIR` / `DATA_DIR` 等路徑常數（區分 frozen/dev/Docker 環境）
- 以 `@dataclass` 嵌套結構描述所有設定項
- `ConfigManager` 靜態方法讀寫 config.json
- `VaultPaths` 統一所有 Vault 目錄路徑的生成邏輯

---

## 2. 路徑常數

| 常數 | 型別 | 說明 |
|------|------|------|
| `ENGINE_DIR` | `Path` | 程式所在目錄（frozen = exe 旁；dev = AI_Engine/） |
| `DATA_DIR` | `Path` | 可寫資料目錄（frozen = %APPDATA%；dev = ENGINE_DIR；Docker = `VAULT_DATA_DIR` 環境變數） |
| `PROJECT_ROOT` | `Path` | ENGINE_DIR.parent |
| `CONFIG_FILE` | `Path` | DATA_DIR / "config.json" |
| `__version__` | `str` | `"3.6.0"` |

### 2.1 索引設定常數

| 常數 | 型別 | 說明 |
|------|------|------|
| `CATEGORY_MAP` | `dict` | 路徑前綴 → emoji 分類標籤對照 |
| `CATEGORY_UNKNOWN` | `str` | `"📁 未分類"` |
| `EXCLUDE_DIRS` | `set` | 索引排除目錄（`.venv`, `chroma_db` 等） |
| `FRONTMATTER_FIELDS` | `list` | Frontmatter 提取欄位清單 |

---

## 3. 資料結構 — Dataclass 設定樹

```
AppConfig
├── version: str
├── vault_path: str
├── vscode_user_path: str
├── paths: VaultPaths
├── user: UserConfig        (name, organizations, email)
├── llm: LLMConfig          (provider, model, api_key_env, ollama_base_url)
├── embedding: EmbeddingConfig  (model, device, chunk_size, chunk_overlap)
├── search: SearchConfig    (top_k, use_hybrid, bm25_weight, vector_weight, ...)
├── database: DatabaseConfig (chroma_dir, record_db, collection_name)
├── api: APIConfig          (host, port)
└── git: GitConfig          (auto_commit, author_name, author_email)
```

### 3.1 UserConfig

| 欄位 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `name` | `str` | `""` | 使用者名稱（用於 @author） |
| `organizations` | `list` | `[]` | 所屬組織清單 |
| `email` | `str` | `""` | 電子信箱 |

### 3.2 LLMConfig

| 欄位 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `provider` | `str` | `""` | LLM 供應商 |
| `model` | `str` | `""` | 模型名稱 |
| `api_key_env` | `str` | `""` | API Key 環境變數名 |
| `ollama_base_url` | `str` | `""` | Ollama 連線 URL |

### 3.3 EmbeddingConfig

| 欄位 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `model` | `str` | `"..."` | 嵌入模型名稱 |
| `device` | `str` | `"cpu"` | 運算裝置 |
| `chunk_size` | `int` | `500` | 文字切塊大小 |
| `chunk_overlap` | `int` | `50` | 切塊重疊量 |

### 3.4 SearchConfig

| 欄位 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `top_k` | `int` | `10` | 搜尋結果數上限 |
| `use_hybrid` | `bool` | `True` | 啟用混合搜尋 |
| `bm25_weight` | `float` | — | BM25 權重（一般模式） |
| `vector_weight` | `float` | — | 向量權重（一般模式） |
| `keyword_bm25_weight` | `float` | — | 關鍵字模式 BM25 權重 |
| `semantic_bm25_weight` | `float` | — | 語意模式 BM25 權重 |
| `recency_bias_enabled` | `bool` | `False` | 啟用時間衰減 |
| `recency_decay_days` | `int` | `30` | 衰減天數 |

### 3.5 DatabaseConfig

| 欄位 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `chroma_dir` | `str` | `"chroma_db"` | ChromaDB 目錄 |
| `record_db` | `str` | `"record_manager_cache.sql"` | RecordManager 資料庫 |
| `collection_name` | `str` | `"vault_main"` | 向量集合名稱 |

#### 方法

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `get_chroma_path()` | — | `str` | 取得 ChromaDB 絕對路徑 |
| `get_record_db_url()` | — | `str` | 取得 RecordManager SQLite URL |

### 3.6 APIConfig

| 欄位 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `host` | `str` | `"localhost"` | API 伺服器地址 |
| `port` | `int` | `8765` | API 伺服器埠 |

### 3.7 GitConfig

| 欄位 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `auto_commit` | `bool` | `False` | 自動 git commit |
| `author_name` | `str` | `"AI Memory Vault"` | 提交者名稱 |
| `author_email` | `str` | `"vault@localhost"` | 提交者信箱 |

---

## 4. VaultPaths — 目錄路徑對照

> 統一所有 Vault 目錄路徑的生成邏輯，避免硬編碼路徑字串散落各處。

### 4.1 靜態路徑欄位（約 40 個）

包含 `_config`, `knowledge`, `personal`, `templates`, `attachments`, `workspaces`, `_global_rules`, `_global_skills`, 以及所有 personal 子目錄路徑。

### 4.2 動態方法

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `org_dir(iOrg)` | org 名稱 | `str` | 組織根目錄 |
| `org_rules_dir(iOrg)` | org 名稱 | `str` | 組織規則目錄 |
| `org_projects_dir(iOrg)` | org 名稱 | `str` | 組織專案根目錄 |
| `project_dir(iOrg, iProject)` | org, project | `str` | 專案根目錄 |
| `project_daily_dir(iOrg, iProject)` | org, project | `str` | 專案每日進度目錄 |
| `project_notes_dir(iOrg, iProject)` | org, project | `str` | 專案筆記目錄 |
| `project_meetings_dir(iOrg, iProject)` | org, project | `str` | 專案會議目錄 |
| `project_conversations_dir(iOrg, iProject)` | org, project | `str` | AI 對話目錄 |
| `project_status_file(iOrg, iProject)` | org, project | `str` | 專案 status.md 路徑 |
| `get_all_dirs()` | — | `list[str]` | 初始化所需全部目錄 |
| `get_project_skeleton_dirs()` | — | `list[str]` | 新專案骨架子目錄 |
| `get_initial_files()` | — | `dict` | 初始化檔案→生成函式對照 |
| `parse_project_path(iRelPath)` | rel path | `tuple[str\|None, str\|None]` | 從路徑解析 org/project |

---

## 5. ConfigManager（靜態方法）

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `is_initialized()` | — | `bool` | config.json 是否存在 |
| `load()` | — | `AppConfig` | 載入設定（含 .env 覆蓋） |
| `save(iConfig)` | AppConfig | `None` | 寫入 config.json |

---

## 6. 使用範例

### 6.1 載入設定

```python
from config import ConfigManager

config = ConfigManager.load()
print(config.vault_path)
print(config.database.get_chroma_path())
```

### 6.2 路徑取得

```python
paths = config.paths
daily_dir = paths.project_daily_dir("LIFEOFDEVELOPMENT", "ai-memory-vault")
# → "workspaces/LIFEOFDEVELOPMENT/projects/ai-memory-vault/daily"
```

### 6.3 Docker 環境

```bash
# 設定 VAULT_DATA_DIR 覆蓋 DATA_DIR
export VAULT_DATA_DIR=/data
# → DATA_DIR = Path("/data")，ChromaDB/config/backups 都放在 /data 下
```

---

## 7. 設計注意事項

- **DATA_DIR 分離**：exe 放 Program Files 時為唯讀，資料需獨立存放於 %APPDATA%
- **VAULT_DATA_DIR 環境變數**：Docker 容器化時覆蓋 DATA_DIR，無需改程式碼
- **VaultPaths 集中管理**：所有路徑字串由 VaultPaths 生成，禁止直接拼接
- **config.json 遷移**：新增設定欄位時，`load()` 會以 dataclass 預設值填補缺失欄位
