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
from typing import Optional

from config import AppConfig
from core.logger import get_logger
from core.errors import (
    VaultError, PathTraversalError, FileNotFoundError_,
    ExtensionError, NotInitializedError, NoteAlreadyExistsError,
    EditMatchError,
)

_logger = get_logger( __name__ )


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
        return write_note( cls, iFilePath, iContent, iMode )

    @classmethod
    def batch_write_notes( cls, iNotes: list ) -> tuple:
        """批次寫入多個筆記，統一執行一次 ChromaDB 索引。"""
        from services._vault.note_ops import batch_write_notes
        return batch_write_notes( cls, iNotes )

    @classmethod
    def edit_note( cls, iFilePath: str, iOldText: str, iNewText: str ) -> tuple:
        """在指定 .md 檔案中執行精確的文字替換（不全文覆寫）。"""
        from services._vault.note_ops import edit_note
        return edit_note( cls, iFilePath, iOldText, iNewText )

    @classmethod
    def delete_note( cls, iFilePath: str ) -> tuple:
        """刪除 Vault 中的指定 .md 檔案，並移除 ChromaDB 中對應的向量記錄。"""
        from services._vault.note_ops import delete_note
        return delete_note( cls, iFilePath )

    @classmethod
    def rename_note( cls, iOldPath: str, iNewPath: str ) -> tuple:
        """將 Vault 中的 .md 檔案移動到新路徑，同步更新 ChromaDB 索引。"""
        from services._vault.note_ops import rename_note
        return rename_note( cls, iOldPath, iNewPath )

    @classmethod
    def list_notes( cls, iPath: str = "", iRecursive: bool = False ) -> tuple:
        """列出指定目錄下的所有 .md 檔案。"""
        from services._vault.note_ops import list_notes
        return list_notes( cls, iPath, iRecursive )

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
        return sync( cls )

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
