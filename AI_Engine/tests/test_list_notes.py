"""
list_notes 三層測試：VaultService / MCP tool / CLI command

覆蓋：
  VaultService.list_notes    根目錄列出 / 指定目錄 / 遞迴 / 空目錄
                              目錄不存在 / 路徑穿越防護 / 無 .md 檔案
  MCP list_notes             空結果訊息 / 有檔案 / 遞迴標旗 / 錯誤處理
  CLI _cmd_list              無引數 / 路徑引數 / -r 旗標 / 空結果
                              錯誤顯示 / 別名 ls / dispatch 路由

VaultService 使用 tmp_path 真實目錄，不依賴 ChromaDB。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.06
"""
import os
import importlib
import pytest


# ════════════════════════════════════════════════════════════
# Helpers — shared VaultService fixture builder
# ════════════════════════════════════════════════════════════

def _init_vs( monkeypatch, tmp_path ):
    import services.vault as _V
    _V.VaultService.m_VaultRoot     = str( tmp_path )
    _V.VaultService.m_IsInitialized = True
    monkeypatch.setattr( _V.VaultService, "_ensure_initialized", classmethod( lambda cls: None ) )
    return _V.VaultService


def _write( base, rel_path: str, content: str = "hello" ):
    _abs = base / rel_path
    _abs.parent.mkdir( parents=True, exist_ok=True )
    _abs.write_text( content, encoding="utf-8" )
    return _abs


# ════════════════════════════════════════════════════════════
# VaultService.list_notes
# ════════════════════════════════════════════════════════════

class TestVaultServiceListNotes:

    @pytest.fixture( autouse=True )
    def _init( self, monkeypatch, tmp_path ):
        self._vs   = _init_vs( monkeypatch, tmp_path )
        self._root = tmp_path

    # ── root listing ────────────────────────────────────────

    def test_empty_path_lists_root( self ):
        _write( self._root, "a.md" )
        _write( self._root, "b.md" )
        _Result, _Err = self._vs.list_notes( "", False )
        assert _Err is None
        assert _Result["path"] == "/"
        assert _Result["total"] == 2
        _Paths = [_N["path"] for _N in _Result["notes"]]
        assert "a.md" in _Paths
        assert "b.md" in _Paths

    def test_path_dot_lists_root( self ):
        _write( self._root, "z.md" )
        _Result, _Err = self._vs.list_notes( ".", False )
        assert _Err is None
        assert _Result["total"] == 1

    # ── specific directory ───────────────────────────────────

    def test_specific_subdir( self ):
        _write( self._root, "knowledge/k1.md" )
        _write( self._root, "knowledge/k2.md" )
        _write( self._root, "personal/p1.md" )
        _Result, _Err = self._vs.list_notes( "knowledge", False )
        assert _Err is None
        assert _Result["total"] == 2
        _Paths = [_N["path"] for _N in _Result["notes"]]
        assert all( _P.startswith( "knowledge/" ) for _P in _Paths )

    def test_non_md_files_ignored( self ):
        _write( self._root, "keep.md" )
        ( self._root / "skip.txt" ).write_text( "no" )
        ( self._root / "skip.py"  ).write_text( "no" )
        _Result, _Err = self._vs.list_notes( "", False )
        assert _Err is None
        assert _Result["total"] == 1

    # ── recursive ───────────────────────────────────────────

    def test_recursive_finds_nested( self ):
        _write( self._root, "a.md" )
        _write( self._root, "sub/b.md" )
        _write( self._root, "sub/deep/c.md" )
        _Result, _Err = self._vs.list_notes( "", True )
        assert _Err is None
        assert _Result["recursive"] is True
        assert _Result["total"] == 3

    def test_non_recursive_skips_subdir( self ):
        _write( self._root, "top.md" )
        _write( self._root, "sub/nested.md" )
        _Result, _Err = self._vs.list_notes( "", False )
        assert _Err is None
        assert _Result["total"] == 1
        assert _Result["notes"][0]["path"] == "top.md"

    def test_recursive_skips_hidden_dirs( self ):
        _write( self._root, "visible.md" )
        _write( self._root, ".hidden/secret.md" )
        _Result, _Err = self._vs.list_notes( "", True )
        assert _Err is None
        assert _Result["total"] == 1

    # ── empty results ────────────────────────────────────────

    def test_empty_dir_returns_zero( self ):
        ( self._root / "emptydir" ).mkdir()
        _Result, _Err = self._vs.list_notes( "emptydir", False )
        assert _Err is None
        assert _Result["total"] == 0
        assert _Result["notes"] == []

    # ── metadata ─────────────────────────────────────────────

    def test_notes_have_metadata( self ):
        _write( self._root, "meta.md", content="12345" )  # 5 bytes
        _Result, _Err = self._vs.list_notes( "", False )
        assert _Err is None
        _Note = _Result["notes"][0]
        assert "path"     in _Note
        assert "size"     in _Note
        assert "modified" in _Note
        assert _Note["size"] == 5

    def test_paths_use_forward_slashes( self ):
        _write( self._root, "sub/dir/note.md" )
        _Result, _Err = self._vs.list_notes( "", True )
        assert _Err is None
        assert "/" in _Result["notes"][0]["path"]
        assert "\\" not in _Result["notes"][0]["path"]

    def test_notes_are_sorted( self ):
        _write( self._root, "z.md" )
        _write( self._root, "a.md" )
        _write( self._root, "m.md" )
        _Result, _Err = self._vs.list_notes( "", False )
        assert _Err is None
        _Paths = [_N["path"] for _N in _Result["notes"]]
        assert _Paths == sorted( _Paths )

    # ── error cases ─────────────────────────────────────────

    def test_nonexistent_dir_returns_error( self ):
        _Result, _Err = self._vs.list_notes( "does_not_exist", False )
        assert _Result is None
        assert _Err is not None
        assert "not found" in _Err.lower() or "does_not_exist" in _Err

    def test_path_traversal_returns_error( self ):
        _Result, _Err = self._vs.list_notes( "../../etc", False )
        assert _Result is None
        assert _Err is not None

    def test_file_path_returns_error( self ):
        _write( self._root, "note.md" )
        _Result, _Err = self._vs.list_notes( "note.md", False )
        assert _Result is None
        assert _Err is not None


# ════════════════════════════════════════════════════════════
# MCP list_notes tool
# ════════════════════════════════════════════════════════════

class TestMcpListNotes:

    @pytest.fixture( autouse=True )
    def _import( self ):
        import mcp_app.server as _S
        self._S = _S

    def _call( self, path="", recursive=False ):
        return self._S.mcp._tool_manager._tools["list_notes"].fn( path=path, recursive=recursive )

    def test_empty_result_message( self, monkeypatch, tmp_path ):
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "list_notes",
            classmethod( lambda cls, p, r: ( {"path": path_used, "recursive": False, "total": 0, "notes": []}, None ) ) )
        path_used = "emptydir"
        _Out = self._S.mcp._tool_manager._tools["list_notes"].fn( path="emptydir", recursive=False )
        assert "找不到" in _Out or "0" in _Out

    def test_files_listed( self, monkeypatch ):
        import services.vault as _V
        import time
        _FakeResult = {
            "path": "knowledge", "recursive": False, "total": 2,
            "notes": [
                {"path": "knowledge/a.md", "size": 512,  "modified": time.time()},
                {"path": "knowledge/b.md", "size": 2048, "modified": time.time()},
            ]
        }
        monkeypatch.setattr( _V.VaultService, "list_notes",
            classmethod( lambda cls, p, r: ( _FakeResult, None ) ) )
        _Out = self._S.mcp._tool_manager._tools["list_notes"].fn( path="knowledge", recursive=False )
        assert "knowledge/a.md" in _Out
        assert "knowledge/b.md" in _Out
        assert "2" in _Out   # total count

    def test_recursive_flag_in_header( self, monkeypatch ):
        import services.vault as _V
        import time
        _FakeResult = {
            "path": "/", "recursive": True, "total": 1,
            "notes": [{"path": "sub/note.md", "size": 100, "modified": time.time()}]
        }
        monkeypatch.setattr( _V.VaultService, "list_notes",
            classmethod( lambda cls, p, r: ( _FakeResult, None ) ) )
        _Out = self._S.mcp._tool_manager._tools["list_notes"].fn( path="", recursive=True )
        assert "recursive" in _Out.lower() or "遞迴" in _Out

    def test_error_from_service( self, monkeypatch ):
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "list_notes",
            classmethod( lambda cls, p, r: ( None, "directory not found — bad/dir" ) ) )
        _Out = self._S.mcp._tool_manager._tools["list_notes"].fn( path="bad/dir" )
        assert "❌" in _Out or "error" in _Out.lower()

    def test_exception_caught( self, monkeypatch ):
        import services.vault as _V
        def _bomb( cls, p, r ):
            raise RuntimeError( "boom" )
        monkeypatch.setattr( _V.VaultService, "list_notes", classmethod( _bomb ) )
        _Out = self._S.mcp._tool_manager._tools["list_notes"].fn( path="" )
        assert "Error" in _Out or "error" in _Out or "boom" in _Out

    def test_size_formatted( self, monkeypatch ):
        import services.vault as _V
        import time
        _FakeResult = {
            "path": "/", "recursive": False, "total": 2,
            "notes": [
                {"path": "big.md",   "size": 4096, "modified": time.time()},
                {"path": "small.md", "size": 512,  "modified": time.time()},
            ]
        }
        monkeypatch.setattr( _V.VaultService, "list_notes",
            classmethod( lambda cls, p, r: ( _FakeResult, None ) ) )
        _Out = self._S.mcp._tool_manager._tools["list_notes"].fn()
        assert "KB" in _Out or "B" in _Out


# ════════════════════════════════════════════════════════════
# CLI _cmd_list
# ════════════════════════════════════════════════════════════

class TestCmdListNotes:

    @pytest.fixture( autouse=True )
    def _setup( self ):
        from cli.repl import VaultRepl
        self._repl = VaultRepl.__new__( VaultRepl )

    def _run( self, args: list, monkeypatch ) -> str:
        import services.vault as _V
        import io, sys
        _Captured = io.StringIO()
        _Stdout   = sys.stdout
        sys.stdout = _Captured
        try:
            self._repl._cmd_list( args )
        finally:
            sys.stdout = _Stdout
        return _Captured.getvalue()

    def test_no_args_calls_root( self, monkeypatch, tmp_path ):
        import services.vault as _V
        import time
        _FakeResult = {
            "path": "/", "recursive": False, "total": 1,
            "notes": [{"path": "a.md", "size": 100, "modified": time.time()}]
        }
        monkeypatch.setattr( _V.VaultService, "list_notes",
            classmethod( lambda cls, p, r: ( _FakeResult, None ) ) )
        _Out = self._run( [], monkeypatch )
        assert "a.md" in _Out

    def test_path_arg_passed( self, monkeypatch ):
        import services.vault as _V
        import time
        _Calls = []
        def _fake( cls, p, r ):
            _Calls.append( (p, r) )
            return ( {"path": p or "/", "recursive": r, "total": 0, "notes": []}, None )
        monkeypatch.setattr( _V.VaultService, "list_notes", classmethod( _fake ) )
        self._run( ["knowledge"], monkeypatch )
        assert _Calls[0][0] == "knowledge"

    def test_r_flag_enables_recursive( self, monkeypatch ):
        import services.vault as _V
        _Calls = []
        def _fake( cls, p, r ):
            _Calls.append( (p, r) )
            return ( {"path": p or "/", "recursive": r, "total": 0, "notes": []}, None )
        monkeypatch.setattr( _V.VaultService, "list_notes", classmethod( _fake ) )
        self._run( ["-r"], monkeypatch )
        assert _Calls[0][1] is True

    def test_path_and_r_combined( self, monkeypatch ):
        import services.vault as _V
        _Calls = []
        def _fake( cls, p, r ):
            _Calls.append( (p, r) )
            return ( {"path": p or "/", "recursive": r, "total": 0, "notes": []}, None )
        monkeypatch.setattr( _V.VaultService, "list_notes", classmethod( _fake ) )
        self._run( ["workspaces", "-r"], monkeypatch )
        assert _Calls[0] == ("workspaces", True)

    def test_empty_result_prints_message( self, monkeypatch ):
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "list_notes",
            classmethod( lambda cls, p, r: ( {"path": "/", "recursive": False, "total": 0, "notes": []}, None ) ) )
        _Out = self._run( [], monkeypatch )
        assert "無" in _Out or "No" in _Out or "0" in _Out

    def test_error_shows_x_mark( self, monkeypatch ):
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "list_notes",
            classmethod( lambda cls, p, r: ( None, "something went wrong" ) ) )
        _Out = self._run( ["bad_path"], monkeypatch )
        assert "❌" in _Out or "Error" in _Out.lower() or "went wrong" in _Out

    def test_alias_ls_wired( self ):
        from cli.repl import VaultRepl
        assert VaultRepl._ALIASES.get( "ls" ) == "list"

    def test_dispatch_routes_to_cmd_list( self, monkeypatch ):
        """Verify _dispatch("list ...") resolves to _cmd_list."""
        from cli.repl import VaultRepl
        _Repl  = VaultRepl.__new__( VaultRepl )
        _Calls = []
        monkeypatch.setattr( _Repl, "_cmd_list", lambda args: _Calls.append( args ) )
        import services.vault as _V
        monkeypatch.setattr( _V.VaultService, "list_notes",
            classmethod( lambda cls, p, r: ( {"path": "/", "recursive": False, "total": 0, "notes": []}, None ) ) )
        _Repl._dispatch( "list" )
        assert len( _Calls ) == 1, "_cmd_list was not called via dispatch"
