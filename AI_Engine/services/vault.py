"""
Vault 業務邏輯層（Facade）
三個模式（CLI / API / MCP）的唯一業務邏輯入口。
統一路徑驗證、.md 檢查、讀寫、搜尋、同步、寫入後自動索引。

V3.5 變更：
  - 新增 threading.Lock 保護 initialize / _ensure_initialized（C-3 修復）。
  - 統一使用 core.logger（取代 print / 硬編碼錯誤字串）。
  - 新增 grep / edit_note / add_todo / remove_todo 方法（Phase 5 功能）。

V3.6 變更：
  - 從 God Object（982 行）重構為 Facade + 內部委派。
  - 實作拆分至 services/_vault/（note_ops, search_ops, index_ops）。
  - 本檔僅保留共用基礎設施 + 公開方法委派（~200 行）。
  - 外部呼叫者零修改：from services.vault import VaultService 繼續有效。

@author gabrielchen
@version 3.6
@since AI-Memory-Vault 3.0
@date 2026.04.10
"""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Optional

from filelock import FileLock

from config import AppConfig, DATA_DIR
from core.logger import get_logger
from core.errors import (
    VaultError, PathTraversalError, FileNotFoundError_,
    ExtensionError, NotInitializedError, NoteAlreadyExistsError,
    EditMatchError,
)

_logger = get_logger( __name__ )

## <summary>跨程序檔案鎖（保護多 Editor 並發寫入）</summary>
_VAULT_LOCK_PATH = str( DATA_DIR / "vault.lock" )
_VAULT_FILE_LOCK = FileLock( _VAULT_LOCK_PATH, timeout=30 )


class VaultService:
    """Vault 業務邏輯：所有對外操作的統一入口（Facade）。"""

    #region 常數定義
    ALLOWED_EXTENSION: str = ".md"
    ERROR_PATH_TRAVERSAL: str = "Error: path traversal not allowed."
    ERROR_EXTENSION: str = "Error: only .md files are allowed."
    #endregion

    #region 類別級狀態（由 initialize 設定）
    ## <summary>執行緒鎖（保護 initialize / _ensure_initialized）</summary>
    _lock: threading.Lock = threading.Lock()
    ## <summary>Vault 根目錄絕對路徑</summary>
    m_VaultRoot: str = ""
    ## <summary>應用程式設定</summary>
    m_Config: Optional[AppConfig] = None
    ## <summary>文件索引器</summary>
    m_Indexer = None
    ## <summary>文件檢索器</summary>
    m_Retriever = None
    ## <summary>是否已初始化</summary>
    m_IsInitialized: bool = False
    ## <summary>寫入後 hook 回呼列表 — Callable[[str], None]，參數為 Vault 相對路徑</summary>
    _post_write_hooks: list = []
    #endregion

    #region 初始化
    @classmethod
    def initialize( cls, iConfig: AppConfig ) -> None:
        """
        注入設定，初始化內部依賴。執行緒安全。

        Args:
            iConfig: 應用程式頂層設定。
        """
        with cls._lock:
            from core.indexer import VaultIndexer
            from core.retriever import VaultRetriever

            cls.m_VaultRoot = os.path.realpath( iConfig.vault_path )
            cls.m_Config = iConfig
            cls.m_Indexer = VaultIndexer(
                cls.m_VaultRoot,
                iConfig.embedding.chunk_size,
                iConfig.embedding.chunk_overlap,
            )
            cls.m_Retriever = VaultRetriever( iConfig )
            cls.m_IsInitialized = True
            _logger.info( "VaultService initialized — vault=%s", cls.m_VaultRoot )
    #endregion

    #region 共用基礎設施（子模組透過 cls 存取）
    @classmethod
    def _ensure_initialized( cls ) -> None:
        """確認服務已初始化（執行緒安全）。"""
        if not cls.m_IsInitialized:
            raise NotInitializedError( "VaultService" )

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
        _VaultPrefix = cls.m_VaultRoot.rstrip( os.sep ) + os.sep
        if not ( _AbsPath + os.sep ).startswith( _VaultPrefix ):
            return None, "Error: path traversal not allowed."

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
            return None, "Error: only .md files are allowed."

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

    @classmethod
    def _invalidate_bm25_cache( cls ) -> None:
        """使 Retriever 的 BM25 全量語料快取失效，下次搜尋時自動重建。"""
        if cls.m_Retriever is not None and hasattr( cls.m_Retriever, "invalidate_bm25_cache" ):
            cls.m_Retriever.invalidate_bm25_cache()

    @classmethod
    def register_post_write_hook( cls, iCallback ) -> None:
        """
        註冊寫入後 hook。每次成功 write / batch_write / edit 後依序呼叫。
        callback 簽名：(rel_path: str) -> None。

        Args:
            iCallback: 回呼函式，接收 Vault 相對路徑。
        """
        if iCallback not in cls._post_write_hooks:
            cls._post_write_hooks.append( iCallback )

    @classmethod
    def unregister_post_write_hook( cls, iCallback ) -> None:
        """移除已註冊的寫入後 hook。"""
        try:
            cls._post_write_hooks.remove( iCallback )
        except ValueError:
            pass

    @classmethod
    def _fire_post_write_hooks( cls, iRelPath: str ) -> None:
        """觸發所有已註冊的 post-write hooks（靜默失敗）。"""
        for _Hook in cls._post_write_hooks:
            try:
                _Hook( iRelPath )
            except Exception as _Err:
                _logger.warning( f"Post-write hook error ({_Hook.__name__}): {_Err}" )

    @staticmethod
    @contextmanager
    def _write_lock():
        """取得跨程序寫入鎖（多 Editor 並發保護）。"""
        try:
            _VAULT_FILE_LOCK.acquire()
            yield
        finally:
            _VAULT_FILE_LOCK.release()
    #endregion

    #region 公開方法（Facade — 委派至 services/_vault/ 子模組）

    # ── 筆記 CRUD ──────────────────────────────────────────

    @classmethod
    def read_note( cls, iFilePath: str ) -> tuple:
        """讀取 Vault 中指定筆記的完整原始內容。"""
        from services._vault.note_ops import read_note
        return read_note( cls, iFilePath )

    @classmethod
    def write_note( cls, iFilePath: str, iContent: str, iMode: str = "overwrite" ) -> tuple:
        """寫入或更新 Vault 中的筆記檔案，並自動索引至向量庫。"""
        from services._vault.note_ops import write_note
        with cls._write_lock():
            _Result = write_note( cls, iFilePath, iContent, iMode )
        cls._invalidate_bm25_cache()
        if _Result[1] is None:  # 寫入成功
            cls._fire_post_write_hooks( iFilePath )
        return _Result

    @classmethod
    def batch_write_notes( cls, iNotes: list ) -> tuple:
        """批次寫入多個筆記，統一執行一次 ChromaDB 索引。"""
        from services._vault.note_ops import batch_write_notes
        with cls._write_lock():
            _Result = batch_write_notes( cls, iNotes )
        cls._invalidate_bm25_cache()
        _ItemResults = _Result[0] if _Result[0] else []
        for _Item in _ItemResults:
            if _Item.get( "ok" ):
                cls._fire_post_write_hooks( _Item["file_path"] )
        return _Result

    @classmethod
    def edit_note( cls, iFilePath: str, iOldText: str, iNewText: str ) -> tuple:
        """在指定 .md 檔案中執行精確的文字替換（不全文覆寫）。"""
        from services._vault.note_ops import edit_note
        with cls._write_lock():
            _Result = edit_note( cls, iFilePath, iOldText, iNewText )
        cls._invalidate_bm25_cache()
        if _Result[1] is None:
            cls._fire_post_write_hooks( iFilePath )
        return _Result

    @classmethod
    def delete_note( cls, iFilePath: str ) -> tuple:
        """刪除 Vault 中的指定 .md 檔案，並移除 ChromaDB 中對應的向量記錄。"""
        from services._vault.note_ops import delete_note
        with cls._write_lock():
            _Result = delete_note( cls, iFilePath )
        cls._invalidate_bm25_cache()
        return _Result

    @classmethod
    def rename_note( cls, iOldPath: str, iNewPath: str ) -> tuple:
        """將 Vault 中的 .md 檔案移動到新路徑，同步更新 ChromaDB 索引。"""
        from services._vault.note_ops import rename_note
        with cls._write_lock():
            _Result = rename_note( cls, iOldPath, iNewPath )
        cls._invalidate_bm25_cache()
        return _Result

    @classmethod
    def list_notes( cls, iPath: str = "", iRecursive: bool = False ) -> tuple:
        """列出指定目錄下的所有 .md 檔案。"""
        from services._vault.note_ops import list_notes
        return list_notes( cls, iPath, iRecursive )

    @classmethod
    def list_projects( cls ) -> tuple:
        """列出所有組織及其下的專案清單。"""
        from services._vault.note_ops import list_projects
        return list_projects( cls )

    # ── Todo ───────────────────────────────────────────────

    @classmethod
    def update_todo( cls, iFilePath: str, iTodoText: str, iDone: bool ) -> tuple:
        """在指定 .md 檔案中更新 todo 項目的勾選狀態。"""
        from services._vault.note_ops import update_todo
        return update_todo( cls, iFilePath, iTodoText, iDone )

    @classmethod
    def add_todo( cls, iFilePath: str, iTodoText: str, iSection: str = "" ) -> tuple:
        """在指定 .md 檔案中新增一個 todo 項目。"""
        from services._vault.note_ops import add_todo
        return add_todo( cls, iFilePath, iTodoText, iSection )

    @classmethod
    def remove_todo( cls, iFilePath: str, iTodoText: str ) -> tuple:
        """從指定 .md 檔案中移除包含指定文字的 todo 行。"""
        from services._vault.note_ops import remove_todo
        return remove_todo( cls, iFilePath, iTodoText )

    # ── 搜尋 ──────────────────────────────────────────────

    @classmethod
    def search(
        cls,
        iQuery: str,
        iCategory: str = "",
        iDocType: str = "",
        iTopK: Optional[int] = None,
        iMode: str = "",
    ) -> list:
        """執行語意搜尋。"""
        from services._vault.search_ops import search
        return search( cls, iQuery, iCategory, iDocType, iTopK, iMode )

    @classmethod
    def search_formatted(
        cls,
        iQuery: str,
        iCategory: str = "",
        iDocType: str = "",
        iMode: str = "",
    ) -> str:
        """執行語意搜尋，回傳格式化文字。"""
        from services._vault.search_ops import search_formatted
        return search_formatted( cls, iQuery, iCategory, iDocType, iMode )

    @classmethod
    def grep( cls, iPattern: str, iPath: str = "", iIsRegex: bool = False, iMaxResults: int = 50 ) -> tuple:
        """在 Vault .md 檔案中執行純文字或正規表達式搜尋。"""
        from services._vault.search_ops import grep
        return grep( cls, iPattern, iPath, iIsRegex, iMaxResults )

    # ── 索引管理 ──────────────────────────────────────────

    @classmethod
    def sync( cls ) -> dict:
        """執行全量增量同步。"""
        from services._vault.index_ops import sync
        with cls._write_lock():
            _Result = sync( cls )
        cls._invalidate_bm25_cache()
        return _Result

    @classmethod
    def check_integrity( cls ) -> tuple:
        """比對 ChromaDB 與 Vault 檔案系統，找出孤立記錄。"""
        from services._vault.index_ops import check_integrity
        return check_integrity( cls )

    @classmethod
    def clean_orphans( cls ) -> tuple:
        """移除 ChromaDB 中所有孤立向量記錄。"""
        from services._vault.index_ops import clean_orphans
        return clean_orphans( cls )

    @classmethod
    def get_project_status( cls, iOrg: str, iProject: str ) -> tuple:
        """讀取指定專案的 status.md 並回傳結構化資料。"""
        from services._vault.index_ops import get_project_status
        return get_project_status( cls, iOrg, iProject )

    #endregion
