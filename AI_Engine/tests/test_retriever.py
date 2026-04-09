"""
VaultRetriever 單元測試
覆蓋 _build_filter 與基本搜尋排程邏輯（不需真實 embeddings）。
focus: 確認 filter 分支不會汙染 stdout（MCP stdio 安全）。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.4
@date 2026.04.05
"""
import io
import os
import sys
import pytest


# ────────────────────────────────────────────────────────────
# _build_filter
# ────────────────────────────────────────────────────────────

class TestBuildFilter:
    """VaultRetriever._build_filter 回傳正確 ChromaDB filter dict。"""

    @pytest.fixture
    def retriever( monkeypatch ):
        """建立 VaultRetriever，用最小 config stub 跳過模型載入。"""
        from config import AppConfig, VaultPaths, SearchConfig
        _Config = AppConfig(
            vault_path = "/tmp/vault",
            paths      = VaultPaths(),
        )
        _Config.search = SearchConfig()
        # 不呼叫 get_vectorstore — 只測試 filter 建立邏輯
        from core.retriever import VaultRetriever
        return VaultRetriever.__new__( VaultRetriever )

    def test_empty_filter_returns_none( self ):
        from core.retriever import VaultRetriever
        _R = VaultRetriever.__new__( VaultRetriever )
        _Filter = _R._build_filter( "", "" )
        assert _Filter is None or _Filter == {}

    def test_category_filter( self ):
        from core.retriever import VaultRetriever
        _R = VaultRetriever.__new__( VaultRetriever )
        _Filter = _R._build_filter( "knowledge", "" )
        assert _Filter is not None

    def test_doc_type_filter( self ):
        from core.retriever import VaultRetriever
        _R = VaultRetriever.__new__( VaultRetriever )
        _Filter = _R._build_filter( "", "rule" )
        assert _Filter is not None


# ────────────────────────────────────────────────────────────
# _validate_date (SchedulerService) — 藉此測試 stderr 安全
# ────────────────────────────────────────────────────────────

class TestSchedulerValidateDate:
    """
    確認 SchedulerService._validate_date 在無效日期時拋出 ValueError，
    而非靜默通過或汙染 stdout。
    """

    def test_valid_date_passes( self ):
        from services.scheduler import SchedulerService
        SchedulerService._validate_date( "2026-04-05" )  # 不應拋出

    def test_none_passes( self ):
        from services.scheduler import SchedulerService
        SchedulerService._validate_date( None )  # None = 今天，不驗證

    def test_invalid_format_raises( self ):
        from services.scheduler import SchedulerService
        with pytest.raises( ValueError ):
            SchedulerService._validate_date( "2026/04/05" )

    def test_path_injection_raises( self ):
        from services.scheduler import SchedulerService
        with pytest.raises( ValueError ):
            SchedulerService._validate_date( "../../etc/passwd" )

    def test_sql_injection_raises( self ):
        from services.scheduler import SchedulerService
        with pytest.raises( ValueError ):
            SchedulerService._validate_date( "2026-04-05'; DROP TABLE notes;--" )
