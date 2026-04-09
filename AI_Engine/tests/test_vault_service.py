"""
VaultService 單元測試
覆蓋重點：路徑穿越防護、read_note OSError、batch_write_notes 逐項容錯。

所有測試使用 tmp_path 隔離，不依賴真實 Vault / ChromaDB。
VaultIndexer 透過 monkeypatch 替換為 stub。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.4
@date 2026.04.05
"""
import os
import pytest


# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────

@pytest.fixture( autouse=True )
def reset_vault_service():
    """每個測試前後重置 VaultService 的類別狀態。"""
    from services.vault import VaultService
    VaultService.m_VaultRoot    = ""
    VaultService.m_Config       = None
    VaultService.m_Indexer      = None
    VaultService.m_Retriever    = None
    VaultService.m_IsInitialized = False
    yield
    VaultService.m_VaultRoot    = ""
    VaultService.m_Config       = None
    VaultService.m_Indexer      = None
    VaultService.m_Retriever    = None
    VaultService.m_IsInitialized = False


@pytest.fixture
def vault_root( tmp_path ):
    """建立最小 Vault 骨架。"""
    ( tmp_path / "notes" ).mkdir()
    return tmp_path


class _StubIndexer:
    """StubIndexer：讓 VaultService 可操作，不需真實 ChromaDB。"""
    def sync_single( self, _AbsPath ) -> dict:
        return { "index_stats": { "num_added": 1, "num_updated": 0 }, "total_chunks": 1 }
    def sync_batch( self, _Paths ) -> dict:
        return { "index_stats": { "num_added": len( _Paths ), "num_updated": 0 }, "total_chunks": len( _Paths ) }


@pytest.fixture
def vault_service( vault_root, monkeypatch ):
    """
    初始化 VaultService，替換 Indexer 為 stub，跳過向量庫依賴。
    """
    from services.vault import VaultService
    from config import AppConfig, VaultPaths

    _Config = AppConfig(
        vault_path = str( vault_root ),
        paths      = VaultPaths(),
    )

    # 替換 VaultIndexer 為 stub
    monkeypatch.setattr( "core.indexer.VaultIndexer", lambda *a, **kw: _StubIndexer() )

    # initialize 會呼叫 VaultRetriever(config) — 也 stub 掉
    monkeypatch.setattr( "core.retriever.VaultRetriever", lambda *a, **kw: object() )

    VaultService.initialize( _Config )
    return VaultService


# ────────────────────────────────────────────────────────────
# _validate_path — 路徑穿越防護
# ────────────────────────────────────────────────────────────

class TestValidatePath:

    def test_valid_path( self, vault_service, vault_root ):
        _Abs, _Err = vault_service._validate_path( "notes/hello.md" )
        assert _Err is None
        assert _Abs.startswith( str( vault_root ) )

    def test_path_traversal_blocked( self, vault_service ):
        """../../../etc/passwd などのパス穿越は拒否される。"""
        _, _Err = vault_service._validate_path( "../../../etc/passwd" )
        assert _Err == vault_service.ERROR_PATH_TRAVERSAL

    def test_path_traversal_prefix_attack( self, vault_service, tmp_path ):
        """
        /vault/../vault_evil のようなプレフィックスマッチ攻撃も拒否される。
        （旧実装の startswith(m_VaultRoot) では通過していた）
        """
        # vault_root = tmp_path/"tmp/xxx"、vault_evil = tmp_path/"tmp/xxxevil" に相当するケース
        _Vault = str( vault_service.m_VaultRoot )
        _Evil  = _Vault + "evil"  # e.g. /tmp/pytest-xxx/testevil
        # パス操作で /vault → /vault_evil を試みる
        _Rel = os.path.relpath( _Evil, _Vault )
        _, _Err = vault_service._validate_path( _Rel )
        assert _Err == vault_service.ERROR_PATH_TRAVERSAL


# ────────────────────────────────────────────────────────────
# read_note
# ────────────────────────────────────────────────────────────

class TestReadNote:

    def test_reads_existing_file( self, vault_service, vault_root ):
        _NoteFile = vault_root / "notes" / "hello.md"
        _NoteFile.write_text( "# Hello", encoding="utf-8" )

        _Content, _Err = vault_service.read_note( "notes/hello.md" )
        assert _Err is None
        assert "Hello" in _Content

    def test_file_not_found( self, vault_service ):
        _Content, _Err = vault_service.read_note( "notes/nonexistent.md" )
        assert _Content is None
        assert "not found" in _Err.lower() or "error" in _Err.lower()

    def test_path_traversal_rejected( self, vault_service ):
        _Content, _Err = vault_service.read_note( "../../../etc/passwd" )
        assert _Content is None
        assert _Err == vault_service.ERROR_PATH_TRAVERSAL

    def test_os_error_returns_error_tuple( self, vault_service, vault_root, monkeypatch ):
        """simulate OSError during open() — should return (None, error_str)."""
        _NoteFile = vault_root / "notes" / "locked.md"
        _NoteFile.write_text( "content", encoding="utf-8" )

        import builtins
        _real_open = builtins.open
        def _mock_open( path, *a, **kw ):
            if "locked.md" in str( path ):
                raise OSError( "permission denied" )
            return _real_open( path, *a, **kw )

        monkeypatch.setattr( builtins, "open", _mock_open )
        _Content, _Err = vault_service.read_note( "notes/locked.md" )
        assert _Content is None
        assert _Err is not None
        assert "Error" in _Err


# ────────────────────────────────────────────────────────────
# write_note
# ────────────────────────────────────────────────────────────

class TestWriteNote:

    def test_creates_new_file( self, vault_service, vault_root ):
        _Stats, _Err = vault_service.write_note( "notes/new.md", "# New note" )
        assert _Err is None
        assert os.path.isfile( str( vault_root / "notes" / "new.md" ) )

    def test_overwrite_mode( self, vault_service, vault_root ):
        vault_service.write_note( "notes/edit.md", "v1" )
        vault_service.write_note( "notes/edit.md", "v2" )
        _Content = ( vault_root / "notes" / "edit.md" ).read_text( encoding="utf-8" )
        assert _Content == "v2"

    def test_append_mode( self, vault_service, vault_root ):
        vault_service.write_note( "notes/append.md", "line1" )
        vault_service.write_note( "notes/append.md", "line2", iMode="append" )
        _Content = ( vault_root / "notes" / "append.md" ).read_text( encoding="utf-8" )
        assert "line1" in _Content
        assert "line2" in _Content

    def test_non_md_rejected( self, vault_service ):
        _, _Err = vault_service.write_note( "notes/evil.txt", "bad" )
        assert _Err == vault_service.ERROR_EXTENSION

    def test_path_traversal_rejected( self, vault_service ):
        _, _Err = vault_service.write_note( "../../../etc/evil.md", "bad" )
        assert _Err == vault_service.ERROR_PATH_TRAVERSAL


# ────────────────────────────────────────────────────────────
# batch_write_notes
# ────────────────────────────────────────────────────────────

class TestBatchWriteNotes:

    def test_writes_multiple_files( self, vault_service, vault_root ):
        _Notes = [
            { "file_path": "notes/a.md", "content": "# A" },
            { "file_path": "notes/b.md", "content": "# B" },
        ]
        _Results, _BatchStats, _Err = vault_service.batch_write_notes( _Notes )
        assert _Err is None
        assert len( _Results ) == 2
        assert all( _R["ok"] for _R in _Results )

    def test_partial_failure_continues( self, vault_service, vault_root, monkeypatch ):
        """一個檔案 OSError，其餘繼續寫入，不應整批失敗。"""
        import builtins
        _real_open = builtins.open
        _call_count = { "n": 0 }

        def _mock_open( path, *a, **kw ):
            if "bad.md" in str( path ) and "w" in ( a[0] if a else kw.get( "mode", "" ) ):
                raise OSError( "disk full" )
            return _real_open( path, *a, **kw )

        monkeypatch.setattr( builtins, "open", _mock_open )

        _Notes = [
            { "file_path": "notes/good.md", "content": "# Good" },
            { "file_path": "notes/bad.md",  "content": "# Bad" },
        ]
        _Results, _, _Err = vault_service.batch_write_notes( _Notes )
        assert _Err is None
        _OkFiles  = [ _R for _R in _Results if _R["ok"] ]
        _ErrFiles = [ _R for _R in _Results if not _R["ok"] ]
        assert len( _OkFiles ) == 1
        assert len( _ErrFiles ) == 1
        assert "bad.md" in _ErrFiles[0]["file_path"]

    def test_path_traversal_per_item( self, vault_service ):
        """路徑穿越的項目標為失敗，其餘項目繼續。"""
        _Notes = [
            { "file_path": "notes/ok.md",         "content": "ok" },
            { "file_path": "../../../etc/evil.md", "content": "evil" },
        ]
        _Results, _, _Err = vault_service.batch_write_notes( _Notes )
        assert _Err is None
        _ErrItems = [ _R for _R in _Results if not _R["ok"] ]
        assert len( _ErrItems ) == 1
        assert "evil.md" in _ErrItems[0]["file_path"]
