"""
多語言向量嵌入模組
使用 paraphrase-multilingual-MiniLM-L12-v2 支援繁體中文語意搜尋。
取代舊版的純英文模型 all-MiniLM-L6-v2。

@author gabrielchen
@version 2.0
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from config import settings


@lru_cache( maxsize=1 )
def get_embeddings() -> HuggingFaceEmbeddings:
    """取得多語言向量嵌入模型（單例，首次呼叫時初始化）。"""
    return HuggingFaceEmbeddings( model_name=settings.EMBEDDING_MODEL )
