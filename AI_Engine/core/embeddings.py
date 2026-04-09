"""
多語言向量嵌入模組
使用 paraphrase-multilingual-MiniLM-L12-v2 支援繁體中文語意搜尋。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
from functools import lru_cache

# ── 模組級快取（延遲載入，由 initialize() 設定模型名稱）────
_g_ModelName: str = "paraphrase-multilingual-MiniLM-L12-v2"


def initialize( iModelName: str ) -> None:
    """
    設定嵌入模型名稱（須在首次呼叫 get_embeddings 前執行）。

    Args:
        iModelName: HuggingFace 模型名稱。
    """
    global _g_ModelName
    _g_ModelName = iModelName
    # 清除快取，下次呼叫時用新模型
    get_embeddings.cache_clear()


@lru_cache( maxsize=1 )
def get_embeddings():
    """取得多語言向量嵌入模型（單例，首次呼叫時初始化）。"""
    # 延遲載入：避免 frozen exe 在 import 階段就觸發 sentence_transformers/torch DLL 載入
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings( model_name=_g_ModelName )
