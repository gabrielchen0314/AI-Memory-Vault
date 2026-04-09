"""
筆記 CRUD + Todo 操作
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


def read_note( cls, iFilePath: str ) -> tuple:
    """
    讀取 Vault 中指定筆記的完整原始內容。

    Args:
        cls:       VaultService class。
        iFilePath: 相對於 Vault 根目錄的檔案路徑。

    Returns:
        (content, error_message) — 成功時 error_message 為 None。
    """
    cls._ensure_initialized()
    _AbsPath, _Error = cls._validate_path( iFilePath )
    if _Error:
        return None, _Error

    if not os.path.isfile( _AbsPath ):
        return None, f"Error: file not found — {iFilePath}"

    try:
        with open( _AbsPath, "r", encoding="utf-8" ) as _F:
            return _F.read(), None
    except OSError as _E:
        return None, f"Error reading file: {_E}"


def write_note( cls, iFilePath: str, iContent: str, iMode: str = "overwrite" ) -> tuple:
    """
    寫入或更新 Vault 中的筆記檔案，並自動索引至向量庫。

    Args:
        cls:       VaultService class。
        iFilePath: 相對於 Vault 根目錄的檔案路徑。
        iContent:  要寫入的內容。
        iMode:     寫入模式。'overwrite' = 覆寫；'append' = 追加。

    Returns:
        (stats_dict, error_message) — 成功時 error_message 為 None。
    """
    cls._ensure_initialized()
    _AbsPath, _Error = cls._validate_write_path( iFilePath )
    if _Error:
        return None, _Error

    # 自動偵測並建立專案骨架
    _IsNewProject = cls._ensure_project_skeleton( iFilePath )

    _Dir = os.path.dirname( _AbsPath )
    if not os.path.exists( _Dir ):
        os.makedirs( _Dir, exist_ok=True )

    _WriteMode = "a" if iMode == "append" else "w"
    _WriteContent = ( "\n" + iContent ) if iMode == "append" else iContent
    with open( _AbsPath, _WriteMode, encoding="utf-8" ) as _F:
        _F.write( _WriteContent )

    # 寫入後自動索引（單檔增量）
    _Stats = cls.m_Indexer.sync_single( _AbsPath )

    # Git 自動提交（若已啟用）
    if cls.m_Config and cls.m_Config.git.auto_commit:
        from services.git_service import GitService
        _Gc = cls.m_Config.git
        GitService.commit(
            cls.m_VaultRoot, iFilePath,
            f"write: {iFilePath}",
            _Gc.author_name, _Gc.author_email,
        )

    return {
        "file_path": iFilePath,
        "chars": len( iContent ),
        "mode": iMode,
        "new_project": _IsNewProject,
        "index_stats": _Stats["index_stats"],
        "total_chunks": _Stats["total_chunks"],
    }, None


def batch_write_notes( cls, iNotes: list ) -> tuple:
    """
    批次寫入多個筆記，統一執行一次 ChromaDB 索引。

    Args:
        cls:    VaultService class。
        iNotes: list[dict]，每個 dict 含 'file_path': str 和 'content': str。
                可選 'mode': 'overwrite'（預設）或 'append'。

    Returns:
        (results, batch_stats, error_message)
    """
    cls._ensure_initialized()

    _Results = []
    _AbsPathsToIndex = []

    for _Note in iNotes:
        _FilePath = _Note.get( "file_path", "" )
        _Content = _Note.get( "content", "" )
        _Mode = _Note.get( "mode", "overwrite" )

        _AbsPath, _PathErr = cls._validate_write_path( _FilePath )
        if _PathErr:
            _Results.append( { "file_path": _FilePath, "ok": False, "error": _PathErr, "chars": 0 } )
            continue

        cls._ensure_project_skeleton( _FilePath )

        _Dir = os.path.dirname( _AbsPath )
        if _Dir:
            os.makedirs( _Dir, exist_ok=True )

        _WriteMode = "a" if _Mode == "append" else "w"
        _WriteContent = ( "\n" + _Content ) if _Mode == "append" else _Content
        try:
            with open( _AbsPath, _WriteMode, encoding="utf-8" ) as _F:
                _F.write( _WriteContent )
        except OSError as _E:
            _Results.append( { "file_path": _FilePath, "ok": False, "error": str( _E ), "chars": 0 } )
            continue

        _AbsPathsToIndex.append( _AbsPath )
        _Results.append( { "file_path": _FilePath, "ok": True, "error": None, "chars": len( _Content ) } )

    # 一次批次索引所有成功寫入的檔案
    _BatchStats = cls.m_Indexer.sync_batch( _AbsPathsToIndex )

    # Git 自動提交（批次加入後一次 commit）
    if cls.m_Config and cls.m_Config.git.auto_commit and _AbsPathsToIndex:
        from services.git_service import GitService
        _Gc = cls.m_Config.git
        _Msg = f"batch-write: {len(_AbsPathsToIndex)} files"
        GitService.commit(
            cls.m_VaultRoot, ".",
            _Msg,
            _Gc.author_name, _Gc.author_email,
        )

    return _Results, _BatchStats, None


def edit_note( cls, iFilePath: str, iOldText: str, iNewText: str ) -> tuple:
    """
    在指定 .md 檔案中執行精確的文字替換（不全文覆寫）。

    Args:
        cls:       VaultService class。
        iFilePath: 相對於 Vault 根目錄的 .md 路徑。
        iOldText:  要被替換的原始文字（必須唯一出現）。
        iNewText:  替換後的新文字。

    Returns:
        (stats_dict, error_message)
    """
    cls._ensure_initialized()
    _AbsPath, _Err = cls._validate_write_path( iFilePath )
    if _Err:
        return None, _Err

    if not os.path.isfile( _AbsPath ):
        return None, f"Error: file not found — {iFilePath}"

    with open( _AbsPath, "r", encoding="utf-8" ) as _F:
        _Content = _F.read()

    _Count = _Content.count( iOldText )
    if _Count == 0:
        return None, "Error: old_text not found in file."
    if _Count > 1:
        return None, f"Error: old_text found {_Count} times; expected exactly 1."

    _NewContent = _Content.replace( iOldText, iNewText, 1 )
    with open( _AbsPath, "w", encoding="utf-8" ) as _F:
        _F.write( _NewContent )

    _Stats = cls.m_Indexer.sync_single( _AbsPath )

    if cls.m_Config and cls.m_Config.git.auto_commit:
        from services.git_service import GitService
        _Gc = cls.m_Config.git
        GitService.commit(
            cls.m_VaultRoot, iFilePath,
            f"edit: {iFilePath}",
            _Gc.author_name, _Gc.author_email,
        )

    return {
        "file_path": iFilePath,
        "chars_removed": len( iOldText ),
        "chars_added": len( iNewText ),
        "index_stats": _Stats["index_stats"],
        "total_chunks": _Stats["total_chunks"],
    }, None


def delete_note( cls, iFilePath: str ) -> tuple:
    """
    刪除 Vault 中的指定 .md 檔案，並移除 ChromaDB 中對應的所有向量記錄。

    Args:
        cls:       VaultService class。
        iFilePath: 相對於 Vault 根目錄的 .md 檔案路徑。

    Returns:
        (stats_dict, error_message) — 成功時 error_message 為 None。
    """
    cls._ensure_initialized()

    _AbsPath, _Error = cls._validate_write_path( iFilePath )
    if _Error:
        return None, _Error

    if not os.path.isfile( _AbsPath ):
        return None, f"Error: file not found — {iFilePath}"

    os.remove( _AbsPath )

    _Stats = cls.m_Indexer.delete_source( _AbsPath )

    # Git 自動提交（刪除後）
    if cls.m_Config and cls.m_Config.git.auto_commit:
        from services.git_service import GitService
        _Gc = cls.m_Config.git
        GitService.commit(
            cls.m_VaultRoot, iFilePath,
            f"delete: {iFilePath}",
            _Gc.author_name, _Gc.author_email,
        )

    return {
        "file_path": iFilePath,
        "deleted_chunks": _Stats["index_stats"]["num_deleted"],
    }, None


def rename_note( cls, iOldPath: str, iNewPath: str ) -> tuple:
    """
    將 Vault 中的 .md 檔案移動（重新命名）到新路徑，
    同步更新 ChromaDB 向量索引。

    Args:
        cls:      VaultService class。
        iOldPath: 來源相對路徑。
        iNewPath: 目標相對路徑。

    Returns:
        (stats_dict, error_message)
    """
    cls._ensure_initialized()

    # 驗證兩條路徑
    _OldAbs, _OldErr = cls._validate_write_path( iOldPath )
    if _OldErr:
        return None, _OldErr

    _NewAbs, _NewErr = cls._validate_write_path( iNewPath )
    if _NewErr:
        return None, _NewErr

    if not os.path.isfile( _OldAbs ):
        return None, f"Error: file not found — {iOldPath}"

    if os.path.isfile( _NewAbs ):
        return None, f"Error: destination already exists — {iNewPath}"

    try:
        _NewDir = os.path.dirname( _NewAbs )
        os.makedirs( _NewDir, exist_ok=True )

        os.rename( _OldAbs, _NewAbs )

        _DeleteStats = cls.m_Indexer.delete_source( _OldAbs )
        _DeletedChunks = _DeleteStats["index_stats"]["num_deleted"]

        _IndexStats = cls.m_Indexer.sync_single( _NewAbs )
        _IndexedChunks = _IndexStats["total_chunks"]

        if cls.m_Config and cls.m_Config.git.auto_commit:
            from services.git_service import GitService
            _Gc = cls.m_Config.git
            GitService.commit(
                cls.m_VaultRoot, iNewPath,
                f"rename: {iOldPath} → {iNewPath}",
                _Gc.author_name, _Gc.author_email,
            )

        return (
            {
                "old_path": iOldPath,
                "new_path": iNewPath,
                "deleted_chunks": _DeletedChunks,
                "indexed_chunks": _IndexedChunks,
            },
            None,
        )
    except OSError as _Ex:
        return None, f"Error: {_Ex}"


def list_notes( cls, iPath: str = "", iRecursive: bool = False ) -> tuple:
    """
    列出指定目錄下的所有 .md 檔案（不含隱藏目錄）。

    Args:
        cls:        VaultService class。
        iPath:      相對於 Vault 根目錄的目錄路徑。
        iRecursive: True = 遞迴。

    Returns:
        ({path, recursive, total, notes}, error)
    """
    cls._ensure_initialized()
    try:
        if iPath:
            _AbsDir, _Err = cls._validate_path( iPath )
            if _Err:
                return None, _Err
        else:
            _AbsDir = cls.m_VaultRoot

        if not os.path.isdir( _AbsDir ):
            return None, f"Error: directory not found — {iPath}"

        _Notes = []
        if iRecursive:
            for _Root, _Dirs, _Files in os.walk( _AbsDir ):
                _Dirs[:] = sorted( d for d in _Dirs if not d.startswith( "." ) )
                for _F in sorted( _Files ):
                    if _F.endswith( ".md" ):
                        _Abs  = os.path.join( _Root, _F )
                        _Rel  = os.path.relpath( _Abs, cls.m_VaultRoot ).replace( os.sep, "/" )
                        _Stat = os.stat( _Abs )
                        _Notes.append( {
                            "path":     _Rel,
                            "size":     _Stat.st_size,
                            "modified": _Stat.st_mtime,
                        } )
        else:
            for _F in sorted( os.listdir( _AbsDir ) ):
                if _F.endswith( ".md" ):
                    _Abs  = os.path.join( _AbsDir, _F )
                    _Rel  = os.path.relpath( _Abs, cls.m_VaultRoot ).replace( os.sep, "/" )
                    _Stat = os.stat( _Abs )
                    _Notes.append( {
                        "path":     _Rel,
                        "size":     _Stat.st_size,
                        "modified": _Stat.st_mtime,
                    } )

        return (
            {
                "path":      iPath or "/",
                "recursive": iRecursive,
                "total":     len( _Notes ),
                "notes":     _Notes,
            },
            None,
        )
    except Exception as _Ex:
        return None, str( _Ex )


# ── Todo 操作 ─────────────────────────────────────────────

def update_todo( cls, iFilePath: str, iTodoText: str, iDone: bool ) -> tuple:
    """
    在指定 .md 檔案中更新 todo 項目的勾選狀態。

    Args:
        cls:       VaultService class。
        iFilePath: 相對於 Vault 根目錄的 .md 檔案路徑。
        iTodoText: todo 項目文字（部分比對即可）。
        iDone:     True = 標為完成 [x]，False = 標為未完成 [ ]。

    Returns:
        (stats_dict, error_message)
    """
    cls._ensure_initialized()

    _AbsPath, _PathErr = cls._validate_path( iFilePath )
    if _PathErr:
        return None, _PathErr

    if not os.path.isfile( _AbsPath ):
        return None, f"Error: file not found — {iFilePath}"

    with open( _AbsPath, "r", encoding="utf-8" ) as _F:
        _Lines = _F.readlines()

    _Matched = False
    _UpdatedLine = ""
    _NewState = "[x]" if iDone else "[ ]"
    _OldState = "[ ]" if iDone else "[x]"

    for _Idx, _Line in enumerate( _Lines ):
        if iTodoText in _Line and ( "- [ ]" in _Line or "- [x]" in _Line ):
            _Lines[_Idx] = _Line.replace( f"- {_OldState}", f"- {_NewState}", 1 )
            _UpdatedLine = _Lines[_Idx].rstrip()
            _Matched = True
            break

    if not _Matched:
        return { "matched": False, "updated_line": "" }, None

    with open( _AbsPath, "w", encoding="utf-8" ) as _F:
        _F.writelines( _Lines )

    _IndexStats = cls.m_Indexer.sync_single( _AbsPath )

    return {
        "matched": True,
        "updated_line": _UpdatedLine,
        "index_stats": _IndexStats["index_stats"],
        "total_chunks": _IndexStats["total_chunks"],
    }, None


def add_todo( cls, iFilePath: str, iTodoText: str, iSection: str = "" ) -> tuple:
    """
    在指定 .md 檔案中新增一個 todo 項目。

    Args:
        cls:       VaultService class。
        iFilePath: 相對於 Vault 根目錄的 .md 路徑。
        iTodoText: todo 內容文字。
        iSection:  插入到哪個 section 標題下（空字串 = 檔案末尾）。

    Returns:
        (stats_dict, error_message)
    """
    cls._ensure_initialized()
    _AbsPath, _Err = cls._validate_write_path( iFilePath )
    if _Err:
        return None, _Err

    if not os.path.isfile( _AbsPath ):
        return None, f"Error: file not found — {iFilePath}"

    _NewLine = f"- [ ] {iTodoText}\n"

    with open( _AbsPath, "r", encoding="utf-8" ) as _F:
        _Lines = _F.readlines()

    if iSection:
        _Inserted = False
        for _Idx, _Line in enumerate( _Lines ):
            if _Line.strip().startswith( "#" ) and iSection.lower() in _Line.lower():
                _InsertIdx = _Idx + 1
                while _InsertIdx < len( _Lines ):
                    _Stripped = _Lines[_InsertIdx].strip()
                    if _Stripped.startswith( "- [ ]" ) or _Stripped.startswith( "- [x]" ) or _Stripped.startswith( "- [X]" ):
                        _InsertIdx += 1
                    elif _Stripped == "":
                        _InsertIdx += 1
                    else:
                        break
                _Lines.insert( _InsertIdx, _NewLine )
                _Inserted = True
                break
        if not _Inserted:
            _Lines.append( _NewLine )
    else:
        _Lines.append( _NewLine )

    with open( _AbsPath, "w", encoding="utf-8" ) as _F:
        _F.writelines( _Lines )

    _Stats = cls.m_Indexer.sync_single( _AbsPath )
    return {
        "file_path": iFilePath,
        "added_todo": iTodoText,
        "index_stats": _Stats["index_stats"],
        "total_chunks": _Stats["total_chunks"],
    }, None


def remove_todo( cls, iFilePath: str, iTodoText: str ) -> tuple:
    """
    從指定 .md 檔案中移除包含指定文字的 todo 行。

    Args:
        cls:       VaultService class。
        iFilePath: 相對於 Vault 根目錄的 .md 路徑。
        iTodoText: 要移除的 todo 文字（部分比對）。

    Returns:
        (stats_dict, error_message)
    """
    cls._ensure_initialized()
    _AbsPath, _Err = cls._validate_write_path( iFilePath )
    if _Err:
        return None, _Err

    if not os.path.isfile( _AbsPath ):
        return None, f"Error: file not found — {iFilePath}"

    with open( _AbsPath, "r", encoding="utf-8" ) as _F:
        _Lines = _F.readlines()

    _RemovedLine = ""
    _NewLines = []
    for _Line in _Lines:
        _Stripped = _Line.strip()
        if ( iTodoText in _Line
             and ( _Stripped.startswith( "- [ ]" ) or _Stripped.startswith( "- [x]" ) or _Stripped.startswith( "- [X]" ) )
             and not _RemovedLine ):
            _RemovedLine = _Stripped
            continue
        _NewLines.append( _Line )

    if not _RemovedLine:
        return { "matched": False, "removed_line": "" }, None

    with open( _AbsPath, "w", encoding="utf-8" ) as _F:
        _F.writelines( _NewLines )

    _Stats = cls.m_Indexer.sync_single( _AbsPath )
    return {
        "matched": True,
        "removed_line": _RemovedLine,
        "index_stats": _Stats["index_stats"],
        "total_chunks": _Stats["total_chunks"],
    }, None
