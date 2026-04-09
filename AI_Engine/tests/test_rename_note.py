"""
rename_note 三層測試：VaultService / MCP tool / CLI command

覆蓋：
  VaultService.rename_note   成功移動 / 來源不存在 / 目的地已存在
                              路徑穿越防護 / 非 .md 副檔名 / OS 錯誤
  MCP rename_note            成功訊息 / 錯誤處理 / 例外捕捉
  CLI _cmd_rename            正常移動 / 來源=目的地 / 缺少參數 / 失敗
                              別名 mv / dispatch 路由

VaultService.m_Indexer 以 monkeypatch stub 替換，不依賴真實 ChromaDB。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.06
"""
import os
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


def _make_fake_indexer( deleted: int = 2, indexed: int = 3 ):
    """Build a fake VaultIndexer stub with controllable stats."""
    class _FakeIndexer:
        def delete_source( self, iAbsPath ):
            return { "index_stats": { "num_deleted": deleted } }
        def sync_single( self, iAbsPath ):
            return { "total_chunks": indexed,
                     "index_stats": { "num_added": indexed, "num_updated": 0,
                                      "num_deleted": 0, "num_skipped": 0 } }
    return _FakeIndexer()


# ════════════════════════════════════════════════════════════
# VaultService.rename_note
# ════════════════════════════════════════════════════════════

class TestVaultServiceRenameNote:

    @pytest.fixture( autouse=True )
    def _init( self, monkeypatch, tmp_path ):
        """
        Initialise VaultService with a real tmp vault so path validation works,
        but replace Indexer with a stub to avoid ChromaDB.
        """
        import services.vault as _V
        from config import AppConfig, EmbeddingConfig, SearchConfig, DatabaseConfig, UserConfig, GitConfig, VaultPaths

        class _FakeVaultPaths:
            workspaces   = "workspaces"
            org_projects = "projects"
            config       = "_config"
            def org_rules_dir( self, o ):          return f"workspaces/{o}/rules"
            def org_projects_dir( self, o ):       return f"workspaces/{o}/projects"
            def project_status_file( self, o, p ): return f"workspaces/{o}/projects/{p}/status.md"
            def parse_project_path( self, fp ):    return None, None
            def project_dir( self, o, p ):         return f"workspaces/{o}/projects/{p}"
            def get_project_skeleton_dirs( self ):return []

        class _FakeAppConfig:
            vault_path = str( tmp_path )
            paths      = _FakeVaultPaths()
            class embedding:
                chunk_size    = 500
                chunk_overlap = 50
            class search:
                pass
            class git:
                auto_commit = False

        _V.VaultService.m_VaultRoot = str( tmp_path )
        _V.VaultService.m_Config    = _FakeAppConfig()
        _V.VaultService.m_Indexer   = _make_fake_indexer()
        _V.VaultService.m_IsInitialized = True

        self._vault_root = tmp_path
        self._vs = _V.VaultService

    # ── helpers ─────────────────────────────────────────────

    def _create_md( self, rel_path: str, content: str = "hello" ):
        """Write a .md file inside the tmp vault."""
        _abs = self._vault_root / rel_path
        _abs.parent.mkdir( parents=True, exist_ok=True )
        _abs.write_text( content, encoding="utf-8" )
        return _abs

    # ── success ─────────────────────────────────────────────

    def test_success_moves_file( self ):
        """成功時：來源不存在，目的地存在，DB 刪除+索引操作均呼叫。"""
        _old_abs = self._create_md( "knowledge/old.md" )
        _new_rel = "knowledge/new.md"

        _Stats, _Err = self._vs.rename_note( "knowledge/old.md", _new_rel )

        assert _Err is None
        assert not _old_abs.exists(), "來源應已消失"
        _new_abs = self._vault_root / "knowledge" / "new.md"
        assert _new_abs.exists(), "目的地應已建立"

    def test_success_returns_stats( self ):
        """stats 應包含 old_path, new_path, deleted_chunks, indexed_chunks。"""
        self._create_md( "knowledge/a.md" )
        _Stats, _Err = self._vs.rename_note( "knowledge/a.md", "knowledge/b.md" )

        assert _Err is None
        assert _Stats["old_path"] == "knowledge/a.md"
        assert _Stats["new_path"] == "knowledge/b.md"
        assert _Stats["deleted_chunks"] == 2   # matches _make_fake_indexer default
        assert _Stats["indexed_chunks"]  == 3

    def test_creates_missing_directory( self ):
        """目標目錄不存在時，應自動建立。"""
        self._create_md( "knowledge/flat.md" )

        _Stats, _Err = self._vs.rename_note(
            "knowledge/flat.md",
            "knowledge/nested/dir/flat.md",
        )

        assert _Err is None
        _new_abs = self._vault_root / "knowledge" / "nested" / "dir" / "flat.md"
        assert _new_abs.exists()

    # ── error cases ─────────────────────────────────────────

    def test_source_not_found( self ):
        """來源不存在時應回傳 Error: file not found。"""
        _Stats, _Err = self._vs.rename_note( "knowledge/ghost.md", "knowledge/ghost2.md" )

        assert _Stats is None
        assert "not found" in _Err.lower()

    def test_destination_already_exists( self ):
        """目的地已存在時應拒絕操作（防止意外覆蓋）。"""
        self._create_md( "knowledge/src.md" )
        self._create_md( "knowledge/dst.md" )

        _Stats, _Err = self._vs.rename_note( "knowledge/src.md", "knowledge/dst.md" )

        assert _Stats is None
        assert "already exists" in _Err.lower() or "destination" in _Err.lower()

    def test_old_path_traversal_blocked( self ):
        """路徑穿越嘗試應被阻止。"""
        _Stats, _Err = self._vs.rename_note( "../outside/evil.md", "knowledge/ok.md" )

        assert _Stats is None
        assert "path traversal" in _Err.lower() or "Error" in _Err

    def test_new_path_traversal_blocked( self ):
        """目的地路徑穿越嘗試應被阻止。"""
        self._create_md( "knowledge/src.md" )
        _Stats, _Err = self._vs.rename_note( "knowledge/src.md", "../outside/evil.md" )

        assert _Stats is None
        assert "path traversal" in _Err.lower() or "Error" in _Err

    def test_old_path_non_md_rejected( self ):
        """非 .md 副檔名的來源路徑應被拒絕。"""
        _Stats, _Err = self._vs.rename_note( "knowledge/file.txt", "knowledge/file.md" )

        assert _Stats is None
        assert "md" in _Err.lower() or "extension" in _Err.lower() or "Error" in _Err

    def test_new_path_non_md_rejected( self ):
        """非 .md 副檔名的目的地路徑應被拒絕。"""
        self._create_md( "knowledge/src.md" )
        _Stats, _Err = self._vs.rename_note( "knowledge/src.md", "knowledge/dst.txt" )

        assert _Stats is None
        assert "md" in _Err.lower() or "extension" in _Err.lower() or "Error" in _Err


# ════════════════════════════════════════════════════════════
# MCP tool: rename_note
# ════════════════════════════════════════════════════════════

class TestMcpRenameNote:



    def test_success_message( self, monkeypatch ):
        """成功時訊息應包含來源路徑、目的地路徑和 chunk 數字。"""
        import mcp_app.server as _S
        import services.vault as _V
        monkeypatch.setattr(
            _V.VaultService, "rename_note",
            classmethod( lambda cls, o, n: (
                { "old_path": o, "new_path": n, "deleted_chunks": 4, "indexed_chunks": 5 }, None
            ))
        )

        _Out = _S.mcp._tool_manager._tools["rename_note"].fn( "knowledge/old.md", "knowledge/new.md" )

        assert "knowledge/old.md" in _Out
        assert "knowledge/new.md" in _Out
        assert "4" in _Out
        assert "5" in _Out

    def test_error_string( self, monkeypatch ):
        """VaultService 回傳錯誤時，輸出應以 'Error:' 開頭。"""
        import mcp_app.server as _S
        import services.vault as _V
        monkeypatch.setattr(
            _V.VaultService, "rename_note",
            classmethod( lambda cls, o, n: ( None, "Error: destination already exists" ) )
        )

        _Out = _S.mcp._tool_manager._tools["rename_note"].fn( "a.md", "b.md" )

        assert _Out.startswith( "Error:" )
        assert "destination already exists" in _Out

    def test_exception_handled( self, monkeypatch ):
        """意外例外應被捕捉並以 'Error:' 開頭回傳。"""
        import mcp_app.server as _S
        import services.vault as _V

        def _raise( cls, o, n ):
            raise RuntimeError( "disk full" )

        monkeypatch.setattr( _V.VaultService, "rename_note", classmethod( _raise ) )

        _Out = _S.mcp._tool_manager._tools["rename_note"].fn( "a.md", "b.md" )

        assert _Out.startswith( "Error:" )
        assert "disk full" in _Out


# ════════════════════════════════════════════════════════════
# CLI _cmd_rename
# ════════════════════════════════════════════════════════════

@pytest.fixture
def repl( monkeypatch, tmp_path ):
    """最小可用 VaultRepl（與其他 CLI 測試相同的 fixture pattern）。"""
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


_RENAME_SUCCESS = {
    "old_path": "knowledge/old.md",
    "new_path": "knowledge/new.md",
    "deleted_chunks": 2,
    "indexed_chunks": 3,
}


class TestCmdRenameNote:

    def test_missing_args_shows_usage( self, repl, capsys ):
        """缺少參數時應印出用法提示。"""
        repl._cmd_rename( [] )

        _Out = capsys.readouterr().out
        assert "用法" in _Out or "rename" in _Out.lower()

    def test_only_one_arg_shows_usage( self, repl, capsys ):
        """只提供來源路徑時，也應顯示用法。"""
        repl._cmd_rename( ["knowledge/old.md"] )

        _Out = capsys.readouterr().out
        assert "用法" in _Out or "rename" in _Out.lower()

    def test_same_source_and_dest( self, repl, capsys ):
        """來源與目的地相同時應印出警告，不呼叫 VaultService。"""
        repl._cmd_rename( ["knowledge/a.md", "knowledge/a.md"] )

        _Out = capsys.readouterr().out
        assert "相同" in _Out or "⚠️" in _Out

    def test_success( self, repl, monkeypatch, capsys ):
        """成功時應印出 ✅ 和詳細統計。"""
        import services.vault as _V
        monkeypatch.setattr(
            _V.VaultService, "rename_note",
            classmethod( lambda cls, o, n: ( _RENAME_SUCCESS, None ) )
        )

        repl._cmd_rename( ["knowledge/old.md", "knowledge/new.md"] )

        _Out = capsys.readouterr().out
        assert "✅" in _Out
        assert "knowledge/old.md" in _Out
        assert "knowledge/new.md" in _Out

    def test_failure( self, repl, monkeypatch, capsys ):
        """VaultService 失敗時應印出 ❌ 和錯誤訊息。"""
        import services.vault as _V
        monkeypatch.setattr(
            _V.VaultService, "rename_note",
            classmethod( lambda cls, o, n: ( None, "destination already exists" ) )
        )

        repl._cmd_rename( ["knowledge/old.md", "knowledge/new.md"] )

        _Out = capsys.readouterr().out
        assert "❌" in _Out
        assert "destination already exists" in _Out

    def test_alias_mv_exists( self, repl ):
        """'mv' 別名應對應 'rename'。"""
        assert repl._ALIASES.get( "mv" ) == "rename"

    def test_dispatch_routes_rename( self, repl, monkeypatch, capsys ):
        """_dispatch('rename old.md new.md') 應路由到 _cmd_rename，不顯示未知指令。"""
        import services.vault as _V
        monkeypatch.setattr(
            _V.VaultService, "rename_note",
            classmethod( lambda cls, o, n: ( _RENAME_SUCCESS, None ) )
        )

        repl._dispatch( "rename knowledge/old.md knowledge/new.md" )

        _Out = capsys.readouterr().out
        assert "未知指令" not in _Out
        assert "✅" in _Out

    def test_dispatch_routes_mv_alias( self, repl, monkeypatch, capsys ):
        """_dispatch('mv old.md new.md') 應透過別名展開路由到 rename。"""
        import services.vault as _V
        monkeypatch.setattr(
            _V.VaultService, "rename_note",
            classmethod( lambda cls, o, n: ( _RENAME_SUCCESS, None ) )
        )

        repl._dispatch( "mv knowledge/old.md knowledge/new.md" )

        _Out = capsys.readouterr().out
        assert "未知指令" not in _Out
        assert "✅" in _Out
