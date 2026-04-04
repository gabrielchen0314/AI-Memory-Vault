"""
AI 第二大腦 — 全域設定
所有配置集中管理，從 .env 載入。敏感資訊與可調參數統一在此。

@author gabrielchen
@version 2.0
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
from pathlib import Path
from pydantic_settings import BaseSettings


# ── 路徑常數（由程式碼位置推導，不可從 .env 覆寫）──────────
ENGINE_DIR: Path = Path(__file__).resolve().parent
VAULT_ROOT: Path = ENGINE_DIR.parent / "Vault"

# ── 分類標籤對照表 ──────────────────────────────────────────
CATEGORY_MAP: dict = {
    "work":      "💼 工作",
    "life":      "🏠 生活",
    "knowledge": "📚 知識",
    "templates": "🧩 模板",
    "_system":   "⚙️ 系統",
}
CATEGORY_UNKNOWN: str = "📁 未分類"

# ── 索引時需排除的目錄 ────────────────────────────────────
EXCLUDE_DIRS: set = {
    "_AI_Engine", ".venv", "chroma_db", "node_modules",
    ".git", "__pycache__", ".obsidian", ".trash", ".ai_memory",
}

# ── Frontmatter 中要提取的欄位 ────────────────────────────
FRONTMATTER_FIELDS: list = ["type", "domain", "workspace", "severity", "ai_summary", "date", "created", "last_updated"]


class Settings( BaseSettings ):
    """從 .env 載入的全域設定。"""

    # ── LLM 設定 ──────────────────────────────
    LLM_PROVIDER: str = "gemini"
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-lite"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # ── 向量搜尋設定 ──────────────────────────
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    SEARCH_TOP_K: int = 5
    USE_HYBRID_SEARCH: bool = True       # BM25 + Vector 混合檢索
    HYBRID_BM25_WEIGHT: float = 0.4      # BM25 權重（Vector 權重 = 1 - 此值）
    RECENCY_BIAS_ENABLED: bool = True    # 啟用近期偏好重排序
    RECENCY_DECAY_DAYS: int = 90         # 半衰期（天數）：超過此天數後分數衰減至 ~50%

    # ── Core Memory 設定 ──────────────────────
    CORE_MEMORY_ENABLED: bool = True     # 啟用 Core Memory 注入 System Prompt
    CORE_MEMORY_PATH: str = "_system/core-memory.md"  # 相對於 VAULT_ROOT

    # ── 對話設定 ──────────────────────────────
    MAX_HISTORY_TURNS: int = 10

    # ── API 設定 ──────────────────────────────
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # ── Messaging Gateway 設定 ────────────────
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

    # Discord Bot 設定
    DISCORD_BOT_TOKEN: str = ""
    DISCORD_CHANNEL_ID: int = 0

    model_config = {
        "env_file": str( ENGINE_DIR / ".env" ),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# 模組級單例，import 即可用
settings = Settings()
