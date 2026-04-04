"""
Phase 18 E2E 測試腳本
測試 write → search → read → batch → update_todo → delete_note → vscode_integration → auto_scheduler 完整流程

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


print( "\n=== Phase 15 E2E Test ===\n" )

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
check( "search result contains test marker", "vault_e2e_unique_marker_x7q9" in _SearchResult )

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
check( "job_count == 3 after start", _AutoSched.job_count() == 3, f"got {_AutoSched.job_count()}" )
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
if os.path.isdir( _VscodeTempDir ):
    shutil.rmtree( _VscodeTempDir )
    print( "  [DEL] cleaned up _e2e_vscode_* temp dir" )

# ── Summary ───────────────────────────────────────────────
print( f"\n=== Result: {_PASS} passed, {_FAIL} failed ===\n" )
sys.exit( 0 if _FAIL == 0 else 1 )
