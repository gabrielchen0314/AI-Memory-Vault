"""
Vault 檢索器
封裝語意搜尋邏輯，支援：
  - Pure Vector Search（ChromaDB 語意搜尋）
  - Hybrid Search（BM25 關鍵字 + Vector 語意，EnsembleRetriever）
  - Recency Bias（依文件日期衰減係數重排序）

透過 SearchConfig 控制搜尋行為。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
import math
import sys
from datetime import datetime, timezone
from typing import Optional

from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever

from config import CATEGORY_UNKNOWN, AppConfig
from .vectorstore import get_vectorstore


class VaultRetriever:
    """Vault 檢索器：支援 Pure Vector 與 Hybrid（BM25 + Vector）兩種模式。"""

    #region 成員變數
    ## <summary>搜尋設定快照</summary>
    m_TopK: int
    m_UseHybrid: bool
    m_BM25Weight: float
    m_VecWeight: float
    m_RecencyEnabled: bool
    m_RecencyDecayDays: int
    #endregion

    def __init__( self, iConfig: AppConfig ):
        """
        以 AppConfig 建立檢索器。

        Args:
            iConfig: 應用程式設定。
        """
        self.m_TopK = iConfig.search.top_k
        self.m_UseHybrid = iConfig.search.use_hybrid
        self.m_BM25Weight = iConfig.search.bm25_weight
        self.m_VecWeight = iConfig.search.vector_weight
        self.m_RecencyEnabled = iConfig.search.recency_bias_enabled
        self.m_RecencyDecayDays = iConfig.search.recency_decay_days

    #region 公開方法
    def search(
        self,
        iQuery: str,
        iCategory: str = "",
        iDocType: str = "",
        iTopK: Optional[int] = None,
    ) -> list:
        """
        執行搜尋（自動依設定選擇模式）。

        Args:
            iQuery:    搜尋文字。
            iCategory: 過濾分類（workspaces / personal / knowledge）。
            iDocType:  過濾文件類型（rule / project / meeting ...）。
            iTopK:     回傳筆數（預設使用 config）。

        Returns:
            搜尋結果列表，每筆含 content、source、category、metadata。
        """
        _TopK = iTopK or self.m_TopK

        print( f"\n[系統執行中] 🔍 正在搜尋：{iQuery}...", file=sys.stderr )

        if self.m_UseHybrid:
            _Docs = self._hybrid_search( iQuery, iCategory, iDocType, _TopK )
        else:
            _Filter = self._build_filter( iCategory, iDocType )
            if _Filter:
                print( f"[過濾條件] {_Filter}", file=sys.stderr )
            _Docs = get_vectorstore().similarity_search( iQuery, k=_TopK, filter=_Filter )

        # ── Recency Bias 重排序 ────────────────────────────
        if self.m_RecencyEnabled and _Docs:
            _Docs = self._apply_recency_bias( _Docs )

        _Results = []
        for _Doc in _Docs:
            _Results.append( {
                "content": _Doc.page_content,
                "source": _Doc.metadata.get( "source", "" ),
                "category": _Doc.metadata.get( "category", CATEGORY_UNKNOWN ),
                "doc_type": _Doc.metadata.get( "type", "" ),
                "domain": _Doc.metadata.get( "domain", "" ),
                "tags": _Doc.metadata.get( "tags", "" ),
                "ai_summary": _Doc.metadata.get( "ai_summary", "" ),
            } )

        return _Results

    def search_formatted(
        self,
        iQuery: str,
        iCategory: str = "",
        iDocType: str = "",
    ) -> str:
        """
        執行搜尋並回傳格式化的文字結果（供 MCP Tool 使用）。

        Args:
            iQuery:    搜尋文字。
            iCategory: 過濾分類。
            iDocType:  過濾文件類型。

        Returns:
            格式化搜尋結果字串。
        """
        _Results = self.search( iQuery, iCategory, iDocType )

        if not _Results:
            return "記憶庫中找不到相關資料。"

        _Lines = []
        for _R in _Results:
            _Header = f"[{_R['category']}]【{_R['source']}】"
            if _R["doc_type"]:
                _Header += f"（{_R['doc_type']}）"
            _Lines.append( f"{_Header}\n{_R['content']}" )

        return "\n\n---\n\n".join( _Lines )
    #endregion

    #region 私有方法
    def _hybrid_search(
        self,
        iQuery: str,
        iCategory: str,
        iDocType: str,
        iTopK: int,
    ) -> list[Document]:
        """
        BM25 關鍵字 + Vector 語意混合搜尋（EnsembleRetriever）。

        Args:
            iQuery:    搜尋文字。
            iCategory: 過濾分類。
            iDocType:  過濾文件類型。
            iTopK:     回傳筆數。

        Returns:
            去重後的 Document 列表。
        """
        _Filter = self._build_filter( iCategory, iDocType )
        _Vectorstore = get_vectorstore()

        # ── 取出語料（依 filter 縮小範圍 or 全量）──────────
        if _Filter:
            print( f"[過濾條件] {_Filter}" )
            _AllDocs = _Vectorstore.similarity_search( iQuery, k=500, filter=_Filter )
        else:
            _Raw = _Vectorstore._collection.get( include=["documents", "metadatas"] )
            _AllDocs = [
                Document( page_content=_Text, metadata=_Meta )
                for _Text, _Meta in zip( _Raw["documents"], _Raw["metadatas"] )
                if _Text
            ]

        if not _AllDocs:
            return []

        # ── BM25 Retriever ─────────────────────────────────
        _Bm25 = BM25Retriever.from_documents( _AllDocs )
        _Bm25.k = iTopK

        # ── Vector Retriever ───────────────────────────────
        _VectorKwargs: dict = {"k": iTopK}
        if _Filter:
            _VectorKwargs["filter"] = _Filter
        _VectorRetriever = _Vectorstore.as_retriever( search_kwargs=_VectorKwargs )

        # ── Ensemble（RRF 合併）────────────────────────────
        _Ensemble = EnsembleRetriever(
            retrievers=[_Bm25, _VectorRetriever],
            weights=[self.m_BM25Weight, self.m_VecWeight],
        )

        print( f"[搜尋模式] 🔀 Hybrid（BM25 {int(self.m_BM25Weight*100)}% + Vector {int(self.m_VecWeight*100)}%）", file=sys.stderr )

        # ── 去重：同一來源檔案只保留排名最高的 chunk ──────
        _SeenSources = set()
        _Deduped = []
        for _Doc in _Ensemble.invoke( iQuery ):
            _Src = _Doc.metadata.get( "source", "" )
            if _Src not in _SeenSources:
                _SeenSources.add( _Src )
                _Deduped.append( _Doc )
            if len( _Deduped ) >= iTopK:
                break

        return _Deduped

    def _apply_recency_bias( self, iDocs: list[Document] ) -> list[Document]:
        """
        依文件日期對搜尋結果套用指數衰減係數並重排序。

        衰減公式：score = e^(−ln2 / T½ × 距今天數)

        Args:
            iDocs: 搜尋結果 Document 列表。

        Returns:
            重排序後的 Document 列表。
        """
        _HalfLife = self.m_RecencyDecayDays
        _Lambda = math.log( 2 ) / _HalfLife
        _Today = datetime.now( timezone.utc ).date()

        def _decay_score( iDoc: Document ) -> float:
            _RawDate = (
                iDoc.metadata.get( "last_updated" )
                or iDoc.metadata.get( "date" )
                or iDoc.metadata.get( "created" )
                or ""
            )
            if not _RawDate:
                return 0.5

            try:
                _DateStr = str( _RawDate ).replace( ".", "-" )[:10]
                _DocDate = datetime.strptime( _DateStr, "%Y-%m-%d" ).date()
                _DaysDelta = max( 0, ( _Today - _DocDate ).days )
                return math.exp( -_Lambda * _DaysDelta )
            except ( ValueError, TypeError ):
                return 0.5

        _Scored = sorted( iDocs, key=_decay_score, reverse=True )
        return _Scored

    @staticmethod
    def _build_filter( iCategory: str, iDocType: str ) -> dict:
        """
        組建 ChromaDB where filter。

        Args:
            iCategory: 分類名稱。
            iDocType:  文件類型。

        Returns:
            ChromaDB filter dict（空則回傳 None）。
        """
        _Conditions = []
        if iCategory:
            _Conditions.append( {"category": {"$eq": iCategory}} )
        if iDocType:
            _Conditions.append( {"type": {"$eq": iDocType}} )

        if len( _Conditions ) > 1:
            return {"$and": _Conditions}
        if len( _Conditions ) == 1:
            return _Conditions[0]
        return None
    #endregion
