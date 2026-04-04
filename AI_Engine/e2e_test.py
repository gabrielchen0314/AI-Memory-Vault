"""
Phase 19 E2E 測試腳本
測試 write → search → read → batch → update_todo → delete_note → vscode_integration → auto_scheduler → search_quality → project_daily_prefill → cli_repl 完整流程

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
import sys
import os

# 確保在 AI_Engine 目錄執行
os.chdir( os.path.dirname( os.path.abspath( __file__ ) ) )

from config import ConfigManager
from services.vault import VaultService
import core.vectorstore as vectorstore

# ── 初始化 ─────────────────────────────────────────────────
_Cfg = ConfigManager.load()
vectorstore.initialize(
    _Cfg.database.get_chroma_path(),
    _Cfg.database.get_record_db_url(),
    _Cfg.database.collection_name,
)
VaultService.initialize( _Cfg )

_PASS = 0
_FAIL = 0
_TEST_PATH = "workspaces/_global/rules/_e2e_test.md"
_TEST_CONTENT = "---\ntype: test\n---\n# E2E Test\n\nkeyword: vault_e2e_unique_marker_x7q9"


def check( iLabel: str, iCondition: bool, iDetail: str = "" ):
    """測試檢查點輸出。"""
    global _PASS, _FAIL
    if iCondition:
        _PASS += 1
        print( f"  [PASS] {iLabel}" )
    else:
        _FAIL += 1
        print( f"  [FAIL] {iLabel}" + ( f" -- {iDetail}" if iDetail else "" ) )


print( "\n=== Phase 19 E2E Test ===\n" )

# ── Step 1: write_note ─────────────────────────────────────
print( "Step 1: write_note" )
_Stats, _Err = VaultService.write_note( _TEST_PATH, _TEST_CONTENT )
check( "write_note returns no error", _Err is None, str( _Err ) )
check( "chars > 0", _Stats is not None and _Stats.get("chars", 0) > 0 )
check( "total_chunks > 0", _Stats is not None and _Stats.get("total_chunks", 0) > 0 )

# ── Step 2: search_formatted ────────────────────────────────
print( "\nStep 2: search_vault" )
_SearchResult = VaultService.search_formatted( "vault_e2e_unique_marker_x7q9" )
check( "search returns non-empty result", bool( _SearchResult ) )
# 唯一 marker 屬精確 token 查詢，使用 keyword 模式以確保 BM25 主導排名
_SearchResultKeyword = VaultService.search_formatted( "vault_e2e_unique_marker_x7q9", iMode="keyword" )
check( "search result contains test marker", "vault_e2e_unique_marker_x7q9" in _SearchResultKeyword )

# ── Step 3: read_note ──────────────────────────────────────
print( "\nStep 3: read_note" )
_Content, _ReadErr = VaultService.read_note( _TEST_PATH )
check( "read_note returns no error", _ReadErr is None, str( _ReadErr ) )
check( "content matches written", _Content is not None and "vault_e2e_unique_marker_x7q9" in _Content )

# ── Step 4: generate_project_status (via SchedulerService) ─
print( "\nStep 4: generate_project_status" )
from services.scheduler import SchedulerService
_Sched = SchedulerService( _Cfg )
_StatusPath = _Sched.generate_project_status( "LIFEOFDEVELOPMENT", "_e2e_test_proj" )
check( "generate_project_status returns path", bool( _StatusPath ) )
_StatusAbs = os.path.join( _Cfg.vault_path, _StatusPath )
check( "status.md file created on disk", os.path.isfile( _StatusAbs ) )
# Idempotency: call again should return same path without error
_StatusPath2 = _Sched.generate_project_status( "LIFEOFDEVELOPMENT", "_e2e_test_proj" )
check( "generate_project_status idempotent (same path)", _StatusPath == _StatusPath2 )

# ── Step 5: list_projects (via server logic) ────────────────
print( "\nStep 5: list_projects" )
_P = _Cfg.paths
_WorkspacesAbs = os.path.join( _Cfg.vault_path, _P.workspaces )
_Lines = []
for _OrgEntry in sorted( os.listdir( _WorkspacesAbs ) ):
    if _OrgEntry.startswith( "_" ):
        continue
    _OrgDir = os.path.join( _WorkspacesAbs, _OrgEntry )
    if not os.path.isdir( _OrgDir ):
        continue
    _ProjectsDir = os.path.join( _OrgDir, _P.org_projects )
    if os.path.isdir( _ProjectsDir ):
        for _ProjEntry in sorted( os.listdir( _ProjectsDir ) ):
            if os.path.isdir( os.path.join( _ProjectsDir, _ProjEntry ) ):
                _Lines.append( f"{_OrgEntry}/{_ProjEntry}" )
_ListOutput = "\n".join( _Lines )
check( "list_projects returns non-empty", bool( _ListOutput ) )
check( "list_projects includes LIFEOFDEVELOPMENT", "LIFEOFDEVELOPMENT" in _ListOutput or "lifeofdevelopment" in _ListOutput.lower() )

# ── Step 6: sync_vault ─────────────────────────────────────
print( "\nStep 6: sync_vault" )
_SyncStats = VaultService.sync()
check( "sync_vault returns stats", bool( _SyncStats ) )
check( "total_files > 0", _SyncStats.get("total_files", 0) > 0 )

# ── Step 7: batch_write_notes ──────────────────────────────
print( "\nStep 7: batch_write_notes" )
_BatchNotes = [
    { "file_path": "workspaces/_global/rules/_batch_test_1.md", "content": "---\ntype: test\n---\n# Batch Test 1\n\nbatch_1_content" },
    { "file_path": "workspaces/_global/rules/_batch_test_2.md", "content": "---\ntype: test\n---\n# Batch Test 2\n\nbatch_2_content" },
]
_BatchResults, _BatchStats, _BatchErr = VaultService.batch_write_notes( _BatchNotes )
check( "batch_write_notes returns no error", _BatchErr is None, str( _BatchErr ) )
check( "all 2 notes written ok", all( _R["ok"] for _R in _BatchResults ) )
check( "batch total_chunks > 0", _BatchStats.get("total_chunks", 0) > 0 )
check( "batch total_files == 2", _BatchStats.get("total_files", 0) == 2 )
_BatchFile1 = os.path.join( _Cfg.vault_path, "workspaces/_global/rules/_batch_test_1.md" )
_BatchFile2 = os.path.join( _Cfg.vault_path, "workspaces/_global/rules/_batch_test_2.md" )
check( "batch file 1 exists on disk", os.path.isfile( _BatchFile1 ) )
check( "batch file 2 exists on disk", os.path.isfile( _BatchFile2 ) )

# ── Step 8: update_todo ────────────────────────────────────
print( "\nStep 8: update_todo" )
_TodoTestPath = "workspaces/_global/rules/_todo_test.md"
_TodoTestContent = "# Todo Test\n\n## 待辦\n\n- [ ] 完成 E2E 測試\n- [ ] 部署到生產環境\n"
VaultService.write_note( _TodoTestPath, _TodoTestContent )
# Mark first todo as done
_TodoStats, _TodoErr = VaultService.update_todo( _TodoTestPath, "完成 E2E 測試", True )
check( "update_todo returns no error", _TodoErr is None, str( _TodoErr ) )
check( "update_todo matched", _TodoStats is not None and _TodoStats.get("matched") )
check( "updated_line contains [x]", _TodoStats is not None and "[x]" in _TodoStats.get("updated_line","") )
# Verify file was updated
_TodoContent, _ = VaultService.read_note( _TodoTestPath )
check( "file contains [x] after update", "[x] 完成 E2E 測試" in _TodoContent )
check( "second todo still [ ]", "- [ ] 部署到生產環境" in _TodoContent )
# Mark it back to undone (idempotency)
_TodoStats2, _ = VaultService.update_todo( _TodoTestPath, "完成 E2E 測試", False )
check( "update_todo can restore to [ ]", _TodoStats2 is not None and "[ ]" in _TodoStats2.get("updated_line","") )

# ── Step 9: check_integrity ────────────────────────────────
print( "\nStep 9: check_integrity" )
_IntResult, _IntErr = VaultService.check_integrity()
check( "check_integrity returns no error", _IntErr is None, str( _IntErr ) )
check( "total_db_sources > 0", _IntResult is not None and _IntResult.get("total_db_sources", 0) > 0 )
check( "total_files > 0", _IntResult is not None and _IntResult.get("total_files", 0) > 0 )
check( "orphaned is list", _IntResult is not None and isinstance( _IntResult.get("orphaned"), list ) )

# ── Step 10: get_project_status ────────────────────────────
print( "\nStep 10: get_project_status" )
_PsResult, _PsErr = VaultService.get_project_status( "LIFEOFDEVELOPMENT", "ai-memory-vault" )
check( "get_project_status returns no error", _PsErr is None, str( _PsErr ) )
check( "result has last_updated", _PsResult is not None and bool( _PsResult.get("last_updated") ) )
check( "result has pending_todos list", _PsResult is not None and isinstance( _PsResult.get("pending_todos"), list ) )
check( "result has completed_count", _PsResult is not None and isinstance( _PsResult.get("completed_count"), int ) )
check( "result has path", _PsResult is not None and "status.md" in _PsResult.get("path", "") )

# ── Step 11: delete_note ───────────────────────────────────
print( "\nStep 11: delete_note" )
_DelPath = "workspaces/_global/tech-stack/_e2e_delete_test.md"
# 先寫入一個測試檔
_DelWrite, _DelWriteErr = VaultService.write_note( _DelPath, "# delete test\n\nthis will be deleted." )
check( "write before delete: no error", _DelWriteErr is None, str( _DelWriteErr ) )
# 驗證寫入成功
_DelRead, _DelReadErr = VaultService.read_note( _DelPath )
check( "file exists before delete", _DelReadErr is None and _DelRead is not None )
# 執行刪除
_DelStats, _DelErr = VaultService.delete_note( _DelPath )
check( "delete_note returns no error", _DelErr is None, str( _DelErr ) )
check( "deleted_chunks >= 0", _DelStats is not None and _DelStats["deleted_chunks"] >= 0 )
# 驗證檔案已刪除
_DelRead2, _DelReadErr2 = VaultService.read_note( _DelPath )
check( "file is gone after delete", _DelRead2 is None and _DelReadErr2 is not None )

# ── Step 12: vscode integration ────────────────────────────
print( "\nStep 12: vscode integration (SetupService._setup_vscode_integration)" )
import tempfile
from services.setup import SetupService as _SetupService
_VscodeTempDir = tempfile.mkdtemp( prefix="_e2e_vscode_" )
_VscodeConfig = type( "C", (), {} )()  # 輕量 mock
_VscodeConfig.vscode_user_path = _VscodeTempDir
_VscodeConfig.user = type( "U", (), { "organizations": ["TESTORG"] } )()
_VscodeCreated = _SetupService._setup_vscode_integration( _VscodeConfig )
check( "vscode_files_created == 2", _VscodeCreated == 2, f"got {_VscodeCreated}" )
_CodingRulesPath = os.path.join( _VscodeTempDir, "prompts", "vault-coding-rules.instructions.md" )
_WriteConvPath   = os.path.join( _VscodeTempDir, "prompts", "VaultWriteConventions.instructions.md" )
check( "vault-coding-rules.instructions.md exists", os.path.isfile( _CodingRulesPath ) )
check( "VaultWriteConventions.instructions.md exists", os.path.isfile( _WriteConvPath ) )
_CodingContent = open( _CodingRulesPath, encoding="utf-8" ).read()
check( "coding rules contains type:rule search", "type:rule" in _CodingContent )
check( "coding rules contains org row", "TESTORG" in _CodingContent )
# 冪等：再次呼叫不應新建檔案
_VscodeCreated2 = _SetupService._setup_vscode_integration( _VscodeConfig )
check( "idempotent: second call creates 0 files", _VscodeCreated2 == 0, f"got {_VscodeCreated2}" )

# ── Step 13: AutoScheduler ────────────────────────────────
print( "\nStep 13: AutoScheduler (APScheduler trigger layer)" )
from services.auto_scheduler import AutoScheduler as _AutoScheduler
_AutoSched = _AutoScheduler( _Cfg )
check( "AutoScheduler instantiates", _AutoSched is not None )
_AutoSched.start()
check( "job_count == 6 after start", _AutoSched.job_count() == 6, f"got {_AutoSched.job_count()}" )
# 手動觸發（驗證不拋出例外）
_WeeklyOk = True
try:
    _AutoSched._run_weekly()
except Exception as _Ex:
    _WeeklyOk = False
check( "_run_weekly() executes without raising", _WeeklyOk )
_MonthlyOk = True
try:
    _AutoSched._run_monthly()
except Exception as _Ex:
    _MonthlyOk = False
check( "_run_monthly() executes without raising", _MonthlyOk )
_DailyOk = True
try:
    _AutoSched._run_daily()
except Exception as _Ex:
    _DailyOk = False
check( "_run_daily() executes without raising", _DailyOk )
_AutoSched.stop()
check( "stop() does not raise", True )

# ── Step 14: Search Quality ────────────────────────────────
print( "\nStep 14: Search Quality (chunk_size + search mode)" )
# 14a: Chunk size config persists in VaultIndexer
check( "VaultService indexer chunk_size == config", VaultService.m_Indexer.m_ChunkSize == _Cfg.embedding.chunk_size )
check( "chunk_size default is 500", _Cfg.embedding.chunk_size == 500 )
check( "chunk_overlap default is 50", _Cfg.embedding.chunk_overlap == 50 )
# 14b: SearchConfig mode presets populated
check( "keyword_bm25_weight default is 0.7", _Cfg.search.keyword_bm25_weight == 0.7 )
check( "semantic_bm25_weight default is 0.2", _Cfg.search.semantic_bm25_weight == 0.2 )
# 14c: Write a note with a unique keyword for mode search test
_ModeTestPath = "workspaces/_global/rules/_e2e_mode_test.md"
_ModeTestContent = "---\ntype: test\n---\n# Mode Search Test\n\nmode_search_unique_token_k7x2"
_ModeWrite, _ModeWriteErr = VaultService.write_note( _ModeTestPath, _ModeTestContent )
check( "mode test note write: no error", _ModeWriteErr is None, str( _ModeWriteErr ) )
# 14d: keyword mode search finds exact token
_KeywordResult = VaultService.search_formatted( "mode_search_unique_token_k7x2", iMode="keyword" )
check( "keyword mode finds exact token", "mode_search_unique_token_k7x2" in _KeywordResult, repr( _KeywordResult[:100] ) )
# 14e: semantic mode search also returns results (BM25 still partly active)
_SemanticResult = VaultService.search_formatted( "mode_search_unique_token_k7x2", iMode="semantic" )
check( "semantic mode returns non-empty", bool( _SemanticResult ) )
# 14f: default (no mode) also finds the token
_DefaultResult = VaultService.search_formatted( "mode_search_unique_token_k7x2" )
check( "default mode finds token", "mode_search_unique_token_k7x2" in _DefaultResult )
# 14g: Retriever has mode weight attributes
_Retriever = VaultService.m_Retriever
check( "retriever has m_KeywordBM25Weight", hasattr( _Retriever, "m_KeywordBM25Weight" ) )
check( "retriever has m_SemanticBM25Weight", hasattr( _Retriever, "m_SemanticBM25Weight" ) )
# 14h: VaultIndexer has m_CharSplitter
check( "indexer has m_CharSplitter", hasattr( VaultService.m_Indexer, "m_CharSplitter" ) )

# ── Step 15: generate_project_daily pre-fill ──────────────
print( "\nStep 15: generate_project_daily pre-fill (status.md → 今日計畫)" )
# 15a: 準備一個有 pending todos 的 status.md
_PfOrg     = "LIFEOFDEVELOPMENT"
_PfProject = "_e2e_prefill_proj"
_PfStatusPath = f"workspaces/{_PfOrg}/projects/{_PfProject}/status.md"
_PfStatusContent = (
    "---\ntype: status\nproject: _e2e_prefill_proj\norg: LIFEOFDEVELOPMENT\n"
    "last_updated: 2026.04.04\n---\n\n# status\n\n## 待辦事項\n\n"
    "- [ ] todo_alpha\n- [ ] todo_beta\n- [x] todo_done\n"
)
VaultService.write_note( _PfStatusPath, _PfStatusContent )
# 15b: generate_project_daily → 應自動從 status.md 預填「今日計畫」
_PfDailyPath = _Sched.generate_project_daily( _PfOrg, _PfProject, "2026-04-04" )
check( "generate_project_daily returns path", bool( _PfDailyPath ) )
_PfDailyContent, _PfDailyErr = VaultService.read_note( _PfDailyPath )
check( "daily file created", _PfDailyErr is None, str( _PfDailyErr ) )
check( "daily has 今日計畫 section", "今日計畫" in ( _PfDailyContent or "" ) )
check( "daily prefilled todo_alpha", "todo_alpha" in ( _PfDailyContent or "" ) )
check( "daily prefilled todo_beta", "todo_beta" in ( _PfDailyContent or "" ) )
check( "daily does NOT include completed todo_done", "todo_done" not in ( _PfDailyContent or "" ) )
check( "daily has status.md link", "status.md" in ( _PfDailyContent or "" ) )
# 15c: 冪等 — 已存在不覆蓋
_PfDailyPath2 = _Sched.generate_project_daily( _PfOrg, _PfProject, "2026-04-04" )
check( "idempotent: same path returned", _PfDailyPath == _PfDailyPath2 )
# 15d: 無 status.md 時降級為空模板（不拋出例外）
_PfNoStatusPath = _Sched.generate_project_daily( _PfOrg, "_e2e_no_status_proj", "2026-04-04" )
_PfNoContent, _PfNoErr = VaultService.read_note( _PfNoStatusPath )
check( "no-status fallback: no error", _PfNoErr is None, str( _PfNoErr ) )
check( "no-status fallback: has template sections", "今日完成" in ( _PfNoContent or "" ) )
# 15e: config.json has new embedding fields persisted
check( "embedding.chunk_size in config", _Cfg.embedding.chunk_size == 500 )
check( "search.keyword_bm25_weight in config", _Cfg.search.keyword_bm25_weight == 0.7 )

# ── Step 16: CLI REPL ─────────────────────────────────────
print( "\nStep 16: CLI REPL (VaultRepl command dispatch)" )
import io, contextlib
from cli.repl import VaultRepl
_Repl = VaultRepl( _Cfg )
check( "VaultRepl instantiates", _Repl is not None )
check( "VaultRepl has SchedulerService", _Repl.m_Sched is not None )
# 16a: dispatch known commands without exception
_Buf = io.StringIO()
with contextlib.redirect_stdout( _Buf ):
    _Repl._dispatch( "help" )
_HelpOut = _Buf.getvalue()
check( "help contains 'search'", "search" in _HelpOut )
check( "help contains 'read'", "read" in _HelpOut )
check( "help contains 'write'", "write" in _HelpOut )
check( "help contains 'sync'", "sync" in _HelpOut )
check( "help contains 'projects'", "projects" in _HelpOut )
check( "help contains 'integrity'", "integrity" in _HelpOut )
# 16b: unknown command reports error, does not raise
_Buf2 = io.StringIO()
with contextlib.redirect_stdout( _Buf2 ):
    _Repl._dispatch( "xyzzy" )
check( "unknown cmd output non-empty", len( _Buf2.getvalue() ) > 0 )
# 16c: search dispatch runs without exception
_Buf3 = io.StringIO()
with contextlib.redirect_stdout( _Buf3 ):
    _Repl._dispatch( "search mode_search_unique_token_k7x2" )
_SearchOut = _Buf3.getvalue()
check( "search dispatch produces output", len( _SearchOut ) > 0 )
# 16d: projects dispatch runs without exception
_Buf4 = io.StringIO()
with contextlib.redirect_stdout( _Buf4 ):
    _Repl._dispatch( "projects" )
check( "projects dispatch produces output", len( _Buf4.getvalue() ) > 0 )
# 16e: sync dispatch runs without exception
_Buf5 = io.StringIO()
with contextlib.redirect_stdout( _Buf5 ):
    _Repl._dispatch( "sync" )
check( "sync dispatch produces output", len( _Buf5.getvalue() ) > 0 )
# 16f: integrity dispatch runs without exception
_Buf6 = io.StringIO()
with contextlib.redirect_stdout( _Buf6 ):
    _Repl._dispatch( "integrity" )
check( "integrity dispatch produces output", len( _Buf6.getvalue() ) > 0 )

# ── Step 17: Scheduler 單元測試 ───────────────────────────
print( "\nStep 17: Scheduler 單元測試 (pytest tests/test_scheduler.py)" )
import subprocess
_PytestResult = subprocess.run(
    [ sys.executable, "-m", "pytest", "tests/test_scheduler.py", "-q", "--tb=short" ],
    capture_output=True,
    text=True,
    cwd=os.path.dirname( os.path.abspath( __file__ ) ),
)
_PytestOut = _PytestResult.stdout + _PytestResult.stderr
print( _PytestOut.strip() )
check( "pytest tests/test_scheduler.py passes", _PytestResult.returncode == 0 )

# ── Step 18: CLI REPL — 新增 5 個指令對齊 MCP ────────────
print( "\nStep 18: CLI REPL MCP 對齊（review / genstatus / log / aiweekly / aimonthly）" )
# 18a: help 包含新指令
_Buf18 = io.StringIO()
with contextlib.redirect_stdout( _Buf18 ):
    _Repl._dispatch( "help" )
_H18 = _Buf18.getvalue()
check( "help contains 'review'",    "review"    in _H18 )
check( "help contains 'genstatus'", "genstatus" in _H18 )
check( "help contains 'log'",       "log"       in _H18 )
check( "help contains 'aiweekly'",  "aiweekly"  in _H18 )
check( "help contains 'aimonthly'", "aimonthly" in _H18 )
# 18b: 別名對應正確
check( "alias rv → review",    _Repl._ALIASES.get( "rv" )  == "review" )
check( "alias gs → genstatus", _Repl._ALIASES.get( "gs" )  == "genstatus" )
check( "alias la → log",       _Repl._ALIASES.get( "la" )  == "log" )
check( "alias aw → aiweekly",  _Repl._ALIASES.get( "aw" )  == "aiweekly" )
check( "alias am → aimonthly", _Repl._ALIASES.get( "am" )  == "aimonthly" )
# 18c: review dispatch — 生成每日總進度表
_Buf18c = io.StringIO()
with contextlib.redirect_stdout( _Buf18c ):
    _Repl._dispatch( "review 2026-01-01" )
check( "review dispatch produces output", len( _Buf18c.getvalue() ) > 0 )
# 18d: genstatus dispatch — 生成 status.md 模板
import os as _Oe2e18
_E2eGsPath = _Cfg.vault_path
_Buf18d = io.StringIO()
with contextlib.redirect_stdout( _Buf18d ):
    _Repl._dispatch( "genstatus LIFEOFDEVELOPMENT _e2e_gs_proj" )
check( "genstatus dispatch produces output", len( _Buf18d.getvalue() ) > 0 )
_GsFile = _Oe2e18.path.join( _E2eGsPath, "workspaces", "LIFEOFDEVELOPMENT", "projects", "_e2e_gs_proj", "status.md" )
check( "genstatus creates status.md", _Oe2e18.path.isfile( _GsFile ) )
# 18e: log dispatch — 記錄 AI 對話
_Buf18e = io.StringIO()
with contextlib.redirect_stdout( _Buf18e ):
    _Repl._dispatch( "log LIFEOFDEVELOPMENT _e2e_gs_proj e2e-session test content line 1" )
check( "log dispatch produces output", len( _Buf18e.getvalue() ) > 0 )
# 18f: aiweekly dispatch
_Buf18f = io.StringIO()
with contextlib.redirect_stdout( _Buf18f ):
    _Repl._dispatch( "aiweekly 2026-01-05" )
check( "aiweekly dispatch produces output", len( _Buf18f.getvalue() ) > 0 )
# 18g: aimonthly dispatch
_Buf18g = io.StringIO()
with contextlib.redirect_stdout( _Buf18g ):
    _Repl._dispatch( "aimonthly 2026-01-01" )
check( "aimonthly dispatch produces output", len( _Buf18g.getvalue() ) > 0 )

# ── Step 19: CLI 自動化同步（tools/registry.py）──────────────────────────
print( "\nStep 19: CLI 自動化同步 — registry.py 架構驗證" )
from tools.registry import TOOL_REGISTRY, REGISTRY_BY_NAME, REGISTRY_BY_ALIAS, ToolEntry, ToolParam
# 19a: registry 可匯入、長度正確
check( "TOOL_REGISTRY importable",       isinstance( TOOL_REGISTRY, list ) )
check( "TOOL_REGISTRY has 11 entries",   len( TOOL_REGISTRY ) == 11 )
# 19b: 每個 entry 有必要欄位
for _TE in TOOL_REGISTRY:
    check( f"entry {_TE.name} has alias",      bool( _TE.alias ) )
    check( f"entry {_TE.name} has group",      bool( _TE.group ) )
    check( f"entry {_TE.name} has help_line",  bool( _TE.help_line ) )
# 19c: REGISTRY_BY_NAME / ALIAS lookup 正確
check( "REGISTRY_BY_NAME 'review'",    REGISTRY_BY_NAME.get( "review" ) is not None )
check( "REGISTRY_BY_NAME 'aiweekly'",  REGISTRY_BY_NAME.get( "aiweekly" ) is not None )
check( "REGISTRY_BY_ALIAS 'rv'",       REGISTRY_BY_ALIAS.get( "rv" ) is not None )
check( "REGISTRY_BY_ALIAS 'aw' → aiweekly",  REGISTRY_BY_ALIAS.get( "aw" ).name == "aiweekly" )
# 19d: _ALIASES 完全從 registry 衍生（無需手動維護）
for _TE in TOOL_REGISTRY:
    check( f"_ALIASES contains alias {_TE.alias}", _Repl._ALIASES.get( _TE.alias ) == _TE.name )
# 19e: _build_help() 包含所有 registry 工具名稱
_HelpText = _Repl._HELP
for _TE in TOOL_REGISTRY:
    check( f"help contains '{_TE.name}'", _TE.name in _HelpText )
# 19f: invoke=None 工具（sync/integrity）不走 _run_registry
_SyncEntry = REGISTRY_BY_NAME.get( "sync" )
check( "sync invoke is None", _SyncEntry is not None and _SyncEntry.invoke is None )
_IntgEntry = REGISTRY_BY_NAME.get( "integrity" )
check( "integrity invoke is None", _IntgEntry is not None and _IntgEntry.invoke is None )
# 19g: invoke 非 None 的工具可呼叫（weekly/monthly 無 params）
_Buf19g = io.StringIO()
with contextlib.redirect_stdout( _Buf19g ):
    _Repl._dispatch( "weekly" )
check( "weekly dispatch via registry", len( _Buf19g.getvalue() ) > 0 )
_Buf19h = io.StringIO()
with contextlib.redirect_stdout( _Buf19h ):
    _Repl._dispatch( "monthly" )
check( "monthly dispatch via registry", len( _Buf19h.getvalue() ) > 0 )

# ── Step 20: Vault Git 版本控制整合 ───────────────────────
print( "\nStep 20: Vault Git 版本控制整合（services/git_service.py）" )
import tempfile, shutil as _shutil20

# 建立獨立 tmp vault（避免污染真實 Vault）
_GitTmp = tempfile.mkdtemp( prefix="vault_git_e2e_" )
try:
    from services.git_service import GitService
    from config import GitConfig

    # 20a: GitConfig 預設值正確
    _Gc = GitConfig()
    check( "GitConfig.auto_commit default False",  _Gc.auto_commit == False )
    check( "GitConfig.author_name default set",    bool( _Gc.author_name ) )
    check( "GitConfig.author_email default set",   bool( _Gc.author_email ) )

    # 20b: _git_available() 不拋例外
    _GitAvail = GitService._git_available()
    check( "git_available() returns bool",  isinstance( _GitAvail, bool ) )

    if _GitAvail:
        # 20c: ensure_repo 建立 .git
        _Ok = GitService.ensure_repo( _GitTmp )
        check( "ensure_repo returns True",         _Ok )
        check( "ensure_repo creates .git dir",     os.path.isdir( os.path.join( _GitTmp, ".git" ) ) )

        # 20d: ensure_repo 冪等（再呼叫不出錯）
        _Ok2 = GitService.ensure_repo( _GitTmp )
        check( "ensure_repo idempotent",           _Ok2 )

        # 20e: 寫入檔案後 commit，回傳 SHA
        _TestFilePath = os.path.join( _GitTmp, "test.md" )
        with open( _TestFilePath, "w", encoding="utf-8" ) as _Ftmp:
            _Ftmp.write( "# Test\n首次寫入。\n" )
        _Committed, _Sha = GitService.commit(
            _GitTmp, "test.md", "write: test.md",
        )
        check( "commit after write returns True",  _Committed )
        check( "commit returns SHA string",        isinstance( _Sha, str ) and len( _Sha ) >= 4 )

        # 20f: 無變更時 commit 回傳 False, None
        _Committed2, _Sha2 = GitService.commit(
            _GitTmp, "test.md", "write: test.md (dup)",
        )
        check( "no-change commit returns False",   not _Committed2 )
        check( "no-change commit sha is None",     _Sha2 is None )

        # 20g: git log 顯示正確 commit message
        import subprocess as _sp20
        _LogRet = _sp20.run(
            ["git", "log", "--oneline", "-1"],
            cwd=_GitTmp, capture_output=True, text=True,
        )
        check( "git log shows commit",             "write: test.md" in _LogRet.stdout )

        # 20h: 刪除後 commit（file 已不存在，仍可 add + commit）
        os.remove( _TestFilePath )
        _Committed3, _Sha3 = GitService.commit(
            _GitTmp, "test.md", "delete: test.md",
        )
        check( "delete commit returns True",       _Committed3 )
        check( "delete commit returns SHA",        isinstance( _Sha3, str ) and len( _Sha3 ) >= 4 )

        # 20i: AppConfig.git 欄位存在且型別正確
        _Cfg20 = _Cfg  # reuse existing loaded config
        check( "AppConfig has .git attr",          hasattr( _Cfg20, "git" ) )
        check( "AppConfig.git is GitConfig",       isinstance( _Cfg20.git, GitConfig ) )

        # 20j: auto_commit=False 時 VaultService.write_note 不觸發 git
        #      （只驗證不拋例外；git 不被呼叫的副作用測試依靠 spy 在 unit test）
        check( "VaultService auto_commit disabled by default", not _Cfg20.git.auto_commit )

    else:
        # git 不可用：只驗證 ensure_repo 不拋例外
        _SafeRet = GitService.ensure_repo( _GitTmp )
        check( "ensure_repo safe when git unavailable", not _SafeRet )
        print( "  ⚠️  git not in PATH, git-specific checks skipped" )

finally:
    _shutil20.rmtree( _GitTmp, ignore_errors=True )

# ── Step 21: 知識萃取自動化 ────────────────────────────────
print( "\nStep 21: 知識萃取自動化（services/knowledge_extractor.py）" )
import shutil as _shutil21, tempfile as _tempfile21

_KETmp   = _tempfile21.mkdtemp( prefix="vault_ke_e2e_" )
_KEOrg   = "_e2e_ke_org"
_KEProj  = "_e2e_ke_proj"
_KETopic = "e2e-extract-test"

# 建立假 conversations/ 目錄與對話檔
_KEConvDir = os.path.join(
    _KETmp, "workspaces", _KEOrg, "projects", _KEProj, "conversations"
)
os.makedirs( _KEConvDir, exist_ok=True )
_KEConvFile = os.path.join( _KEConvDir, "2026-04-05_test-session.md" )
with open( _KEConvFile, "w", encoding="utf-8" ) as _Fke:
    _Fke.write(
        "---\ntype: conversation\n---\n\n"
        "# Test Topic\n\n"
        "## 關鍵決策\n\n"
        "- ChromaDB 使用 RecordManager 追蹤孤立向量\n"
        "- sync() 會清除孤立來源\n"
    )

# 建立假 Vault config 指向 _KETmp
from config import AppConfig, VaultPaths, LLMConfig, EmbeddingConfig, SearchConfig, DatabaseConfig, UserConfig, APIConfig, GitConfig
_KeCfg = AppConfig(
    vault_path=_KETmp,
    paths=VaultPaths(),
    llm=LLMConfig(),
    embedding=EmbeddingConfig(),
    search=SearchConfig(),
    database=DatabaseConfig( chroma_dir=os.path.join( _KETmp, "chroma_db" ) ),
    user=UserConfig(),
    api=APIConfig(),
    git=GitConfig(),
)

try:
    from services.knowledge_extractor import KnowledgeExtractor

    # 21a: 實例化不出錯
    _Ke = KnowledgeExtractor( _KeCfg )
    check( "KnowledgeExtractor instantiate ok", _Ke is not None )

    # 21b: 缺少 conversations 時回傳錯誤而非拋例外
    _PathErr, _ErrMsg = _Ke.extract( "_no_such_org", "_no_such_proj", "topic" )
    check( "extract missing conv returns error",  _PathErr is None )
    check( "extract missing conv error is string", isinstance( _ErrMsg, str ) )

    # 21c: 空 topic 回傳錯誤
    _PathErr2, _ErrMsg2 = _Ke.extract( _KEOrg, _KEProj, "" )
    check( "extract empty topic returns error", _PathErr2 is None and isinstance( _ErrMsg2, str ) )

    # 21d: 正常萃取 — 需使用真實 VaultService（帶 ChromaDB）
    #      這裡只驗證來源掃描邏輯（_scan_conversations），不寫入真實 Vault
    _Scanned = _Ke._scan_conversations( _KEOrg, _KEProj, None )
    check( "scan_conversations finds files",     len( _Scanned ) == 1 )
    check( "scan result has rel_path",           "rel_path" in _Scanned[0] )
    check( "scan result has session",            _Scanned[0]["session"] == "test-session" )
    check( "scan result has date",               _Scanned[0]["date"] == "2026-04-05" )

    # 21e: 萃取重點條列
    _KPoints = _Ke._extract_key_points( _Scanned )
    check( "extract_key_points returns list",    isinstance( _KPoints, list ) )
    check( "key_points non-empty",               len( _KPoints ) > 0 )
    check( "key_points no duplicate",            len( _KPoints ) == len( set( _KPoints ) ) )

    # 21f: 模板渲染不出錯
    _Card = _Ke._render_knowledge_card(
        "e2e-test", "E2E Test Topic", _KEOrg, _KEProj,
        "2026-04-05", _Scanned, _KPoints,
    )
    check( "render_knowledge_card non-empty",    len( _Card ) > 100 )
    check( "card has frontmatter",               "type: knowledge" in _Card )
    check( "card has source section",            "來源對話" in _Card )
    check( "card has source link",               "test-session" in _Card )

    # 21g: SchedulerService 有 extract_knowledge 方法（委派）
    from services.scheduler import SchedulerService
    check( "SchedulerService.extract_knowledge exists", hasattr( SchedulerService, "extract_knowledge" ) )

    # 21h: MCP tool extract_knowledge 已在 server.py 定義
    import importlib.util as _ilu
    _ServerSpec = _ilu.spec_from_file_location( "mcp_server_e2e21", "mcp_app/server.py" )
    # 僅驗證函式名稱存在，不實際啟動 MCP server
    import ast as _ast21
    with open( "mcp_app/server.py", "r", encoding="utf-8" ) as _Fs21:
        _ServerSrc = _Fs21.read()
    check( "server.py has extract_knowledge tool", "def extract_knowledge" in _ServerSrc )

    # 21i: registry 有 extract (alias=ex) 工具登記
    from tools.registry import REGISTRY_BY_NAME, REGISTRY_BY_ALIAS
    check( "registry has 'extract' entry",       "extract" in REGISTRY_BY_NAME )
    check( "registry has 'ex' alias",            "ex" in REGISTRY_BY_ALIAS )
    check( "extract entry invoke is callable",   callable( REGISTRY_BY_NAME["extract"].invoke ) )

finally:
    _shutil21.rmtree( _KETmp, ignore_errors=True )

# ── Step 22: Token 分析欄位 ────────────────────────────────
print( "\nStep 22: Token 分析欄位（services/token_counter.py）" )
import tempfile as _tempfile22, shutil as _shutil22

# ── 22a: TokenCounter 基本運算 ──────────────────
from services.token_counter import TokenCounter

check( "TokenCounter.estimate empty ''",        TokenCounter.estimate( "" ) == 0 )
check( "TokenCounter.estimate 4 chars = 1 tok", TokenCounter.estimate( "1234" ) == 1 )
check( "TokenCounter.estimate 100 chars",       TokenCounter.estimate( "a" * 100 ) == 25 )
check( "TokenCounter.format_k 500 → '500'",     TokenCounter.format_k( 500 ) == "500" )
check( "TokenCounter.format_k 1000 → '0.0k'|'1.0k'", TokenCounter.format_k( 1000 ) == "1.0k" )
check( "TokenCounter.format_k 2400 → '2.4k'",  TokenCounter.format_k( 2400 ) == "2.4k" )

# ── 22b: count_file ──────────────────────────────
_Tc22Tmp = _tempfile22.mkdtemp( prefix="vault_tc_e2e_" )
try:
    _TcFile = os.path.join( _Tc22Tmp, "test.md" )
    with open( _TcFile, "w", encoding="utf-8" ) as _Ftc:
        _Ftc.write( "a" * 400 )  # 400 chars → 100 tokens

    check( "count_file returns int",      isinstance( TokenCounter.count_file( _TcFile ), int ) )
    check( "count_file 400 chars = 100",  TokenCounter.count_file( _TcFile ) == 100 )
    check( "count_file missing → 0",      TokenCounter.count_file( "/nonexistent/path.md" ) == 0 )
finally:
    _shutil22.rmtree( _Tc22Tmp, ignore_errors=True )

# ── 22c: SchedulerService._compute_token_stats ──
from services.scheduler import SchedulerService as _Sched22

_Sc22 = _Sched22( _Cfg )
# empty convs → empty stats
_EmptyStats = _Sc22._compute_token_stats( {} )
check( "_compute_token_stats empty input",  _EmptyStats == {} )
check( "_compute_token_stats returns dict", isinstance( _EmptyStats, dict ) )

# ── 22d: weekly template renders token fields ────
_WTpl = _Sc22._render_ai_weekly_analysis_template(
    2026, 15, "2026-04-06", "2026-04-12", {}, { "ORG/proj": 2400 }
)
check( "weekly template has token total",  "2.4k" in _WTpl )
check( "weekly template no TODO in token summary", "| 估計 Token 消耗 | TODO |" not in _WTpl )

# ── 22e: monthly template renders token fields ───
_MTpl = _Sc22._render_ai_monthly_analysis_template(
    "2026-04", {}, [], { "ORG/proj": 5000 }
)
check( "monthly template has token total", "5.0k" in _MTpl )
check( "monthly template no TODO in token summary", "| 月度 Token 總消耗 | TODO |" not in _MTpl )

# ── 22f: zero convs renders '—' dash ─────────────
_WTplZero = _Sc22._render_ai_weekly_analysis_template(
    2026, 15, "2026-04-06", "2026-04-12", {}, {}
)
check( "weekly template zero tokens renders dash", "| 估計 Token 消耗 | — |" in _WTplZero )

# ── Cleanup ───────────────────────────────────────────────
print( "\nCleanup" )
import shutil
_TestProjAbs = os.path.join( _Cfg.vault_path, _P.org_projects_dir("LIFEOFDEVELOPMENT", ), "_e2e_test_proj" )
_TestProjAbs = os.path.join( _Cfg.vault_path, "workspaces", "LIFEOFDEVELOPMENT", "projects", "_e2e_test_proj" )
if os.path.isdir( _TestProjAbs ):
    shutil.rmtree( _TestProjAbs )
    print( "  [DEL] cleaned up _e2e_test_proj" )
_TestNoteAbs = os.path.join( _Cfg.vault_path, _TEST_PATH )
if os.path.isfile( _TestNoteAbs ):
    os.remove( _TestNoteAbs )
    print( "  [DEL] cleaned up _e2e_test.md" )
for _BatchFile in [ _BatchFile1, _BatchFile2 ]:
    if os.path.isfile( _BatchFile ):
        os.remove( _BatchFile )
        print( f"  [DEL] cleaned up {os.path.basename(_BatchFile)}" )
_TodoTestAbs = os.path.join( _Cfg.vault_path, _TodoTestPath )
if os.path.isfile( _TodoTestAbs ):
    os.remove( _TodoTestAbs )
    print( "  [DEL] cleaned up _todo_test.md" )
_ModeTestAbs = os.path.join( _Cfg.vault_path, _ModeTestPath )
if os.path.isfile( _ModeTestAbs ):
    os.remove( _ModeTestAbs )
    print( "  [DEL] cleaned up _e2e_mode_test.md" )
for _PfDir in [ "_e2e_prefill_proj", "_e2e_no_status_proj", "_e2e_gs_proj" ]:
    _PfAbs = os.path.join( _Cfg.vault_path, "workspaces", "LIFEOFDEVELOPMENT", "projects", _PfDir )
    if os.path.isdir( _PfAbs ):
        shutil.rmtree( _PfAbs )
        print( f"  [DEL] cleaned up {_PfDir}" )
if os.path.isdir( _VscodeTempDir ):
    shutil.rmtree( _VscodeTempDir )
    print( "  [DEL] cleaned up _e2e_vscode_* temp dir" )

# 清理 ChromaDB 孤立向量（磁碟已刪但向量殘留）
try:
    _SyncResult = VaultService.sync()
    print( f"  [SYNC] DB cleanup done: deleted={_SyncResult.get( 'index_stats', {} ).get( 'num_deleted', 0 )}" )
except Exception as _SyncErr:
    print( f"  [WARN] cleanup sync error: {_SyncErr}" )

# ── Summary ───────────────────────────────────────────────
print( f"\n=== Result: {_PASS} passed, {_FAIL} failed ===\n" )
sys.exit( 0 if _FAIL == 0 else 1 )
