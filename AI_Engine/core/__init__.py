"""
AI Memory Vault v3 — 核心模組初始化
匯出所有核心元件供上層使用。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
from .embeddings import get_embeddings
from .vectorstore import get_vectorstore, get_record_manager
from .indexer import VaultIndexer
from .retriever import VaultRetriever

__all__ = [
    "get_embeddings",
    "get_vectorstore",
    "get_record_manager",
    "VaultIndexer",
    "VaultRetriever",
]
