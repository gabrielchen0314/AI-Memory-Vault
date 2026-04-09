"""
Vault 索引器
負責掃描 Vault 目錄、解析 Frontmatter、Markdown 切塊、注入 Metadata、增量同步至 ChromaDB。
路徑與分類標籤從 config 注入，對齊 V3 Vault 結構。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
import re
from typing import Optional

from core.logger import get_logger

_logger = get_logger( __name__ )

import yaml
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.indexing import index as langchain_index
from langchain_core.documents import Document

from config import CATEGORY_MAP, CATEGORY_UNKNOWN, EXCLUDE_DIRS, FRONTMATTER_FIELDS
from .vectorstore import get_vectorstore, get_record_manager


# ── Markdown 標題切塊設定 ─────────────────────────────────
HEADERS_TO_SPLIT = [
    ( "#", "Header 1" ),
    ( "##", "Header 2" ),
    ( "###", "Header 3" ),
]


class VaultIndexer:
    """Vault 文件索引器：掃描 → 解析 Frontmatter → 切塊 → 標籤 → 增量寫入。"""

    #region 成員變數
    ## <summary>Vault 根目錄絕對路徑</summary>
    m_VaultRoot: str
    ## <summary>Markdown 標題切塊器（第一階）</summary>
    m_Splitter: MarkdownHeaderTextSplitter
    ## <summary>字元切塊器（第二階，處理超大 chunk）</summary>
    m_CharSplitter: RecursiveCharacterTextSplitter
    ## <summary>單一 chunk 最大字元數閾值</summary>
    m_ChunkSize: int
    #endregion

    def __init__( self, iVaultRoot: str, iChunkSize: int = 500, iChunkOverlap: int = 50 ):
        """
        建立索引器。

        Args:
            iVaultRoot:    Vault 根目錄絕對路徑。
            iChunkSize:    單一 chunk 最大字元數（預設 500）。
            iChunkOverlap: 相鄰 chunk 重疊字元數（預設 50）。
        """
        self.m_VaultRoot    = iVaultRoot
        self.m_ChunkSize    = iChunkSize
        self.m_Splitter     = MarkdownHeaderTextSplitter(
            headers_to_split_on=HEADERS_TO_SPLIT,
            strip_headers=False,
        )
        self.m_CharSplitter = RecursiveCharacterTextSplitter(
            chunk_size=iChunkSize,
            chunk_overlap=iChunkOverlap,
            separators=[ "\n\n", "\n", "\uff0c", "\u3002", "\uff1b", " ", "" ],
        )

    #region 公開方法
    def sync( self ) -> dict:
        """
        執行全量增量同步。

        Returns:
            統計結果字典，包含 index_stats、category_summary、type_summary、total_chunks、total_files。
        """
        _logger.info( "🔄 正在掃描變動的筆記..." )

        # 1. 載入所有 .md 檔案
        _Loader = DirectoryLoader(
            self.m_VaultRoot,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        _RawDocs = _Loader.load()

        # 2. 過濾排除目錄
        _FilteredDocs = [
            _Doc for _Doc in _RawDocs
            if not self._should_exclude( _Doc.metadata.get( "source", "" ) )
        ]
        _logger.info( "掃描結果：共 %d 個檔案（已排除 %d 個）", len( _FilteredDocs ), len( _RawDocs ) - len( _FilteredDocs ) )

        # 3. 逐一處理：解析 Frontmatter → 切塊 → 注入 Metadata
        _TaggedChunks: list = []
        _CategoryCounter: dict = {}
        _TypeCounter: dict = {}

        for _Doc in _FilteredDocs:
            _Chunks = self._process_doc( _Doc )
            _TaggedChunks.extend( _Chunks )
            if _Chunks:
                _Category = _Chunks[0].metadata.get( "category", "" )
                _CategoryCounter[_Category] = _CategoryCounter.get( _Category, 0 ) + len( _Chunks )
                _DocType = _Chunks[0].metadata.get( "type", "" ) or "未標註"
                _TypeCounter[_DocType] = _TypeCounter.get( _DocType, 0 ) + len( _Chunks )

        # 4. 全量掃描寫入 ChromaDB（full 模式：清除不在本次掃描中的孤立向量）
        _Stats = langchain_index(
            _TaggedChunks,
            get_record_manager(),
            get_vectorstore(),
            cleanup="full",
            source_id_key="source",
            key_encoder="blake2b",
        )

        _CategorySummary = " | ".join(
            f"{k}: {v} 筆" for k, v in sorted( _CategoryCounter.items() )
        )
        _TypeSummary = " | ".join(
            f"{k}: {v}" for k, v in sorted( _TypeCounter.items() )
        )

        return {
            "index_stats": _Stats,
            "category_summary": _CategorySummary,
            "type_summary": _TypeSummary,
            "total_chunks": len( _TaggedChunks ),
            "total_files": len( _FilteredDocs ),
        }

    def sync_single( self, iAbsPath: str ) -> dict:
        """
        對單一檔案執行增量索引（寫入後即時更新，不掃全 Vault）。

        Args:
            iAbsPath: 檔案絕對路徑。

        Returns:
            與 sync() 相同結構的統計字典。
        """
        import os

        if not os.path.isfile( iAbsPath ):
            return {
                "index_stats": {"num_added": 0, "num_updated": 0, "num_deleted": 0, "num_skipped": 0},
                "category_summary": "",
                "type_summary": "",
                "total_chunks": 0,
                "total_files": 0,
            }

        with open( iAbsPath, "r", encoding="utf-8" ) as _F:
            _Content = _F.read()

        _Doc = Document( page_content=_Content, metadata={"source": iAbsPath} )
        _TaggedChunks = self._process_doc( _Doc )

        _Stats = langchain_index(
            _TaggedChunks,
            get_record_manager(),
            get_vectorstore(),
            cleanup="incremental",
            source_id_key="source",
            key_encoder="blake2b",
        )

        return {
            "index_stats": _Stats,
            "category_summary": "",
            "type_summary": "",
            "total_chunks": len( _TaggedChunks ),
            "total_files": 1,
        }

    def delete_source( self, iAbsPath: str ) -> dict:
        """
        從 ChromaDB 與 RecordManager 中移除指定來源檔案的所有向量記錄。
        物理檔案應已在呼叫前刪除。

        Args:
            iAbsPath: 檔案絕對路徑（即 source metadata 值）。

        Returns:
            與 sync_single() 相同結構的統計字典，num_deleted 為實際移除筆數。
        """
        _Rm = get_record_manager()
        _Vs = get_vectorstore()
        _Keys = _Rm.list_keys( group_ids=[ iAbsPath ] )
        _Count = len( _Keys )
        if _Keys:
            _Vs.delete( ids=_Keys )
            _Rm.delete_keys( keys=_Keys )

        return {
            "index_stats": {
                "num_added": 0,
                "num_updated": 0,
                "num_deleted": _Count,
                "num_skipped": 0,
            },
            "category_summary": "",
            "type_summary": "",
            "total_chunks": 0,
            "total_files": 0,
        }

    def sync_batch( self, iAbsPaths: list ) -> dict:
        """
        對多個檔案執行批次增量索引（一次呼叫 ChromaDB，比逐一 sync_single 效率高）。

        Args:
            iAbsPaths: 檔案絕對路徑列表。

        Returns:
            與 sync() / sync_single() 相同結構的統計字典，total_files 為成功處理的檔案數。
        """
        import os

        _AllChunks: list = []
        _FileCount = 0

        for _AbsPath in iAbsPaths:
            if not os.path.isfile( _AbsPath ):
                continue

            with open( _AbsPath, "r", encoding="utf-8" ) as _F:
                _Content = _F.read()

            _Doc = Document( page_content=_Content, metadata={"source": _AbsPath} )
            _Chunks = self._process_doc( _Doc )
            _AllChunks.extend( _Chunks )
            _FileCount += 1

        if not _AllChunks:
            return {
                "index_stats": {"num_added": 0, "num_updated": 0, "num_deleted": 0, "num_skipped": 0},
                "category_summary": "",
                "type_summary": "",
                "total_chunks": 0,
                "total_files": _FileCount,
            }

        _Stats = langchain_index(
            _AllChunks,
            get_record_manager(),
            get_vectorstore(),
            cleanup="incremental",
            source_id_key="source",
            key_encoder="blake2b",
        )

        return {
            "index_stats": _Stats,
            "category_summary": "",
            "type_summary": "",
            "total_chunks": len( _AllChunks ),
            "total_files": _FileCount,
        }
    #endregion

    #region 私有方法
    def _process_doc( self, iDoc ) -> list:
        """
        處理單一 Document：解析 Frontmatter → 切塊 → 注入 Metadata。

        Args:
            iDoc: LangChain Document 物件。

        Returns:
            已標記的 chunk 清單。
        """
        _SourcePath = iDoc.metadata.get( "source", "" )
        _Category = self._resolve_category( _SourcePath )
        _FrontMeta, _Body = self._parse_frontmatter( iDoc.page_content )

        _DocMeta = {
            "source": _SourcePath,
            "category": _Category,
        }

        for _Field in FRONTMATTER_FIELDS:
            _Value = _FrontMeta.get( _Field, "" )
            if isinstance( _Value, list ):
                _Value = ",".join( str( v ) for v in _Value )
            _DocMeta[_Field] = str( _Value ) if _Value else ""

        _Tags = _FrontMeta.get( "tags", [] )
        if isinstance( _Tags, list ):
            _DocMeta["tags"] = ",".join( str( t ) for t in _Tags )
        else:
            _DocMeta["tags"] = str( _Tags ) if _Tags else ""

        _HeaderChunks = self.m_Splitter.split_text( _Body )

        # 第二階：對超出 size 上限的 chunk 再切（保留 header metadata）
        _FinalChunks: list = []
        for _HC in _HeaderChunks:
            if len( _HC.page_content ) > self.m_ChunkSize:
                _SubDocs = self.m_CharSplitter.split_documents( [ _HC ] )
                _FinalChunks.extend( _SubDocs )
            else:
                _FinalChunks.append( _HC )

        for _Chunk in _FinalChunks:
            _Chunk.metadata.update( _DocMeta )

        return _FinalChunks

    @staticmethod
    def _resolve_category( iSourcePath: str ) -> str:
        """
        依檔案路徑解析所屬分類標籤。

        Args:
            iSourcePath: 檔案絕對路徑。

        Returns:
            分類標籤字串。
        """
        _Normalized = iSourcePath.replace( "\\", "/" ).lower()
        for _Key, _Label in CATEGORY_MAP.items():
            if f"/{_Key}/" in _Normalized or _Normalized.startswith( _Key + "/" ):
                return _Label
        return CATEGORY_UNKNOWN

    @staticmethod
    def _parse_frontmatter( iContent: str ) -> tuple:
        """
        解析 YAML Frontmatter。

        Args:
            iContent: Markdown 原始內容。

        Returns:
            (metadata_dict, body_content) 元組。
        """
        _Match = re.match( r"^---\s*\n(.*?)\n---\s*\n?", iContent, re.DOTALL )
        if _Match:
            try:
                _Meta = yaml.safe_load( _Match.group( 1 ) ) or {}
                _Body = iContent[_Match.end():]
                return _Meta, _Body
            except yaml.YAMLError:
                return {}, iContent
        return {}, iContent

    @staticmethod
    def _should_exclude( iSource: str ) -> bool:
        """
        判斷是否應排除此檔案。

        Args:
            iSource: 檔案路徑。

        Returns:
            是否排除。
        """
        _Normalized = iSource.replace( "\\", "/" )
        for _Dir in EXCLUDE_DIRS:
            if f"/{_Dir}/" in _Normalized or _Normalized.startswith( _Dir + "/" ):
                return True
        return False
    #endregion
