"""
Vault 業務邏輯層
三個模式（CLI / API / MCP）的唯一業務邏輯入口。
統一路徑驗證、.md 檢查、讀寫、搜尋、同步、寫入後自動索引。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 2.0
@date 2026.03.29
"""
import os
from typing import Optional

from config import VAULT_ROOT


class VaultService:
    """Vault 業務邏輯：所有對外操作的統一入口。"""

    #region 常數定義
    ALLOWED_EXTENSION: str = ".md"
    ERROR_PATH_TRAVERSAL: str = "Error: path traversal not allowed."
    ERROR_NOT_FOUND: str = "Error: file not found — {file_path}"
    ERROR_EXTENSION: str = "Error: only .md files are allowed."
    #endregion

    #region 成員變數
    ## <summary>Vault 根目錄絕對路徑</summary>
    m_VaultRoot: str = os.path.realpath( str( VAULT_ROOT ) )
    #endregion

    #region 私有方法
    @classmethod
    def _validate_path( cls, iFilePath: str ) -> tuple:
        """
        驗證並解析相對路徑為安全的絕對路徑。

        Args:
            iFilePath: 相對於 Vault 根目錄的檔案路徑。

        Returns:
            (abs_path, error_message) — 成功時 error_message 為 None。
        """
        _AbsPath = os.path.realpath( os.path.join( cls.m_VaultRoot, iFilePath ) )

        if not _AbsPath.startswith( cls.m_VaultRoot ):
            return None, cls.ERROR_PATH_TRAVERSAL

        return _AbsPath, None

    @classmethod
    def _validate_write_path( cls, iFilePath: str ) -> tuple:
        """
        驗證寫入路徑（含路徑穿越防護 + .md 限制）。

        Args:
            iFilePath: 相對於 Vault 根目錄的檔案路徑。

        Returns:
            (abs_path, error_message) — 成功時 error_message 為 None。
        """
        _AbsPath, _Error = cls._validate_path( iFilePath )
        if _Error:
            return None, _Error

        if not _AbsPath.endswith( cls.ALLOWED_EXTENSION ):
            return None, cls.ERROR_EXTENSION

        return _AbsPath, None
    #endregion

    #region 公開方法
    @classmethod
    def read_note( cls, iFilePath: str ) -> tuple:
        """
        讀取 Vault 中指定筆記的完整原始內容。

        Args:
            iFilePath: 相對於 Vault 根目錄的檔案路徑。

        Returns:
            (content, error_message) — 成功時 error_message 為 None。
        """
        _AbsPath, _Error = cls._validate_path( iFilePath )
        if _Error:
            return None, _Error

        if not os.path.isfile( _AbsPath ):
            return None, cls.ERROR_NOT_FOUND.format( file_path=iFilePath )

        with open( _AbsPath, "r", encoding="utf-8" ) as _F:
            return _F.read(), None

    @classmethod
    def write_note( cls, iFilePath: str, iContent: str, iMode: str = "overwrite" ) -> tuple:
        """
        寫入或更新 Vault 中的筆記檔案，並自動索引至向量庫。

        Args:
            iFilePath: 相對於 Vault 根目錄的檔案路徑。
            iContent:  要寫入的內容。
            iMode:     寫入模式。'overwrite' = 覆寫；'append' = 追加。

        Returns:
            (stats_dict, error_message) — 成功時 error_message 為 None。
            stats_dict 包含 index_stats、total_chunks 等。
        """
        _AbsPath, _Error = cls._validate_write_path( iFilePath )
        if _Error:
            return None, _Error

        _Dir = os.path.dirname( _AbsPath )
        if not os.path.exists( _Dir ):
            os.makedirs( _Dir, exist_ok=True )

        _WriteMode = "a" if iMode == "append" else "w"
        _WriteContent = ( "\n" + iContent ) if iMode == "append" else iContent
        with open( _AbsPath, _WriteMode, encoding="utf-8" ) as _F:
            _F.write( _WriteContent )

        # 寫入後自動索引（單檔增量）
        from core.indexer import VaultIndexer
        _Stats = VaultIndexer().sync_single( _AbsPath )

        return {
            "file_path": iFilePath,
            "chars": len( iContent ),
            "mode": iMode,
            "index_stats": _Stats["index_stats"],
            "total_chunks": _Stats["total_chunks"],
        }, None

    @classmethod
    def search(
        cls,
        iQuery: str,
        iCategory: str = "",
        iDocType: str = "",
        iTopK: Optional[int] = None,
    ) -> list:
        """
        執行語意搜尋（自動選擇 Hybrid 或 Pure Vector）。

        Args:
            iQuery:    搜尋文字。
            iCategory: 過濾分類（work / life / knowledge）。
            iDocType:  過濾文件類型。
            iTopK:     回傳筆數。

        Returns:
            搜尋結果列表。
        """
        from core.retriever import VaultRetriever
        return VaultRetriever().search( iQuery, iCategory, iDocType, iTopK )

    @classmethod
    def search_formatted(
        cls,
        iQuery: str,
        iCategory: str = "",
        iDocType: str = "",
    ) -> str:
        """
        執行語意搜尋，回傳格式化文字。

        Args:
            iQuery:    搜尋文字。
            iCategory: 過濾分類。
            iDocType:  過濾文件類型。

        Returns:
            格式化搜尋結果字串。
        """
        from core.retriever import VaultRetriever
        return VaultRetriever().search_formatted( iQuery, iCategory, iDocType )

    @classmethod
    def sync( cls ) -> dict:
        """
        執行全量增量同步。

        Returns:
            統計結果字典。
        """
        from core.indexer import VaultIndexer
        return VaultIndexer().sync()
    #endregion
