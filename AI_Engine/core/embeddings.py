"""
多語言向量嵌入模組
使用 paraphrase-multilingual-MiniLM-L12-v2 支援繁體中文語意搜尋。

@author gabrielchen
@version 3.1
@since AI-Memory-Vault 3.0
@date 2026.04.11
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


# ──────────────────────────────────────────────────────────
#  Frozen Exe 專用：OnnxEmbeddings
#  完全繞過 torch / sentence-transformers（import torch 在
#  PyInstaller 中觸發 STATUS_STACK_BUFFER_OVERRUN 0xC0000409），
#  僅使用 onnxruntime + tokenizers + huggingface_hub。
# ──────────────────────────────────────────────────────────
class _OnnxEmbeddings:
    """LangChain Embeddings 相容介面，使用 ONNX Runtime 直接推理。"""

    def __init__( self, iModelName: str ):
        import numpy as np
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        _RepoId = iModelName
        if "/" not in _RepoId:
            _RepoId = f"sentence-transformers/{_RepoId}"

        _TokPath   = hf_hub_download( repo_id=_RepoId, filename="tokenizer.json" )
        _ModelPath = hf_hub_download( repo_id=_RepoId, filename="onnx/model.onnx" )

        self._tokenizer = Tokenizer.from_file( _TokPath )
        self._tokenizer.enable_padding()
        self._tokenizer.enable_truncation( max_length=128 )
        self._session = ort.InferenceSession( _ModelPath )
        self._np = np

    # -- LangChain Embeddings 介面 --

    def embed_documents( self, texts: list[str] ) -> list[list[float]]:
        if not texts:
            return []
        return self._encode_batch( texts )

    def embed_query( self, text: str ) -> list[float]:
        return self._encode_batch( [text] )[0]

    # -- 內部 --

    def _encode_batch( self, texts: list[str] ) -> list[list[float]]:
        np = self._np
        encodings = self._tokenizer.encode_batch( texts )

        _Ids  = np.array( [e.ids for e in encodings], dtype=np.int64 )
        _Mask = np.array( [e.attention_mask for e in encodings], dtype=np.int64 )
        _Tids = np.zeros_like( _Ids )

        _Outputs = self._session.run(
            None,
            { "input_ids": _Ids, "attention_mask": _Mask, "token_type_ids": _Tids },
        )

        # Mean pooling
        _TokenEmbs = _Outputs[0]                                       # (batch, seq, hidden)
        _MaskF     = _Mask[:, :, np.newaxis].astype( np.float32 )
        _Summed    = np.sum( _TokenEmbs * _MaskF, axis=1 )
        _Counts    = np.clip( np.sum( _MaskF, axis=1 ), 1e-9, None )
        _MeanPooled = _Summed / _Counts

        return _MeanPooled.tolist()


@lru_cache( maxsize=1 )
def get_embeddings():
    """取得多語言向量嵌入模型（單例，首次呼叫時初始化）。"""
    import sys

    if getattr( sys, 'frozen', False ):
        # frozen exe：使用 ONNX Runtime 直接推理（不 import torch）
        return _OnnxEmbeddings( _g_ModelName )

    # 開發模式：使用 HuggingFaceEmbeddings（sentence-transformers + torch）
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings( model_name=_g_ModelName )
