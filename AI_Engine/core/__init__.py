"""
AI Memory Vault v3 — 核心模組初始化
匯出所有核心元件供上層使用。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
# 注意：不在此處做 eager import，避免 frozen exe 在 setup/scheduler 模式下
# 不必要地載入大型 ML 套件（sentence_transformers / chromadb / torch 等）。
# 各元件請於實際需要時再 import（在各自的函式/方法中）。

__all__ = [
    "get_embeddings",
    "get_vectorstore",
    "get_record_manager",
    "VaultIndexer",
    "VaultRetriever",
    "MigrationManager",
]

