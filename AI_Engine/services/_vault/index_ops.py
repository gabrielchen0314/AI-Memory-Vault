"""
索引管理 + 專案狀態操作
從 VaultService 拆出的內部實作。所有函式接收 cls（VaultService class）作為第一個參數。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.6
@date 2026.04.10
"""
from __future__ import annotations

import os
from typing import Optional

from core.logger import get_logger

_logger = get_logger( __name__ )


def sync( cls ) -> dict:
    """
    執行全量增量同步。

    Args:
        cls: VaultService class。

    Returns:
        統計結果字典。
    """
    cls._ensure_initialized()
    return cls.m_Indexer.sync()


def check_integrity( cls ) -> tuple:
    """
    比對 ChromaDB 已索引的 source 路徑與 Vault 檔案系統，
    找出孤立記錄。

    Args:
        cls: VaultService class。

    Returns:
        ({orphaned, total_db_sources, total_files}, error)
    """
    cls._ensure_initialized()
    try:
        from core.vectorstore import get_vectorstore

        _Vs = get_vectorstore()
        _All = _Vs.get( include=["metadatas"] )
        _DbSources = {
            _M.get( "source" )
            for _M in _All["metadatas"]
            if _M.get( "source" )
        }

        _Orphaned = sorted( _S for _S in _DbSources if not os.path.isfile( _S ) )

        _FileCount = sum(
            len( [_F for _F in _Files if _F.endswith( ".md" )] )
            for _, _, _Files in os.walk( cls.m_VaultRoot )
        )

        return (
            {
                "orphaned": _Orphaned,
                "total_db_sources": len( _DbSources ),
                "total_files": _FileCount,
            },
            None,
        )
    except Exception as _Ex:
        return ( None, str( _Ex ) )


def clean_orphans( cls ) -> tuple:
    """
    移除 ChromaDB 中所有孤立向量記錄。

    Args:
        cls: VaultService class。

    Returns:
        ({removed, orphaned_sources, total_db_sources_before}, error)
    """
    cls._ensure_initialized()
    try:
        _Integrity, _Err = check_integrity( cls )
        if _Err:
            return None, _Err

        _Orphaned = _Integrity["orphaned"]
        if not _Orphaned:
            return (
                {
                    "removed": 0,
                    "orphaned_sources": [],
                    "total_db_sources_before": _Integrity["total_db_sources"],
                },
                None,
            )

        _TotalRemoved = 0
        for _Source in _Orphaned:
            _Stats = cls.m_Indexer.delete_source( _Source )
            _TotalRemoved += _Stats["index_stats"]["num_deleted"]

        return (
            {
                "removed": _TotalRemoved,
                "orphaned_sources": _Orphaned,
                "total_db_sources_before": _Integrity["total_db_sources"],
            },
            None,
        )
    except Exception as _Ex:
        return ( None, str( _Ex ) )


def get_project_status( cls, iOrg: str, iProject: str ) -> tuple:
    """
    讀取指定專案的 status.md 並回傳結構化資料。

    Args:
        cls:      VaultService class。
        iOrg:     組織名稱。
        iProject: 專案名稱。

    Returns:
        ({last_updated, pending_todos, completed_todos, context_lines, path}, error)
    """
    cls._ensure_initialized()

    _RelPath = cls.m_Config.paths.project_status_file( iOrg, iProject )

    # 使用 note_ops.read_note 讀取
    from services._vault.note_ops import read_note
    _Content, _Err = read_note( cls, _RelPath )
    if _Err:
        return ( None, _Err )
    if not _Content:
        return ( None, f"Error: file not found — {_RelPath}" )

    # 解析 YAML frontmatter
    _LastUpdated = ""
    _Lines = _Content.splitlines()
    if _Lines and _Lines[0].strip() == "---":
        _End = next( ( _I for _I, _L in enumerate( _Lines[1:], 1 ) if _L.strip() == "---" ), -1 )
        if _End > 0:
            for _L in _Lines[1:_End]:
                if _L.startswith( "last_updated:" ):
                    _LastUpdated = _L.split( ":", 1 )[1].strip()

    # 萃取 todo 行
    _Pending   = []
    _Completed = []
    for _L in _Lines:
        _Stripped = _L.strip()
        if _Stripped.startswith( "- [ ]" ):
            _Pending.append( _Stripped[6:].strip() )
        elif _Stripped.startswith( "- [x]" ) or _Stripped.startswith( "- [X]" ):
            _Completed.append( _Stripped[6:].strip() )

    # 萃取工作脈絡
    _ContextLines = []
    _InContext = False
    for _L in _Lines:
        if _L.startswith( "## 工作脈絡" ):
            _InContext = True
            continue
        if _InContext:
            if _L.startswith( "## " ):
                break
            _ContextLines.append( _L )
            if len( _ContextLines ) >= 15:
                break
    _ContextSummary = "\n".join( _ContextLines ).strip()

    return (
        {
            "last_updated": _LastUpdated,
            "pending_todos": _Pending,
            "completed_count": len( _Completed ),
            "context_summary": _ContextSummary,
            "path": _RelPath,
        },
        None,
    )
