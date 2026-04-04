"""
Vault 檢索器
封裝語意搜尋邏輯，支援：
  - Pure Vector Search（ChromaDB 語意搜尋）
  - Hybrid Search（BM25 關鍵字 + Vector 語意，EnsembleRetriever）
  - Recency Bias（依文件日期衰減係數重排序）

透過 config.USE_HYBRID_SEARCH / RECENCY_BIAS_ENABLED 切換。

@author gabrielchen
@version 2.2
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
import math
from datetime import datetime, timezone
from typing import Optional
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from config import settings, CATEGORY_MAP, CATEGORY_UNKNOWN
from .vectorstore import get_vectorstore


class VaultRetriever:
    """Vault 檢索器：支援 Pure Vector 與 Hybrid（BM25 + Vector）兩種模式。"""

    def search(
        self,
        iQuery: str,
        iCategory: str = "",
        iDocType: str = "",
        iTopK: Optional[int] = None,
    ) -> list:
        """
        執行搜尋（自動依 USE_HYBRID_SEARCH 設定選擇模式）。

        Args:
            iQuery:    搜尋文字。
            iCategory: 過濾分類（work / life / knowledge）。
            iDocType:  過濾文件類型（rule / project / meeting ...）。
            iTopK:     回傳筆數（預設使用 settings.SEARCH_TOP_K）。

        Returns:
            搜尋結果列表，每筆含 content、source、category、metadata。
        """
        _TopK = iTopK or settings.SEARCH_TOP_K

        print( f"\n[系統執行中] 🔍 正在搜尋：{iQuery}..." )

        if settings.USE_HYBRID_SEARCH:
            _Docs = self._hybrid_search( iQuery, iCategory, iDocType, _TopK )
        else:
            _Filter = self._build_filter( iCategory, iDocType )
            if _Filter:
                print( f"[過濾條件] {_Filter}" )
            _Docs = get_vectorstore().similarity_search( iQuery, k=_TopK, filter=_Filter )

        # ── Recency Bias 重排序 ────────────────────────────
        if settings.RECENCY_BIAS_ENABLED and _Docs:
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

    def _hybrid_search(
        self,
        iQuery: str,
        iCategory: str,
        iDocType: str,
        iTopK: int,
    ) -> list[Document]:
        """
        BM25 關鍵字 + Vector 語意混合搜尋（EnsembleRetriever）。

        策略：
          1. 從 ChromaDB 取出所有 Document（含 metadata）作為 BM25 語料庫。
          2. 若有 category/doc_type 過濾，先用 Vector filter 縮小語料範圍後再做 BM25。
          3. EnsembleRetriever 合併兩路結果（BM25 權重 0.4 + Vector 權重 0.6）。
        """
        _Filter = self._build_filter( iCategory, iDocType )
        _Vectorstore = get_vectorstore()

        # ── 取出語料（依 filter 縮小範圍 or 全量）──────────
        if _Filter:
            print( f"[過濾條件] {_Filter}" )
            # 先用 Vector Search 取出過濾後的全部相關文件作為 BM25 語料
            _AllDocs = _Vectorstore.similarity_search( iQuery, k=500, filter=_Filter )
        else:
            # 全量取出（Chroma get() 直接拿 raw data）
            _Raw = _Vectorstore._collection.get( include=["documents", "metadatas"] )
            _AllDocs = [
                Document( page_content=_Text, metadata=_Meta )
                for _Text, _Meta in zip( _Raw["documents"], _Raw["metadatas"] )
                if _Text  # 過濾空內容
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
        _BM25Weight = settings.HYBRID_BM25_WEIGHT
        _VecWeight = round( 1.0 - _BM25Weight, 2 )
        _Ensemble = EnsembleRetriever(
            retrievers=[_Bm25, _VectorRetriever],
            weights=[_BM25Weight, _VecWeight],
        )

        print( f"[搜尋模式] 🔀 Hybrid（BM25 {int(_BM25Weight*100)}% + Vector {int(_VecWeight*100)}%）" )

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

    def search_formatted(
        self,
        iQuery: str,
        iCategory: str = "",
        iDocType: str = "",
    ) -> str:
        """執行搜尋並回傳格式化的文字結果（供 LangChain Tool 使用）。"""
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

    @staticmethod
    def _apply_recency_bias( iDocs: list[Document] ) -> list[Document]:
        """
        依文件日期對搜尋結果套用指數衰減係數並重排序。

        衰減公式：score = e^(−ln2 / T½ × 距今天數)
        T½ = settings.RECENCY_DECAY_DAYS（預設 90 天，超過後分數約 0.5）

        優先讀取 metadata 的 'last_updated' > 'date' > 'created' 欄位，支援
        YYYY-MM-DD 與 YYYY.MM.DD 兩種格式。無法解析時係數視為 0.5（中等優先）。
        """
        _HalfLife = settings.RECENCY_DECAY_DAYS
        _Lambda = math.log( 2 ) / _HalfLife
        _Today = datetime.now( timezone.utc ).date()

        def _decay_score( iDoc: Document ) -> float:
            # 依優先順序取日期欄位
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

        _Top = _Scored[0].metadata
        _TopDate = _Top.get( "last_updated" ) or _Top.get( "date" ) or _Top.get( "created", "unknown" )
        print( f"[Recency Bias] 重排序完成，最新文件日期：{_TopDate}" )

        return _Scored

    @staticmethod
    def _build_filter( iCategory: str, iDocType: str ) -> Optional[dict]:
        """組合 ChromaDB where 過濾條件。"""
        _Conditions = []

        if iCategory:
            _Label = CATEGORY_MAP.get( iCategory.lower().strip() )
            if _Label:
                _Conditions.append( {"category": {"$eq": _Label}} )

        if iDocType:
            _Conditions.append( {"type": {"$eq": iDocType}} )

        if not _Conditions:
            return None
        if len( _Conditions ) == 1:
            return _Conditions[0]
        return {"$and": _Conditions}
