"""
BackupService 單元測試。
測試 ChromaDB 備份建立、清理舊備份、列表查詢。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.7
@date 2026.04.10
"""
import os
import time

import pytest


# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────

@pytest.fixture
def backup_env( tmp_path, monkeypatch ):
    """建立最小備份測試環境：chroma_db/ + 暫時 BACKUP_DIR。"""
    # 建立假 ChromaDB 目錄
    _ChromaDir = tmp_path / "chroma_db"
    _ChromaDir.mkdir()
    ( _ChromaDir / "chroma.sqlite3" ).write_bytes( b"fake-chroma-data-12345" )
    _SubDir = _ChromaDir / "sub"
    _SubDir.mkdir()
    ( _SubDir / "segment.bin" ).write_bytes( b"segment-data" )

    # 導向 BACKUP_DIR 到 tmp
    _BackupDir = tmp_path / "backups"
    import services.backup as _Mod
    monkeypatch.setattr( _Mod, "BACKUP_DIR", _BackupDir )

    # 建立 config，patch get_chroma_path 直接回傳絕對路徑
    from config import AppConfig, VaultPaths, DatabaseConfig
    _DbConfig = DatabaseConfig()
    monkeypatch.setattr( _DbConfig, "get_chroma_path", lambda: str( _ChromaDir ) )
    _Config = AppConfig(
        vault_path=str( tmp_path / "vault" ),
        paths=VaultPaths(),
        database=_DbConfig,
    )

    from services.backup import BackupService
    return {
        "config":     _Config,
        "svc":        BackupService( _Config ),
        "chroma_dir": _ChromaDir,
        "backup_dir": _BackupDir,
    }


# ────────────────────────────────────────────────────────────
# backup_chromadb
# ────────────────────────────────────────────────────────────

class TestBackupChromadb:
    """backup_chromadb() 測試。"""

    def test_backup_creates_zip( self, backup_env ):
        _Svc = backup_env["svc"]
        _Path, _Err = _Svc.backup_chromadb()
        assert _Err is None
        assert _Path is not None
        assert os.path.isfile( _Path )
        assert _Path.endswith( ".zip" )

    def test_zip_contains_files( self, backup_env ):
        import zipfile
        _Svc = backup_env["svc"]
        _Path, _ = _Svc.backup_chromadb()
        with zipfile.ZipFile( _Path, "r" ) as _Zf:
            _Names = _Zf.namelist()
        # 至少包含 chroma.sqlite3 和 sub/segment.bin
        assert any( "chroma.sqlite3" in _N for _N in _Names )
        assert any( "segment.bin" in _N for _N in _Names )

    def test_backup_dir_auto_created( self, backup_env ):
        _BackupDir = backup_env["backup_dir"]
        assert not _BackupDir.exists()
        backup_env["svc"].backup_chromadb()
        assert _BackupDir.is_dir()

    def test_missing_chroma_dir_returns_error( self, tmp_path, monkeypatch ):
        import services.backup as _Mod
        monkeypatch.setattr( _Mod, "BACKUP_DIR", tmp_path / "backups" )
        from config import AppConfig, VaultPaths, DatabaseConfig
        _DbConfig = DatabaseConfig()
        _NonExistent = str( tmp_path / "nonexistent" )
        monkeypatch.setattr( _DbConfig, "get_chroma_path", lambda: _NonExistent )
        _Config = AppConfig(
            vault_path=str( tmp_path / "vault" ),
            paths=VaultPaths(),
            database=_DbConfig,
        )
        from services.backup import BackupService
        _Svc = BackupService( _Config )
        _Path, _Err = _Svc.backup_chromadb()
        assert _Path is None
        assert "不存在" in _Err


# ────────────────────────────────────────────────────────────
# cleanup
# ────────────────────────────────────────────────────────────

class TestCleanup:
    """cleanup() 保留策略測試。"""

    def _create_n_backups( self, backup_env, n ):
        """建立 n 份備份（間隔 mtime 以確保排序）。"""
        _Dir = backup_env["backup_dir"]
        _Dir.mkdir( parents=True, exist_ok=True )
        _Paths = []
        for _I in range( n ):
            _Name = f"chroma_backup_2026-04-{_I+1:02d}_000000.zip"
            _P = _Dir / _Name
            _P.write_bytes( b"fake" )
            # 確保 mtime 遞增
            os.utime( _P, ( _I, _I ) )
            _Paths.append( _P )
        return _Paths

    def test_cleanup_keeps_max( self, backup_env ):
        self._create_n_backups( backup_env, 10 )
        _Deleted = backup_env["svc"].cleanup( iMaxKeep=7 )
        assert _Deleted == 3
        _Remaining = list( backup_env["backup_dir"].glob( "chroma_backup_*.zip" ) )
        assert len( _Remaining ) == 7

    def test_cleanup_no_excess( self, backup_env ):
        self._create_n_backups( backup_env, 3 )
        _Deleted = backup_env["svc"].cleanup( iMaxKeep=7 )
        assert _Deleted == 0

    def test_cleanup_empty_dir( self, backup_env ):
        _Deleted = backup_env["svc"].cleanup()
        assert _Deleted == 0

    def test_cleanup_keeps_newest( self, backup_env ):
        _Paths = self._create_n_backups( backup_env, 5 )
        backup_env["svc"].cleanup( iMaxKeep=2 )
        _Remaining = sorted(
            backup_env["backup_dir"].glob( "chroma_backup_*.zip" ),
            key=lambda p: p.stat().st_mtime,
        )
        # 最新的 2 份應保留（mtime 最大的）
        assert len( _Remaining ) == 2
        assert _Remaining[-1].name == _Paths[-1].name


# ────────────────────────────────────────────────────────────
# list_backups
# ────────────────────────────────────────────────────────────

class TestListBackups:
    """list_backups() 測試。"""

    def test_empty_returns_empty( self, backup_env ):
        assert backup_env["svc"].list_backups() == []

    def test_lists_after_backup( self, backup_env ):
        backup_env["svc"].backup_chromadb()
        _List = backup_env["svc"].list_backups()
        assert len( _List ) == 1
        assert "name" in _List[0]
        assert "size_mb" in _List[0]
        assert "created" in _List[0]

    def test_order_newest_first( self, backup_env ):
        _Dir = backup_env["backup_dir"]
        _Dir.mkdir( parents=True, exist_ok=True )
        ( _Dir / "chroma_backup_2026-04-01_000000.zip" ).write_bytes( b"old" )
        ( _Dir / "chroma_backup_2026-04-10_000000.zip" ).write_bytes( b"new" )
        _List = backup_env["svc"].list_backups()
        assert len( _List ) == 2
        # 最新的排前面（檔名排序 reverse）
        assert "04-10" in _List[0]["name"]
