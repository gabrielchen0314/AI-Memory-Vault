"""
Vault 業務邏輯層
三個模式（CLI / API / MCP）的唯一業務邏輯入口。
統一路徑驗證、.md 檢查、讀寫、搜尋、同步、寫入後自動索引。

V3 變更：
  - 不再使用 classmethod + 全域 VAULT_ROOT，改為 initialize() 注入 AppConfig。
  - 內部持有 Indexer / Retriever 實例（非每次呼叫重建）。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
import os
from typing import Optional

from config import AppConfig
from core.indexer import VaultIndexer
from core.retriever import VaultRetriever


class VaultService:
    """Vault 業務邏輯：所有對外操作的統一入口。"""

    #region 常數定義
    ALLOWED_EXTENSION: str = ".md"
    ERROR_PATH_TRAVERSAL: str = "Error: path traversal not allowed."
    ERROR_NOT_FOUND: str = "Error: file not found — {file_path}"
    ERROR_EXTENSION: str = "Error: only .md files are allowed."
    ERROR_NOT_INITIALIZED: str = "Error: VaultService not initialized. Call initialize() first."
    #endregion

    #region 類別級狀態（由 initialize 設定）
    ## <summary>Vault 根目錄絕對路徑</summary>
    m_VaultRoot: str = ""
    ## <summary>應用程式設定</summary>
    m_Config: Optional[AppConfig] = None
    ## <summary>文件索引器</summary>
    m_Indexer: Optional[VaultIndexer] = None
    ## <summary>文件檢索器</summary>
    m_Retriever: Optional[VaultRetriever] = None
    ## <summary>是否已初始化</summary>
    m_IsInitialized: bool = False
    #endregion

    #region 初始化
    @classmethod
    def initialize( cls, iConfig: AppConfig ) -> None:
        """
        注入設定，初始化內部依賴。

        Args:
            iConfig: 應用程式頂層設定。
        """
        cls.m_VaultRoot = os.path.realpath( iConfig.vault_path )
        cls.m_Config = iConfig
        cls.m_Indexer = VaultIndexer(
            cls.m_VaultRoot,
            iConfig.embedding.chunk_size,
            iConfig.embedding.chunk_overlap,
        )
        cls.m_Retriever = VaultRetriever( iConfig )
        cls.m_IsInitialized = True
    #endregion

    #region 私有方法
    @classmethod
    def _ensure_initialized( cls ) -> None:
        """確認服務已初始化。"""
        if not cls.m_IsInitialized:
            raise RuntimeError( cls.ERROR_NOT_INITIALIZED )

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

    @classmethod
    def _ensure_project_skeleton( cls, iFilePath: str ) -> bool:
        """
        偵測寫入路徑是否屬於專案目錄，若是且專案不存在則自動建立骨架。

        Args:
            iFilePath: 相對於 Vault 根目錄的檔案路徑。

        Returns:
            是否新建了專案骨架。
        """
        if cls.m_Config is None:
            return False

        _Org, _Project = cls.m_Config.paths.parse_project_path( iFilePath )
        if _Org is None or _Project is None:
            return False

        _ProjectDir = os.path.join(
            cls.m_VaultRoot,
            cls.m_Config.paths.project_dir( _Org, _Project ),
        )

        if os.path.exists( _ProjectDir ):
            return False

        # 建立專案骨架
        for _SubDir in cls.m_Config.paths.get_project_skeleton_dirs():
            os.makedirs( os.path.join( _ProjectDir, _SubDir ), exist_ok=True )

        # 同時確保組織 rules 目錄存在
        _OrgRulesDir = os.path.join(
            cls.m_VaultRoot,
            cls.m_Config.paths.org_rules_dir( _Org ),
        )
        os.makedirs( _OrgRulesDir, exist_ok=True )

        return True
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
        cls._ensure_initialized()
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

    @classmethod
    def batch_write_notes( cls, iNotes: list ) -> tuple:
        """
        批次寫入多個筆記，統一執行一次 ChromaDB 索引（比逐一 write_note 效率高）。

        Args:
            iNotes: list[dict]，每個 dict 含 'file_path': str 和 'content': str。
                    可選 'mode': 'overwrite'（預設）或 'append'。

        Returns:
            (results, batch_stats, error_message)
            results:     list[dict] 每筆寫入結果（含 file_path / chars / ok / error）。
            batch_stats: 合併的索引統計。
            error_message: 僅在整體失敗時非 None（個別失敗記錄在 results[i]['error']）。
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
            with open( _AbsPath, _WriteMode, encoding="utf-8" ) as _F:
                _F.write( _WriteContent )

            _AbsPathsToIndex.append( _AbsPath )
            _Results.append( { "file_path": _FilePath, "ok": True, "error": None, "chars": len( _Content ) } )

        # 一次批次索引所有成功寫入的檔案
        _BatchStats = cls.m_Indexer.sync_batch( _AbsPathsToIndex )

        # Git 自動提交（批次加入後一次 commit）
        if cls.m_Config and cls.m_Config.git.auto_commit and _AbsPathsToIndex:
            from services.git_service import GitService
            _Gc = cls.m_Config.git
            _Paths = " ".join(
                os.path.relpath( p, cls.m_VaultRoot ).replace( "\\", "/" )
                for p in _AbsPathsToIndex
            )
            _Msg = f"batch-write: {len(_AbsPathsToIndex)} files"
            GitService.commit(
                cls.m_VaultRoot, ".",
                _Msg,
                _Gc.author_name, _Gc.author_email,
            )

        return _Results, _BatchStats, None

    @classmethod
    def update_todo( cls, iFilePath: str, iTodoText: str, iDone: bool ) -> tuple:
        """
        在指定 .md 檔案中更新 todo 項目的勾選狀態（不全文覆蓋）。

        搜尋包含 iTodoText 的 todo 行（`- [ ] ...` 或 `- [x] ...`），
        將其勾選狀態切換至 iDone 指定的值，並重新索引。

        Args:
            iFilePath: 相對於 Vault 根目錄的 .md 檔案路徑。
            iTodoText: todo 項目文字（部分比對即可）。
            iDone:     True = 標為完成 [x]，False = 標為未完成 [ ]。

        Returns:
            (stats_dict, error_message) — 成功時 error_message 為 None。
            stats_dict 含 'matched' (bool) 和 'updated_line'。
        """
        cls._ensure_initialized()

        _AbsPath, _PathErr = cls._validate_path( iFilePath )
        if _PathErr:
            return None, _PathErr

        if not os.path.isfile( _AbsPath ):
            return None, cls.ERROR_NOT_FOUND.format( file_path=iFilePath )

        with open( _AbsPath, "r", encoding="utf-8" ) as _F:
            _Lines = _F.readlines()

        _Matched = False
        _UpdatedLine = ""
        _NewState = "[x]" if iDone else "[ ]"
        _OldState = "[ ]" if iDone else "[x]"

        for _Idx, _Line in enumerate( _Lines ):
            # 比對包含 todo 關鍵字的 checkbox 行
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

    @classmethod
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

    @classmethod
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
            iQuery:    搜尋文字。
            iCategory: 過濾分類。
            iDocType:  過濾文件類型。
            iMode:     搜尋模式（"keyword" / "semantic" / ""）。

        Returns:
            格式化搜尋結果字串。
        """
        cls._ensure_initialized()
        return cls.m_Retriever.search_formatted( iQuery, iCategory, iDocType, iMode )

    @classmethod
    def sync( cls ) -> dict:
        """
        執行全量增量同步。

        Returns:
            統計結果字典。
        """
        cls._ensure_initialized()
        return cls.m_Indexer.sync()
    @classmethod
    def delete_note( cls, iFilePath: str ) -> tuple:
        """
        刪除 Vault 中的指定 .md 檔案，並移除 ChromaDB 中對應的所有向量記錄。

        Args:
            iFilePath: 相對於 Vault 根目錄的 .md 檔案路徑。

        Returns:
            (stats_dict, error_message) — 成功時 error_message 為 None。
            stats_dict 含 'file_path' 和 'deleted_chunks'。
        """
        cls._ensure_initialized()

        _AbsPath, _Error = cls._validate_write_path( iFilePath )
        if _Error:
            return None, _Error

        if not os.path.isfile( _AbsPath ):
            return None, cls.ERROR_NOT_FOUND.format( file_path=iFilePath )

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

    @classmethod
    def check_integrity( cls ) -> tuple:
        """
        比對 ChromaDB 已索引的 source 路徑與 Vault 檔案系統，
        找出孤立記錄（DB 中存在但對應 .md 檔案已刪除）。

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

    @classmethod
    def get_project_status( cls, iOrg: str, iProject: str ) -> tuple:
        """
        讀取指定專案的 status.md 並回傳結構化資料。

        Args:
            iOrg:     組織名稱。
            iProject: 專案名稱。

        Returns:
            ({last_updated, pending_todos, completed_todos, context_lines, path}, error)
        """
        cls._ensure_initialized()

        _RelPath = cls.m_Config.paths.project_status_file( iOrg, iProject )
        _Content, _Err = cls.read_note( _RelPath )
        if _Err:
            return ( None, _Err )
        if not _Content:
            return ( None, cls.ERROR_NOT_FOUND.format( file_path=_RelPath ) )

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

        # 萃取工作脈絡第一段（## 工作脈絡 區塊前 10 行）
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
    #endregion
