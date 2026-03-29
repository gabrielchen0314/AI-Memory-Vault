"""
向量資料庫管理模組
管理 ChromaDB 連線與 SQLRecordManager 增量追蹤。

@author gabrielchen
@version 2.0
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
from functools import lru_cache
from langchain_chroma import Chroma
from langchain_community.indexes._sql_record_manager import SQLRecordManager
from config import ENGINE_DIR
from .embeddings import get_embeddings


# ── 資料庫路徑（從 ENGINE_DIR 推導）──────────────────────
CHROMA_DB_DIR: str = str( ENGINE_DIR / "chroma_db" )
RECORD_DB_URL: str = f"sqlite:///{ENGINE_DIR / 'record_manager_cache.sql'}"
COLLECTION_NAME: str = "vault_main"


@lru_cache( maxsize=1 )
def get_vectorstore() -> Chroma:
    """取得 ChromaDB 向量資料庫實例（單例）。"""
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DB_DIR,
        embedding_function=get_embeddings(),
    )


@lru_cache( maxsize=1 )
def get_record_manager() -> SQLRecordManager:
    """取得 SQLRecordManager 實例（單例），用於增量索引追蹤。"""
    _Manager = SQLRecordManager( f"chroma/{COLLECTION_NAME}", db_url=RECORD_DB_URL )
    _Manager.create_schema()
    return _Manager
