"""
自動學習管道 + Post-Write Hook 單元測試。
測試 SchedulerService._auto_learn_instincts 和 VaultService hook 系統。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.7
@date 2026.04.10
"""
import os
from unittest.mock import MagicMock, patch, call

import pytest


# ────────────────────────────────────────────────────────────
# Auto-Learn Tests
# ────────────────────────────────────────────────────────────

class TestAutoLearnInstincts:
    """SchedulerService._auto_learn_instincts() 測試。"""

    def test_creates_instinct_from_problem( self, sched, monkeypatch ):
        _MockCreate = MagicMock()
        _MockSvc = MagicMock()
        _MockSvc.create = _MockCreate

        monkeypatch.setattr(
            "services.instinct.InstinctService",
            lambda _cfg: _MockSvc,
        )

        _Detail = {
            "problems": [
                {
                    "problem": "Mock path was wrong after refactor",
                    "cause": "VaultService sub-module split",
                    "solution": "Patch at module level instead of class level",
                }
            ]
        }

        sched._auto_learn_instincts( _Detail, "TESTORG", "test-project" )

        assert _MockCreate.call_count == 1
        _KW = _MockCreate.call_args[1]
        assert "mock-path-was-wrong" in _KW["iId"]
        assert _KW["iDomain"] == "test-project"
        assert _KW["iSource"] == "auto-learn:TESTORG/test-project"
        assert "Patch at module level" in _KW["iAction"]

    def test_creates_instinct_from_learning( self, sched, monkeypatch ):
        _MockCreate = MagicMock()
        _MockSvc = MagicMock()
        _MockSvc.create = _MockCreate

        monkeypatch.setattr(
            "services.instinct.InstinctService",
            lambda _cfg: _MockSvc,
        )

        _Detail = {
            "learnings": [
                "Always check hasattr before calling methods on mock objects"
            ]
        }

        sched._auto_learn_instincts( _Detail, "TESTORG", "test-project" )

        assert _MockCreate.call_count == 1
        _KW = _MockCreate.call_args[1]
        assert "always-check-hasattr" in _KW["iId"]
        assert "學習" in _KW["iTitle"]

    def test_skips_short_learning( self, sched, monkeypatch ):
        _MockCreate = MagicMock()
        _MockSvc = MagicMock()
        _MockSvc.create = _MockCreate

        monkeypatch.setattr(
            "services.instinct.InstinctService",
            lambda _cfg: _MockSvc,
        )

        _Detail = { "learnings": [ "short" ] }  # < 10 chars
        sched._auto_learn_instincts( _Detail, "TESTORG", "test-project" )
        assert _MockCreate.call_count == 0

    def test_skips_problem_without_solution( self, sched, monkeypatch ):
        _MockCreate = MagicMock()
        _MockSvc = MagicMock()
        _MockSvc.create = _MockCreate

        monkeypatch.setattr(
            "services.instinct.InstinctService",
            lambda _cfg: _MockSvc,
        )

        _Detail = {
            "problems": [ { "problem": "Something broke", "solution": "" } ]
        }
        sched._auto_learn_instincts( _Detail, "TESTORG", "test-project" )
        assert _MockCreate.call_count == 0

    def test_file_exists_silently_skipped( self, sched, monkeypatch ):
        _MockSvc = MagicMock()
        _MockSvc.create.side_effect = FileExistsError( "already exists" )

        monkeypatch.setattr(
            "services.instinct.InstinctService",
            lambda _cfg: _MockSvc,
        )

        _Detail = {
            "problems": [ { "problem": "Duplicate problem text here", "solution": "Solution text" } ]
        }
        # Should not raise
        sched._auto_learn_instincts( _Detail, "TESTORG", "test-project" )

    def test_multiple_items_creates_multiple( self, sched, monkeypatch ):
        _MockCreate = MagicMock()
        _MockSvc = MagicMock()
        _MockSvc.create = _MockCreate

        monkeypatch.setattr(
            "services.instinct.InstinctService",
            lambda _cfg: _MockSvc,
        )

        _Detail = {
            "problems": [
                { "problem": "First problem description", "solution": "First solution" },
                { "problem": "Second problem description", "solution": "Second solution" },
            ],
            "learnings": [
                "Learning one is long enough to pass the filter"
            ],
        }
        sched._auto_learn_instincts( _Detail, "TESTORG", "test-project" )
        assert _MockCreate.call_count == 3

    def test_graceful_on_instinct_service_init_fail( self, sched, monkeypatch ):
        monkeypatch.setattr(
            "services.instinct.InstinctService",
            MagicMock( side_effect=RuntimeError( "init fail" ) ),
        )
        # Should not raise
        sched._auto_learn_instincts(
            { "problems": [ { "problem": "test", "solution": "test" } ] },
            "TESTORG", "test-project",
        )

    def test_empty_detail_no_calls( self, sched, monkeypatch ):
        _MockCreate = MagicMock()
        _MockSvc = MagicMock()
        _MockSvc.create = _MockCreate

        monkeypatch.setattr(
            "services.instinct.InstinctService",
            lambda _cfg: _MockSvc,
        )

        sched._auto_learn_instincts( {}, "TESTORG", "test-project" )
        assert _MockCreate.call_count == 0


# ────────────────────────────────────────────────────────────
# Post-Write Hook Tests
# ────────────────────────────────────────────────────────────

class TestPostWriteHooks:
    """VaultService post-write hook 系統測試。"""

    def test_register_and_fire( self ):
        from services.vault import VaultService
        _Calls = []
        _Hook = lambda path: _Calls.append( path )

        try:
            VaultService.register_post_write_hook( _Hook )
            VaultService._fire_post_write_hooks( "test/file.md" )
            assert _Calls == [ "test/file.md" ]
        finally:
            VaultService.unregister_post_write_hook( _Hook )

    def test_unregister_stops_firing( self ):
        from services.vault import VaultService
        _Calls = []
        _Hook = lambda path: _Calls.append( path )

        VaultService.register_post_write_hook( _Hook )
        VaultService.unregister_post_write_hook( _Hook )
        VaultService._fire_post_write_hooks( "test/file.md" )
        assert _Calls == []

    def test_duplicate_register_ignored( self ):
        from services.vault import VaultService
        _Calls = []
        _Hook = lambda path: _Calls.append( path )

        try:
            VaultService.register_post_write_hook( _Hook )
            VaultService.register_post_write_hook( _Hook )  # dup
            VaultService._fire_post_write_hooks( "test.md" )
            assert len( _Calls ) == 1  # 不會觸發兩次
        finally:
            VaultService.unregister_post_write_hook( _Hook )

    def test_hook_error_does_not_propagate( self ):
        from services.vault import VaultService

        def _BadHook( path ):
            raise ValueError( "boom" )

        _GoodCalls = []
        _GoodHook = lambda path: _GoodCalls.append( path )

        try:
            VaultService.register_post_write_hook( _BadHook )
            VaultService.register_post_write_hook( _GoodHook )
            # Should not raise
            VaultService._fire_post_write_hooks( "test.md" )
            # Good hook still fires after bad one
            assert _GoodCalls == [ "test.md" ]
        finally:
            VaultService.unregister_post_write_hook( _BadHook )
            VaultService.unregister_post_write_hook( _GoodHook )

    def test_unregister_nonexistent_no_error( self ):
        from services.vault import VaultService
        _Hook = lambda path: None
        # Should not raise
        VaultService.unregister_post_write_hook( _Hook )

    def test_multiple_hooks_all_fire( self ):
        from services.vault import VaultService
        _A, _B = [], []
        _HookA = lambda path: _A.append( path )
        _HookB = lambda path: _B.append( path )

        try:
            VaultService.register_post_write_hook( _HookA )
            VaultService.register_post_write_hook( _HookB )
            VaultService._fire_post_write_hooks( "note.md" )
            assert _A == [ "note.md" ]
            assert _B == [ "note.md" ]
        finally:
            VaultService.unregister_post_write_hook( _HookA )
            VaultService.unregister_post_write_hook( _HookB )
