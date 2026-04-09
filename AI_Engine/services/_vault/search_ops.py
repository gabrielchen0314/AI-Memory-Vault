"""
搜尋操作
從 VaultService 拆出的內部實作。所有函式接收 cls（VaultService class）作為第一個參數。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.6
@date 2026.04.10
"""
from __future__ import annotations

import os
import re
from typing import Optional

from core.logger import get_logger

_logger = get_logger( __name__ )


def search(
    cls,
    iQuery: str,
    iCategory: str = "",
    iDocType: str = "",
    iTopK: Optional[int] = None,
    iMode: str = "",
) -> list:
    """
    執行語意搜尋。

    Args:
        cls:       VaultService class。
        iQuery:    搜尋文字。
        iCategory: 過濾分類。
        iDocType:  過濾文件類型。
        iTopK:     回傳筆數。
        iMode:     搜尋模式（"keyword" / "semantic" / ""）。

    Returns:
        搜尋結果列表。
    """
    cls._ensure_initialized()
    return cls.m_Retriever.search( iQuery, iCategory, iDocType, iTopK, iMode )


def search_formatted(
    cls,
    iQuery: str,
    iCategory: str = "",
    iDocType: str = "",
    iMode: str = "",
) -> str:
    """
    執行語意搜尋，回傳格式化文字。

    Args:
        cls:       VaultService class。
        iQuery:    搜尋文字。
        iCategory: 過濾分類。
        iDocType:  過濾文件類型。
        iMode:     搜尋模式。

    Returns:
        格式化搜尋結果字串。
    """
    cls._ensure_initialized()
    return cls.m_Retriever.search_formatted( iQuery, iCategory, iDocType, iMode )


def grep( cls, iPattern: str, iPath: str = "", iIsRegex: bool = False, iMaxResults: int = 50 ) -> tuple:
    """
    在 Vault .md 檔案中執行純文字或正規表達式搜尋。

    Args:
        cls:         VaultService class。
        iPattern:    搜尋字串或正規表達式。
        iPath:       限定搜尋目錄。
        iIsRegex:    True = regex 比對。
        iMaxResults: 最大回傳筆數。

    Returns:
        (results_list, error_message)
    """
    cls._ensure_initialized()

    if iPath:
        _AbsDir, _Err = cls._validate_path( iPath )
        if _Err:
            return None, _Err
    else:
        _AbsDir = cls.m_VaultRoot

    if not os.path.isdir( _AbsDir ):
        return None, f"Error: directory not found — {iPath}"

    if iIsRegex:
        try:
            _Rx = re.compile( iPattern, re.IGNORECASE )
        except re.error as _E:
            return None, f"Error: invalid regex — {_E}"
    else:
        _PatternLower = iPattern.lower()

    _Results = []
    for _Root, _Dirs, _Files in os.walk( _AbsDir ):
        _Dirs[:] = sorted( d for d in _Dirs if not d.startswith( "." ) )
        for _FileName in sorted( _Files ):
            if not _FileName.endswith( ".md" ):
                continue
            _Abs = os.path.join( _Root, _FileName )
            _Rel = os.path.relpath( _Abs, cls.m_VaultRoot ).replace( os.sep, "/" )
            try:
                with open( _Abs, "r", encoding="utf-8" ) as _F:
                    for _LineNo, _Line in enumerate( _F, 1 ):
                        if iIsRegex:
                            _M = _Rx.search( _Line )
                            if _M:
                                _Results.append( {
                                    "file": _Rel, "line": _LineNo,
                                    "col": _M.start() + 1,
                                    "text": _Line.rstrip(),
                                } )
                        else:
                            _Idx = _Line.lower().find( _PatternLower )
                            if _Idx >= 0:
                                _Results.append( {
                                    "file": _Rel, "line": _LineNo,
                                    "col": _Idx + 1,
                                    "text": _Line.rstrip(),
                                } )
                        if len( _Results ) >= iMaxResults:
                            return _Results, None
            except (OSError, UnicodeDecodeError):
                continue

    return _Results, None
