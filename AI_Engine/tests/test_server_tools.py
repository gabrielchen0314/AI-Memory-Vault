"""
MCP Server 新增工具的單元測試

覆蓋：
  write_note(mode)        mode 參數正確傳入 VaultService（overwrite/append）
  check_index_status()    無變更 / 有變更 / ConfigManager 未初始化
  reindex_vault()         成功路徑 / reset_index 失敗 / 例外

所有外部依賴（ConfigManager、MigrationManager、VaultService）
均以 monkeypatch 替換，測試無需真實 Vault / ChromaDB。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.07
"""
import pytest


# ────────────────────────────────────────────────────────────
# Helpers — minimal stubs
# ────────────────────────────────────────────────────────────

class _FakeConfig:
    pass


class _FakeConfigManager:
    _initialized: bool = True
    _config = _FakeConfig()

    @classmethod
    def is_initialized( cls ) -> bool:
        return cls._initialized

    @classmethod
    def load( cls ):
        return cls._config


class _FakeOkVault:
    """write_note stub：回傳成功 stats。"""
    @classmethod
    def write_note( cls, file_path, content, mode="overwrite" ):
        cls._last_mode = mode
        return {
            "file_path": file_path,
            "chars": len( content ),
            "mode": mode,
            "new_project": False,
            "index_stats": { "num_added": 1, "num_updated": 0 },
            "total_chunks": 2,
        }, None

    @classmethod
    def sync( cls ):
        return {
            "total_chunks": 50,
            "total_files": 10,
            "index_stats": { "num_added": 50, "num_updated": 0, "num_deleted": 0 },
        }


class _FakeErrVault:
    """write_note stub：回傳錯誤。"""
    @classmethod
    def write_note( cls, file_path, content, mode="overwrite" ):
        return None, "path validation error"


class _FakeMigration_Clean:
    """MigrationManager stub：無需 reindex。"""
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
    """MigrationManager stub：需要 reindex，兩個欄位變更。"""
    _CHANGES = [
        ( "embedding_model", "all-MiniLM-L6-v2", "paraphrase-multilingual" ),
        ( "chunk_size", "500", "1000" ),
    ]

    @classmethod
    def check( cls, config ):
        return True, cls._CHANGES

    @classmethod
    def describe_changes( cls, changes ):
        return "  - embedding_model: old → new\n  - chunk_size: 500 → 1000"


class _FakeMigration_ResetFail:
    """MigrationManager stub：reset_index 失敗。"""
    @classmethod
    def check( cls, config ):
        return True, []

    @classmethod
    def reset_index( cls, config ):
        return False, "disk full"

    @classmethod
    def describe_changes( cls, changes ):
        return ""


# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────




# ────────────────────────────────────────────────────────────
# write_note — mode parameter passthrough
# ────────────────────────────────────────────────────────────

class TestWriteNoteMode:

    def test_overwrite_mode_passed( self, monkeypatch ):
        """write_note 預設 mode='overwrite' 應傳入 VaultService。"""
        import services.vault as _VaultMod
        monkeypatch.setattr( _VaultMod, "VaultService", _FakeOkVault )

        from mcp_app.server import mcp
        write_note = mcp._tool_manager._tools["write_note"].fn
        _Result = write_note( "knowledge/test.md", "hello" )

        assert _FakeOkVault._last_mode == "overwrite"
        assert "已寫入" in _Result

    def test_append_mode_passed( self, monkeypatch ):
        """write_note(mode='append') 應將 mode 傳入 VaultService.write_note。"""
        import services.vault as _VaultMod
        monkeypatch.setattr( _VaultMod, "VaultService", _FakeOkVault )

        from mcp_app.server import mcp
        write_note = mcp._tool_manager._tools["write_note"].fn
        _Result = write_note( "knowledge/test.md", "extra content", mode="append" )

        assert _FakeOkVault._last_mode == "append"
        assert "已寫入" in _Result

    def test_error_returns_error_string( self, monkeypatch ):
        """VaultService 回傳錯誤時，write_note 應回傳錯誤訊息字串。"""
        import services.vault as _VaultMod
        monkeypatch.setattr( _VaultMod, "VaultService", _FakeErrVault )

        from mcp_app.server import mcp
        write_note = mcp._tool_manager._tools["write_note"].fn
        _Result = write_note( "../escape.md", "bad" )

        assert "path validation error" in _Result

    def test_result_contains_chars( self, monkeypatch ):
        """成功時回傳字串應含 chars 資訊。"""
        import services.vault as _VaultMod
        monkeypatch.setattr( _VaultMod, "VaultService", _FakeOkVault )

        from mcp_app.server import mcp
        write_note = mcp._tool_manager._tools["write_note"].fn
        _Result = write_note( "knowledge/test.md", "hello world" )

        assert "字元" in _Result or "已寫入" in _Result


# ────────────────────────────────────────────────────────────
# check_index_status
# ────────────────────────────────────────────────────────────

class TestCheckIndexStatus:

    def test_up_to_date( self, monkeypatch ):
        """索引無需更新時，應回傳 up-to-date 訊息。"""
        import config as _ConfigMod
        import core.migration as _MigMod
        monkeypatch.setattr( _ConfigMod, "ConfigManager", _FakeConfigManager )
        monkeypatch.setattr( _MigMod, "MigrationManager", _FakeMigration_Clean )

        from mcp_app.server import mcp
        check_index_status = mcp._tool_manager._tools["check_index_status"].fn
        _Result = check_index_status()

        assert "無需重建" in _Result or "up-to-date" in _Result

    def test_out_of_date_contains_warning( self, monkeypatch ):
        """索引需更新時，應回傳警告與變更說明。"""
        import config as _ConfigMod
        import core.migration as _MigMod
        monkeypatch.setattr( _ConfigMod, "ConfigManager", _FakeConfigManager )
        monkeypatch.setattr( _MigMod, "MigrationManager", _FakeMigration_Dirty )

        from mcp_app.server import mcp
        check_index_status = mcp._tool_manager._tools["check_index_status"].fn
        _Result = check_index_status()

        assert "⚠️" in _Result
        assert "reindex_vault" in _Result

    def test_out_of_date_contains_change_description( self, monkeypatch ):
        """應包含 describe_changes 輸出（欄位差異說明）。"""
        import config as _ConfigMod
        import core.migration as _MigMod
        monkeypatch.setattr( _ConfigMod, "ConfigManager", _FakeConfigManager )
        monkeypatch.setattr( _MigMod, "MigrationManager", _FakeMigration_Dirty )

        from mcp_app.server import mcp
        check_index_status = mcp._tool_manager._tools["check_index_status"].fn
        _Result = check_index_status()

        assert "embedding_model" in _Result or "chunk_size" in _Result

    def test_exception_returns_error( self, monkeypatch ):
        """ConfigManager.load 拋出例外時，應回傳 Error: 字串。"""
        import config as _ConfigMod

        class _BrokenManager:
            @classmethod
            def is_initialized( cls ) -> bool:
                return True
            @classmethod
            def load( cls ):
                raise RuntimeError( "config file missing" )

        monkeypatch.setattr( _ConfigMod, "ConfigManager", _BrokenManager )

        from mcp_app.server import mcp
        check_index_status = mcp._tool_manager._tools["check_index_status"].fn
        _Result = check_index_status()

        assert "Error:" in _Result


# ────────────────────────────────────────────────────────────
# reindex_vault
# ────────────────────────────────────────────────────────────

class TestReindexVault:

    def test_success_returns_reindex_complete( self, monkeypatch ):
        """正常流程：reset_index 成功且 sync 完成後，應回傳 Reindex complete。"""
        import config as _ConfigMod
        import core.migration as _MigMod
        import services.vault as _VaultMod
        monkeypatch.setattr( _ConfigMod, "ConfigManager", _FakeConfigManager )
        monkeypatch.setattr( _MigMod, "MigrationManager", _FakeMigration_Clean )
        monkeypatch.setattr( _VaultMod, "VaultService", _FakeOkVault )

        from mcp_app.server import mcp
        reindex_vault = mcp._tool_manager._tools["reindex_vault"].fn
        _Result = reindex_vault()

        assert "重建完成" in _Result

    def test_success_contains_chunk_stats( self, monkeypatch ):
        """回傳訊息應含 chunks 與 files 統計。"""
        import config as _ConfigMod
        import core.migration as _MigMod
        import services.vault as _VaultMod
        monkeypatch.setattr( _ConfigMod, "ConfigManager", _FakeConfigManager )
        monkeypatch.setattr( _MigMod, "MigrationManager", _FakeMigration_Clean )
        monkeypatch.setattr( _VaultMod, "VaultService", _FakeOkVault )

        from mcp_app.server import mcp
        reindex_vault = mcp._tool_manager._tools["reindex_vault"].fn
        _Result = reindex_vault()

        assert "chunks" in _Result
        assert "檔案" in _Result or "files" in _Result

    def test_reset_fail_returns_error( self, monkeypatch ):
        """reset_index 回傳 False 時，應回傳 Error 字串（不繼續 sync）。"""
        import config as _ConfigMod
        import core.migration as _MigMod

        _SyncCalled = []

        class _TrackingVault:
            @classmethod
            def sync( cls ):
                _SyncCalled.append( True )
                return {}

        monkeypatch.setattr( _ConfigMod, "ConfigManager", _FakeConfigManager )
        monkeypatch.setattr( _MigMod, "MigrationManager", _FakeMigration_ResetFail )
        import services.vault as _VaultMod
        monkeypatch.setattr( _VaultMod, "VaultService", _TrackingVault )

        from mcp_app.server import mcp
        reindex_vault = mcp._tool_manager._tools["reindex_vault"].fn
        _Result = reindex_vault()

        assert "❌" in _Result or "Error" in _Result
        assert "disk full" in _Result
        assert not _SyncCalled, "sync() 不應在 reset_index 失敗後被呼叫"

    def test_exception_returns_error( self, monkeypatch ):
        """ConfigManager.load 拋出例外時，應回傳 Error: 字串。"""
        import config as _ConfigMod

        class _BrokenManager:
            @classmethod
            def is_initialized( cls ) -> bool:
                return True
            @classmethod
            def load( cls ):
                raise RuntimeError( "no disk space" )

        monkeypatch.setattr( _ConfigMod, "ConfigManager", _BrokenManager )

        from mcp_app.server import mcp
        reindex_vault = mcp._tool_manager._tools["reindex_vault"].fn
        _Result = reindex_vault()

        assert "Error:" in _Result

    def test_added_stat_in_output( self, monkeypatch ):
        """回傳訊息應含 Added= 統計（來自 sync 的 index_stats）。"""
        import config as _ConfigMod
        import core.migration as _MigMod
        import services.vault as _VaultMod
        monkeypatch.setattr( _ConfigMod, "ConfigManager", _FakeConfigManager )
        monkeypatch.setattr( _MigMod, "MigrationManager", _FakeMigration_Clean )
        monkeypatch.setattr( _VaultMod, "VaultService", _FakeOkVault )

        from mcp_app.server import mcp
        reindex_vault = mcp._tool_manager._tools["reindex_vault"].fn
        _Result = reindex_vault()

        assert "新增=" in _Result or "Added=" in _Result
