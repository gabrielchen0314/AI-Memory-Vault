"""
Vault 索引器
負責掃描 Vault 目錄、解析 Frontmatter、Markdown 切塊、注入 Metadata、增量同步至 ChromaDB。

修正舊版缺失：
  - 新增 YAML Frontmatter 解析，將 type/domain/workspace/severity/tags 寫入 metadata
  - 排除 _AI_Engine、.venv 等非筆記目錄
  - 支援多維度過濾檢索

@author gabrielchen
@version 2.0
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
import re
from typing import Optional

import yaml
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.indexing import index as langchain_index
from langchain_core.documents import Document

from config import VAULT_ROOT, CATEGORY_MAP, CATEGORY_UNKNOWN, EXCLUDE_DIRS, FRONTMATTER_FIELDS
from .vectorstore import get_vectorstore, get_record_manager


# ── Markdown 標題切塊設定 ─────────────────────────────────
HEADERS_TO_SPLIT = [
    ( "#", "Header 1" ),
    ( "##", "Header 2" ),
    ( "###", "Header 3" ),
]


class VaultIndexer:
    """Vault 文件索引器：掃描 → 解析 Frontmatter → 切塊 → 標籤 → 增量寫入。"""

    def __init__( self ):
        self.m_VaultRoot: str = str( VAULT_ROOT )
        self.m_Splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=HEADERS_TO_SPLIT,
            strip_headers=False,
        )

    def sync( self ) -> dict:
        """執行全量增量同步，回傳統計結果字典。"""
        print( "\n[系統執行中] 🔄 正在掃描變動的筆記..." )

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
        print( f"[掃描結果] 共 {len( _FilteredDocs )} 個檔案（已排除 {len( _RawDocs ) - len( _FilteredDocs )} 個）" )

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

        # 4. 增量寫入 ChromaDB
        _Stats = langchain_index(
            _TaggedChunks,
            get_record_manager(),
            get_vectorstore(),
            cleanup="incremental",
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
        回傳與 sync() 相同結構的統計字典。
        """
        import os
        from langchain_core.documents import Document as _Document

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

        _Doc = _Document( page_content=_Content, metadata={"source": iAbsPath} )
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

    def _process_doc( self, iDoc ) -> list:
        """
        處理單一 Document：解析 Frontmatter → 切塊 → 注入 Metadata。
        回傳已標記的 chunk 清單。
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

        _Chunks = self.m_Splitter.split_text( _Body )
        for _Chunk in _Chunks:
            _Chunk.metadata.update( _DocMeta )

        return _Chunks

    @staticmethod
    def _resolve_category( iSourcePath: str ) -> str:
        """依檔案路徑解析所屬分類標籤。"""
        _Normalized = iSourcePath.replace( "\\", "/" ).lower()
        for _Key, _Label in CATEGORY_MAP.items():
            if f"/{_Key}/" in _Normalized or _Normalized.startswith( _Key + "/" ):
                return _Label
        return CATEGORY_UNKNOWN

    @staticmethod
    def _parse_frontmatter( iContent: str ) -> tuple:
        """解析 YAML Frontmatter，回傳 (metadata_dict, body_content)。"""
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
        """判斷檔案是否應被排除（位於排除目錄中）。"""
        _Parts = iSource.replace( "\\", "/" ).split( "/" )
        return any( _Part in EXCLUDE_DIRS for _Part in _Parts )
