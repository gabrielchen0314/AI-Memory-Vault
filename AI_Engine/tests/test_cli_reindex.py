"""
CLI REPL checkindex/reindex 指令單元測試

覆蓋：
  _cmd_checkindex   無需 reindex / 需要 reindex（describe_changes 輸出）/ 例外
  _cmd_reindex      確認取消 / 確認執行成功 / reset_index 失敗 / 例外

MigrationManager、ConfigManager、VaultService 以 monkeypatch stub 替換，
不依賴真實 Vault / ChromaDB，測試速度快。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.07
"""
import pytest


# ────────────────────────────────────────────────────────────
# Stubs shared with test_server_tools
# ────────────────────────────────────────────────────────────

class _FakeConfig:
    pass


class _FakeCM_Ok:
    @classmethod
    def is_initialized( cls ) -> bool:
        return True
    @classmethod
    def load( cls ):
        return _FakeConfig()


class _FakeMigration_Clean:
    @classmethod
    def check( cls, config ):
        return False, []
    @classmethod
    def reset_index( cls, config ):
        return True, "ok"
    @classmethod
    def describe_changes( cls, changes ):
        return ""


class _FakeMigration_Dirty:
    _CHANGES = [
        ( "embedding_model", "MiniLM", "multilingual" ),
        ( "chunk_size",      "500",    "1000" ),
    ]
    @classmethod
    def check( cls, config ):
        return True, cls._CHANGES
    @classmethod
    def reset_index( cls, config ):
        return True, "ok"
    @classmethod
    def describe_changes( cls, changes ):
        return "  - embedding_model: MiniLM → multilingual\n  - chunk_size: 500 → 1000"


class _FakeMigration_ResetFail:
    @classmethod
    def check( cls, config ):
        return True, []
    @classmethod
    def reset_index( cls, config ):
        return False, "disk full"
    @classmethod
    def describe_changes( cls, changes ):
        return ""


class _FakeVaultSync:
    @classmethod
    def sync( cls ):
        return {
            "total_chunks": 40,
            "total_files":  8,
            "index_stats":  { "num_added": 40, "num_updated": 0, "num_deleted": 0 },
        }


# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────

@pytest.fixture
def repl( monkeypatch, tmp_path ):
    """
    建立最小可用的 VaultRepl 實例：
      - ConfigManager 已初始化（避免真正的 config.json loading）
      - SchedulerService 以 stub 替換
    """
    # 讓 ConfigManager.is_initialized() 回傳 True 避免 repl.__init__ 路徑卡住
    import config as _ConfigMod
    monkeypatch.setattr( _ConfigMod, "ConfigManager", _FakeCM_Ok )

    # SchedulerService stub（__init__ 只需要 config，我們給 _FakeConfig）
    import services.scheduler as _SchedMod

    class _FakeSched:
        def __init__( self, cfg ):
            pass

    monkeypatch.setattr( _SchedMod, "SchedulerService", _FakeSched )

    # AppConfig / VaultPaths stub 讓 REPL 初始化不崩
    import config as _CM
    _OldAppConfig  = _CM.AppConfig
    _OldVaultPaths = _CM.VaultPaths

    class _FakeVaultPaths:
        workspaces  = "workspaces"
        org_projects = "projects"
        config       = "_config"
        def org_rules_dir( self, o ):         return f"workspaces/{o}/rules"
        def org_projects_dir( self, o ):      return f"workspaces/{o}/projects"
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


# ────────────────────────────────────────────────────────────
# _cmd_checkindex
# ────────────────────────────────────────────────────────────

class TestCmdCheckIndex:

    def test_no_reindex_needed( self, repl, monkeypatch, capsys ):
        """索引最新時，應印出正常狀態訊息。"""
        import config as _CM
        import core.migration as _Mig
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _FakeMigration_Clean )

        repl._cmd_checkindex( [] )

        _Out = capsys.readouterr().out
        assert "✅" in _Out
        assert "無需重建" in _Out or "正常" in _Out

    def test_reindex_needed_shows_warning( self, repl, monkeypatch, capsys ):
        """索引過時時，應印出警告符號。"""
        import config as _CM
        import core.migration as _Mig
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _FakeMigration_Dirty )

        repl._cmd_checkindex( [] )

        _Out = capsys.readouterr().out
        assert "⚠️" in _Out

    def test_reindex_needed_shows_changes( self, repl, monkeypatch, capsys ):
        """應顯示 describe_changes 回傳的變更說明。"""
        import config as _CM
        import core.migration as _Mig
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _FakeMigration_Dirty )

        repl._cmd_checkindex( [] )

        _Out = capsys.readouterr().out
        assert "embedding_model" in _Out or "chunk_size" in _Out

    def test_reindex_needed_suggests_command( self, repl, monkeypatch, capsys ):
        """應提示使用者輸入 reindex 指令。"""
        import config as _CM
        import core.migration as _Mig
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _FakeMigration_Dirty )

        repl._cmd_checkindex( [] )

        _Out = capsys.readouterr().out
        assert "reindex" in _Out


# ────────────────────────────────────────────────────────────
# _cmd_reindex
# ────────────────────────────────────────────────────────────

class TestCmdReindex:

    def test_cancel_aborts( self, repl, monkeypatch, capsys ):
        """輸入 'no' 應取消，不呼叫 MigrationManager.reset_index。"""
        _ResetCalled = []

        class _TrackReset:
            @classmethod
            def check( cls, c ):   return True, []
            @classmethod
            def reset_index( cls, c ):
                _ResetCalled.append( True )
                return True, "ok"
            @classmethod
            def describe_changes( cls, ch ): return ""

        import config as _CM
        import core.migration as _Mig
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _TrackReset )
        monkeypatch.setattr( "builtins.input", lambda _: "no" )

        repl._cmd_reindex( [] )

        assert not _ResetCalled
        _Out = capsys.readouterr().out
        assert "取消" in _Out

    def test_confirm_yes_runs_reindex( self, repl, monkeypatch, capsys ):
        """輸入 'yes' 應執行 reset_index 並 sync。"""
        import config as _CM
        import core.migration as _Mig
        import services.vault as _VaultMod
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _FakeMigration_Clean )
        monkeypatch.setattr( _VaultMod, "VaultService", _FakeVaultSync )
        monkeypatch.setattr( "builtins.input", lambda _: "yes" )

        repl._cmd_reindex( [] )

        _Out = capsys.readouterr().out
        assert "✅" in _Out
        assert "重建完成" in _Out or "chunks" in _Out

    def test_reset_fail_shows_error( self, repl, monkeypatch, capsys ):
        """reset_index 失敗時，應印出錯誤，不繼續 sync。"""
        _SyncCalled = []

        class _TrackSync:
            @classmethod
            def sync( cls ):
                _SyncCalled.append( True )
                return {}

        import config as _CM
        import core.migration as _Mig
        import services.vault as _VaultMod
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _FakeMigration_ResetFail )
        monkeypatch.setattr( _VaultMod, "VaultService", _TrackSync )
        monkeypatch.setattr( "builtins.input", lambda _: "yes" )

        repl._cmd_reindex( [] )

        _Out = capsys.readouterr().out
        assert "❌" in _Out
        assert "disk full" in _Out
        assert not _SyncCalled

    def test_success_shows_chunk_count( self, repl, monkeypatch, capsys ):
        """成功結果應顯示 chunks 數量。"""
        import config as _CM
        import core.migration as _Mig
        import services.vault as _VaultMod
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _FakeMigration_Clean )
        monkeypatch.setattr( _VaultMod, "VaultService", _FakeVaultSync )
        monkeypatch.setattr( "builtins.input", lambda _: "yes" )

        repl._cmd_reindex( [] )

        _Out = capsys.readouterr().out
        assert "40" in _Out   # total_chunks from _FakeVaultSync

    def test_aliases_exist( self, repl ):
        """ci 和 ri 短別名應存在於 _ALIASES 字典。"""
        assert repl._ALIASES.get( "ci" ) == "checkindex"
        assert repl._ALIASES.get( "ri" ) == "reindex"

    def test_dispatch_routes_checkindex( self, repl, monkeypatch, capsys ):
        """_dispatch('checkindex') 應路由到 _cmd_checkindex 而非UnknownCmd。"""
        import config as _CM
        import core.migration as _Mig
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _FakeMigration_Clean )

        repl._dispatch( "checkindex" )

        _Out = capsys.readouterr().out
        assert "未知指令" not in _Out
        assert "✅" in _Out

    def test_dispatch_routes_ci_alias( self, repl, monkeypatch, capsys ):
        """_dispatch('ci') 應透過別名展開路由到 checkindex。"""
        import config as _CM
        import core.migration as _Mig
        monkeypatch.setattr( _CM,  "ConfigManager",    _FakeCM_Ok )
        monkeypatch.setattr( _Mig, "MigrationManager", _FakeMigration_Clean )

        repl._dispatch( "ci" )

        _Out = capsys.readouterr().out
        assert "未知指令" not in _Out
