"""
向量資料庫管理模組
管理 ChromaDB 連線與 SQLRecordManager 增量追蹤。
路徑從 DatabaseConfig 注入，不再硬編碼。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
from functools import lru_cache


# ── 模組級設定（由 initialize() 注入）─────────────────────
_g_ChromaDir: str = ""
_g_RecordDbUrl: str = ""
_g_CollectionName: str = "vault_main"


def initialize( iChromaDir: str, iRecordDbUrl: str, iCollectionName: str = "vault_main" ) -> None:
    """
    注入資料庫路徑設定（須在首次呼叫 get_vectorstore 前執行）。

    Args:
        iChromaDir:       ChromaDB 持久化目錄絕對路徑。
        iRecordDbUrl:     RecordManager SQLite URL。
        iCollectionName:  ChromaDB 集合名稱。
    """
    global _g_ChromaDir, _g_RecordDbUrl, _g_CollectionName
    _g_ChromaDir = iChromaDir
    _g_RecordDbUrl = iRecordDbUrl
    _g_CollectionName = iCollectionName
    # 清除快取，下次呼叫時用新路徑
    get_vectorstore.cache_clear()
    get_record_manager.cache_clear()


@lru_cache( maxsize=1 )
def get_vectorstore():
    """取得 ChromaDB 向量資料庫實例（單例）。"""
    # 延遲載入：避免 frozen exe 在 import 階段就觸發 chromadb DLL 載入
    from langchain_chroma import Chroma
    from .embeddings import get_embeddings
    if not _g_ChromaDir:
        raise RuntimeError( "vectorstore 尚未初始化，請先呼叫 vectorstore.initialize()。" )
    return Chroma(
        collection_name=_g_CollectionName,
        persist_directory=_g_ChromaDir,
        embedding_function=get_embeddings(),
    )


@lru_cache( maxsize=1 )
def get_record_manager():
    """取得 SQLRecordManager 實例（單例），用於增量索引追蹤。"""
    # 延遲載入
    from langchain_community.indexes._sql_record_manager import SQLRecordManager
    if not _g_RecordDbUrl:
        raise RuntimeError( "record_manager 尚未初始化，請先呼叫 vectorstore.initialize()。" )
    _Manager = SQLRecordManager( f"chroma/{_g_CollectionName}", db_url=_g_RecordDbUrl )
    _Manager.create_schema()
    return _Manager
