"""
AI Memory Vault v3 — 服務層初始化

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
# 注意：不在此處做 eager import，避免 frozen exe 在 setup/scheduler 模式下
# 不必要地載入大型 ML 套件（chromadb / sentence_transformers / torch 等），
# 這些套件包含的原生 DLL 在特定環境下會造成 STATUS_STACK_BUFFER_OVERRUN (0xC0000409)。
# 各模組請於實際需要時再 import（在各自的函式/方法中）。

__all__ = [
    "VaultService",
    "SetupService",
    "SchedulerService",
    "InstinctService",
    "AgentRouter",
    "GitService",
    "KnowledgeExtractor",
    "TokenCounter",
]
