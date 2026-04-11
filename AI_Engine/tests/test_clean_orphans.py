"""
clean_orphans 三層測試：VaultService / MCP tool / CLI command

覆蓋：
  VaultService.clean_orphans   無孤立 / 有孤立 / check_integrity 錯誤
  MCP clean_orphans            DB 整潔訊息 / 有孤立時列出來源 / 錯誤處理
  CLI _cmd_clean_orphans       取消 / yes 確認成功 / 無孤立 / check 失敗 / clean 失敗
  別名 cl / dispatch 路由

MCP Server 和 VaultService 以 monkeypatch stub 替換，
不依賴真實 Vault / ChromaDB，測試速度快。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.07
"""
import pytest


# ════════════════════════════════════════════════════════════
# Shared stubs
# ════════════════════════════════════════════════════════════

class _FakeConfig:
    pass


class _FakeCM_Ok:
    @classmethod
    def is_initialized( cls ) -> bool:
        return True
    @classmethod
    def load( cls ):
        return _FakeConfig()


_NO_ORPHANS_INTEGRITY = {
    "total_files":       10,
    "total_db_sources":  10,
    "orphaned":          [],
}

_WITH_ORPHANS_INTEGRITY = {
    "total_files":       8,
    "total_db_sources": 10,
    "orphaned": [
        "/vault/old/deleted_note.md",
        "/vault/old/another.md",
    ],
}

_CLEAN_RESULT_ZERO = {
    "removed":          0,
    "orphaned_sources": [],
}

_CLEAN_RESULT_HIT = {
    "removed":          5,
    "orphaned_sources": [
        "/vault/old/deleted_note.md",
        "/vault/old/another.md",
    ],
}


# ════════════════════════════════════════════════════════════
# VaultService.clean_orphans
# ════════════════════════════════════════════════════════════

class TestVaultServiceCleanOrphans:

    def test_no_orphans_returns_zero( self, monkeypatch ):
        """check_integrity 無孤立時，clean_orphans 應回傳 removed=0。"""
        import services.vault as _V
        import services._vault.index_ops as _IO
        monkeypatch.setattr( _V.VaultService, "_ensure_initialized",
                             classmethod( lambda cls: None ) )
        monkeypatch.setattr( _IO, "check_integrity",
                             lambda cls: ( _NO_ORPHANS_INTEGRITY, None ) )

        _Result, _Err = _V.VaultService.clean_orphans()

        assert _Err   is None
        assert _Result["removed"] == 0
        assert _Result["orphaned_sources"] == []

    def test_with_orphans_calls_delete( self, monkeypatch ):
        """有孤立來源時，clean_orphans 應呼叫 delete_source 並累計 removed。"""
        import services.vault as _V
        import services._vault.index_ops as _IO

        _DeletedPaths = []

        class _FakeIndexer:
            @staticmethod
            def delete_source( iAbsPath ):
                _DeletedPaths.append( iAbsPath )
                return { "index_stats": { "num_deleted": 3 } }

        monkeypatch.setattr( _V.VaultService, "_ensure_initialized",
                             classmethod( lambda cls: None ) )
        monkeypatch.setattr( _IO, "check_integrity",
                             lambda cls: ( _WITH_ORPHANS_INTEGRITY, None ) )
        monkeypatch.setattr( _V.VaultService, "m_Indexer", _FakeIndexer() )

        _Result, _Err = _V.VaultService.clean_orphans()

        assert _Err is None
        assert set( _DeletedPaths ) == set( _WITH_ORPHANS_INTEGRITY["orphaned"] )
        assert _Result["removed"] == 6       # 2 sources × 3 chunks each
        assert len( _Result["orphaned_sources"] ) == 2

    def test_check_integrity_error_propagates( self, monkeypatch ):
        """check_integrity 回傳錯誤時，clean_orphans 應原樣回傳 (None, err)。"""
        import services.vault as _V
        import services._vault.index_ops as _IO
        monkeypatch.setattr( _V.VaultService, "_ensure_initialized",
                             classmethod( lambda cls: None ) )
        monkeypatch.setattr( _IO, "check_integrity",
                             lambda cls: ( None, "DB unreachable" ) )

        _Result, _Err = _V.VaultService.clean_orphans()

        assert _Result is None
        assert _Err == "DB unreachable"

    def test_exception_returns_none_err( self, monkeypatch ):
        """delete_source 拋出例外時，clean_orphans 應捕捉並回傳 (None, message)。"""
        import services.vault as _V
        import services._vault.index_ops as _IO

        class _BrokenIndexer:
            @staticmethod
            def delete_source( _path ):
                raise RuntimeError( "index broken" )

        monkeypatch.setattr( _V.VaultService, "_ensure_initialized",
                             classmethod( lambda cls: None ) )
        monkeypatch.setattr( _IO, "check_integrity",
                             lambda cls: ( _WITH_ORPHANS_INTEGRITY, None ) )
        monkeypatch.setattr( _V.VaultService, "m_Indexer", _BrokenIndexer() )

        _Result, _Err = _V.VaultService.clean_orphans()

        assert _Result is None
        assert "index broken" in _Err


# ════════════════════════════════════════════════════════════
# MCP tool: clean_orphans
# ════════════════════════════════════════════════════════════

class TestMcpCleanOrphans:
    """從 mcp_app/server.py 直接 import clean_orphans 函式測試。"""



    def test_clean_db_returns_clean_message( self, monkeypatch ):
        """`removed == 0` 時，應回傳整潔訊息。"""
        import mcp_app.server as _S
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "clean_orphans",
                             classmethod( lambda cls: ( _CLEAN_RESULT_ZERO, None ) ) )

        _Out = _S.mcp._tool_manager._tools["clean_orphans"].fn()

        assert "整潔" in _Out or "孤立" in _Out or "✅" in _Out

    def test_orphans_found_shows_count_and_sources( self, monkeypatch ):
        """有孤立向量時，輸出應包含 removed 數字與來源路徑。"""
        import mcp_app.server as _S
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "clean_orphans",
                             classmethod( lambda cls: ( _CLEAN_RESULT_HIT, None ) ) )

        _Out = _S.mcp._tool_manager._tools["clean_orphans"].fn()

        assert "5" in _Out                         # removed chunks
        assert "2" in _Out                         # source count
        assert "deleted_note.md" in _Out or "another.md" in _Out

    def test_error_returned_as_error_string( self, monkeypatch ):
        """VaultService 回傳錯誤時，輸出應包含錯誤訊息。"""
        import mcp_app.server as _S
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "clean_orphans",
                             classmethod( lambda cls: ( None, "DB locked" ) ) )

        _Out = _S.mcp._tool_manager._tools["clean_orphans"].fn()

        assert "❌" in _Out or "Error" in _Out
        assert "DB locked" in _Out

    def test_exception_returns_error_string( self, monkeypatch ):
        """意外例外應被捕捉並回傳錯誤訊息。"""
        import mcp_app.server as _S
        import services.vault as _V

        def _raise( cls ):
            raise RuntimeError( "crash" )

        monkeypatch.setattr( _V.VaultService, "clean_orphans",
                             classmethod( _raise ) )

        _Out = _S.mcp._tool_manager._tools["clean_orphans"].fn()

        assert "Error" in _Out or "❌" in _Out or "crash" in _Out


# ════════════════════════════════════════════════════════════
# CLI _cmd_clean_orphans
# ════════════════════════════════════════════════════════════

# ── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def repl( monkeypatch, tmp_path ):
    """最小可用 VaultRepl（同 test_cli_reindex.py 的 repl fixture。）"""
    import config as _CM
    monkeypatch.setattr( _CM, "ConfigManager", _FakeCM_Ok )

    import services.scheduler as _SchedMod

    class _FakeSched:
        def __init__( self, cfg ):
            pass

    monkeypatch.setattr( _SchedMod, "SchedulerService", _FakeSched )

    class _FakeVaultPaths:
        workspaces   = "workspaces"
        org_projects = "projects"
        config       = "_config"
        def org_rules_dir( self, o ):          return f"workspaces/{o}/rules"
        def org_projects_dir( self, o ):       return f"workspaces/{o}/projects"
        def project_status_file( self, o, p ): return f"workspaces/{o}/projects/{p}/status.md"

    class _FakeAppConfig:
        vault_path = str( tmp_path )
        paths      = _FakeVaultPaths()
        class git:
            auto_commit = False

    monkeypatch.setattr( _CM, "AppConfig",  _FakeAppConfig )
    monkeypatch.setattr( _CM, "VaultPaths", _FakeVaultPaths )
    monkeypatch.setattr( _FakeCM_Ok, "load", classmethod( lambda cls: _FakeAppConfig() ) )

    from cli.repl import VaultRepl
    return VaultRepl( _FakeAppConfig() )


# ── Tests ────────────────────────────────────────────────────

class TestCmdCleanOrphans:

    def test_no_orphans_skips_prompt( self, repl, monkeypatch, capsys ):
        """無孤立向量時，應直接印出 'DB 整潔' 訊息，不詢問確認。"""
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "check_integrity",
                             classmethod( lambda cls: ( _NO_ORPHANS_INTEGRITY, None ) ) )

        repl._cmd_clean_orphans( [] )

        _Out = capsys.readouterr().out
        assert "✅" in _Out
        assert "孤立" in _Out or "無需" in _Out or "整潔" in _Out

    def test_cancel_aborts( self, repl, monkeypatch, capsys ):
        """輸入 'no' 應取消，不呼叫 clean_orphans。"""
        _CleanCalled = []

        import services.vault as _V

        def _track_clean( cls ):
            _CleanCalled.append( True )
            return _CLEAN_RESULT_HIT, None

        monkeypatch.setattr( _V.VaultService, "check_integrity",
                             classmethod( lambda cls: ( _WITH_ORPHANS_INTEGRITY, None ) ) )
        monkeypatch.setattr( _V.VaultService, "clean_orphans",
                             classmethod( _track_clean ) )
        monkeypatch.setattr( "builtins.input", lambda _: "no" )

        repl._cmd_clean_orphans( [] )

        assert not _CleanCalled
        _Out = capsys.readouterr().out
        assert "取消" in _Out

    def test_confirm_yes_cleans( self, repl, monkeypatch, capsys ):
        """輸入 'yes' 後應呼叫 clean_orphans 並印出成功訊息。"""
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "check_integrity",
                             classmethod( lambda cls: ( _WITH_ORPHANS_INTEGRITY, None ) ) )
        monkeypatch.setattr( _V.VaultService, "clean_orphans",
                             classmethod( lambda cls: ( _CLEAN_RESULT_HIT, None ) ) )
        monkeypatch.setattr( "builtins.input", lambda _: "yes" )

        repl._cmd_clean_orphans( [] )

        _Out = capsys.readouterr().out
        assert "✅" in _Out
        assert "5" in _Out       # removed chunks

    def test_check_integrity_error_shown( self, repl, monkeypatch, capsys ):
        """check_integrity 失敗時應印出 ❌ 和錯誤訊息。"""
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "check_integrity",
                             classmethod( lambda cls: ( None, "DB unreachable" ) ) )

        repl._cmd_clean_orphans( [] )

        _Out = capsys.readouterr().out
        assert "❌" in _Out
        assert "DB unreachable" in _Out

    def test_clean_failure_shown( self, repl, monkeypatch, capsys ):
        """clean_orphans 失敗時應印出 ❌ 和失敗訊息。"""
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "check_integrity",
                             classmethod( lambda cls: ( _WITH_ORPHANS_INTEGRITY, None ) ) )
        monkeypatch.setattr( _V.VaultService, "clean_orphans",
                             classmethod( lambda cls: ( None, "write failed" ) ) )
        monkeypatch.setattr( "builtins.input", lambda _: "yes" )

        repl._cmd_clean_orphans( [] )

        _Out = capsys.readouterr().out
        assert "❌" in _Out
        assert "write failed" in _Out

    def test_alias_cl_exists( self, repl ):
        """'cl' 別名應對應 'clean'。"""
        assert repl._ALIASES.get( "cl" ) == "clean"

    def test_dispatch_routes_clean( self, repl, monkeypatch, capsys ):
        """_dispatch('clean') 應路由到 _cmd_clean_orphans 而非 '未知指令'。"""
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "check_integrity",
                             classmethod( lambda cls: ( _NO_ORPHANS_INTEGRITY, None ) ) )

        repl._dispatch( "clean" )

        _Out = capsys.readouterr().out
        assert "未知指令" not in _Out
        assert "✅" in _Out

    def test_dispatch_routes_cl_alias( self, repl, monkeypatch, capsys ):
        """_dispatch('cl') 應透過別名展開路由到 clean。"""
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "check_integrity",
                             classmethod( lambda cls: ( _NO_ORPHANS_INTEGRITY, None ) ) )

        repl._dispatch( "cl" )

        _Out = capsys.readouterr().out
        assert "未知指令" not in _Out
        assert "✅" in _Out
