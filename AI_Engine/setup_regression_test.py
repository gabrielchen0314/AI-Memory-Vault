"""
setup.py 回歸測試腳本
驗證 SetupService.run_setup() 的冪等性與目錄/檔案建立正確性。
使用暫存目錄，不影響真實 Vault。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
import os
import sys
import shutil
import tempfile
import io
import contextlib

os.chdir( os.path.dirname( os.path.abspath( __file__ ) ) )

from config import AppConfig, DatabaseConfig, EmbeddingConfig, UserConfig, VaultPaths, ConfigManager
import core.vectorstore as vectorstore
import core.embeddings as embeddings

_PASS = 0
_FAIL = 0


@contextlib.contextmanager
def _suppress_stdout():
    """壓制 stdout 避免 setup emoji 造成 CP950 編碼錯誤。"""
    _Buf = io.StringIO()
    with contextlib.redirect_stdout( _Buf ):
        yield


def check( iLabel: str, iCondition: bool, iDetail: str = "" ):
    """測試檢查點輸出。"""
    global _PASS, _FAIL
    if iCondition:
        _PASS += 1
        print( f"  [PASS] {iLabel}" )
    else:
        _FAIL += 1
        print( f"  [FAIL] {iLabel}" + ( f" -- {iDetail}" if iDetail else "" ) )


def _make_test_config( iVaultPath: str ) -> AppConfig:
    """
    建立指向暫存目錄的測試設定。
    DatabaseConfig 的 chroma_dir / record_db 使用絕對路徑字串，
    Path(ENGINE_DIR) / absolute_path 在 Python 中會以絕對路徑為主，
    因此 get_chroma_path() / get_record_db_url() 均指向暫存目錄。
    """
    _ChromaAbs = os.path.join( iVaultPath, "chroma_db" )
    _RecordAbs = os.path.join( iVaultPath, "chroma_db", "record_manager_cache.sql" )
    _Cfg = AppConfig(
        vault_path=iVaultPath,
        database=DatabaseConfig(
            chroma_dir=_ChromaAbs,
            record_db=_RecordAbs,
            collection_name="test_vault",
        ),
        embedding=EmbeddingConfig( model="all-MiniLM-L6-v2" ),
        user=UserConfig( name="test_user", organizations=["TEST_ORG"] ),
        paths=VaultPaths(),
    )
    return _Cfg


print( "\n=== Setup Regression Test ===\n" )

# ── 真實 config.json 備份（SetupService.run_setup 會覆寫它）──
from config import CONFIG_FILE
import json
_ConfigBackup = None
if CONFIG_FILE.exists():
    with open( CONFIG_FILE, "r", encoding="utf-8" ) as _F:
        _ConfigBackup = _F.read()

# ── 建立暫存目錄 ───────────────────────────────────────────
_TempDir = tempfile.mkdtemp( prefix="vault_setup_test_" )
print( f"Temp dir: {_TempDir}" )

try:
    _Cfg = _make_test_config( _TempDir )

    # 初始化嵌入模型（setup 流程中需要）
    embeddings.initialize( _Cfg.embedding.model )
    vectorstore.initialize(
        _Cfg.database.get_chroma_path(),
        _Cfg.database.get_record_db_url(),
        _Cfg.database.collection_name,
    )

    # ── Step 1: 首次 setup ─────────────────────────────────
    print( "\nStep 1: run_setup (first time)" )
    from services.setup import SetupService
    with _suppress_stdout():
        _Stats1 = SetupService.run_setup( _Cfg )
    check( "returns dict", isinstance( _Stats1, dict ) )
    check( "dirs_created > 0", _Stats1.get( "dirs_created", 0 ) > 0 )
    check( "db_initialized", _Stats1.get( "db_initialized" ) is True )
    check( "chunks_indexed >= 0", _Stats1.get( "chunks_indexed", -1 ) >= 0 )

    # ── Step 2: 必要目錄存在 ───────────────────────────────
    print( "\nStep 2: required dirs exist" )
    _P = _Cfg.paths
    for _RelDir in [
        _P.config,
        _P.workspaces,
        _P.personal,
        _P.knowledge,
        _P.templates,
        _P.attachments,
        _P.personal_reviews_daily,
        _P.personal_reviews_weekly,
        _P.personal_reviews_monthly,
    ]:
        _AbsDir = os.path.join( _TempDir, _RelDir )
        check( f"dir exists: {_RelDir}", os.path.isdir( _AbsDir ) )

    # ── Step 3: 初始檔案存在 ───────────────────────────────
    print( "\nStep 3: initial files exist" )
    for _RelFile in [
        f"{_P.config}/nav.md",
        f"{_P.config}/handoff.md",
    ]:
        _AbsFile = os.path.join( _TempDir, _RelFile )
        check( f"file exists: {_RelFile}", os.path.isfile( _AbsFile ) )

    # ── Step 4: 冪等性（第二次呼叫不新增目錄）─────────────
    print( "\nStep 4: idempotency (second run)" )
    # 重置 lru_cache，讓 vectorstore 重新指向同一 DB
    vectorstore.get_vectorstore.cache_clear()
    vectorstore.get_record_manager.cache_clear()
    vectorstore.initialize(
        _Cfg.database.get_chroma_path(),
        _Cfg.database.get_record_db_url(),
        _Cfg.database.collection_name,
    )
    with _suppress_stdout():
        _Stats2 = SetupService.run_setup( _Cfg )
    check( "second run returns dict", isinstance( _Stats2, dict ) )
    check( "second run dirs_created == 0 (all exist)", _Stats2.get( "dirs_created", -1 ) == 0 )
    check( "second run files_created == 0 (all exist)", _Stats2.get( "files_created", -1 ) == 0 )

    # ── Step 5: ChromaDB 目錄存在 ──────────────────────────
    print( "\nStep 5: ChromaDB created" )
    _ChromaDir = _Cfg.database.get_chroma_path()
    check( "chroma_db dir exists", os.path.isdir( _ChromaDir ) )
    check( "record_manager sqlite exists", os.path.isfile(
        os.path.join( _ChromaDir, "record_manager_cache.sql" )
    ) )

    # ── Step 6: nav.md 內容包含 Vault 路徑關鍵字 ──────────
    print( "\nStep 6: nav.md content" )
    _NavPath = os.path.join( _TempDir, _P.config, "nav.md" )
    with open( _NavPath, "r", encoding="utf-8" ) as _F:
        _NavContent = _F.read()
    check( "nav.md contains 'workspaces'", "workspaces" in _NavContent )
    check( "nav.md contains 'personal'", "personal" in _NavContent )

finally:
    # ── Cleanup ───────────────────────────────────────────
    shutil.rmtree( _TempDir, ignore_errors=True )
    print( f"\n  [DEL] cleaned up {_TempDir}" )

    # 還原真實 config.json（SetupService.run_setup 會覆寫它）
    if _ConfigBackup is not None:
        with open( CONFIG_FILE, "w", encoding="utf-8" ) as _F:
            _F.write( _ConfigBackup )
        print( "  [RESTORE] config.json restored" )

# ── Summary ───────────────────────────────────────────────
print( f"\n=== Result: {_PASS} passed, {_FAIL} failed ===\n" )
sys.exit( 0 if _FAIL == 0 else 1 )
