"""
AI_Engine 單元測試共用 Fixtures。

每個 test function 使用獨立 tmp_path（function scope），避免測試間污染。
VaultService 在 services.scheduler 模組中被 monkeypatch，
使 _sync_write 直接寫至 tmp vault_root，
同時 get_project_status 讀取 tmp vault_root 下的 status.md。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
import os
import sys
import pytest

# ── 確保從 AI_Engine 根目錄載入 ─────────────────────────────
_AI_ENGINE_DIR = os.path.dirname( os.path.dirname( os.path.abspath( __file__ ) ) )
if _AI_ENGINE_DIR not in sys.path:
    sys.path.insert( 0, _AI_ENGINE_DIR )


# ────────────────────────────────────────────────────────────
# vault_root
# ────────────────────────────────────────────────────────────

@pytest.fixture
def vault_root( tmp_path ):
    """建立最小 Vault 目錄骨架（function scope，每個測試獨立）。"""
    _DIRS = [
        "workspaces/TESTORG/projects",
        "personal/reviews/daily",
        "personal/reviews/weekly",
        "personal/reviews/monthly",
        "personal/ai-analysis/weekly",
        "personal/ai-analysis/monthly",
        "workspaces/_global/reviews/daily",
        "workspaces/_global/reviews/weekly",
        "workspaces/_global/reviews/monthly",
    ]
    for _D in _DIRS:
        ( tmp_path / _D.replace( "/", os.sep ) ).mkdir( parents=True, exist_ok=True )
    return tmp_path


# ────────────────────────────────────────────────────────────
# config
# ────────────────────────────────────────────────────────────

@pytest.fixture
def config( vault_root ):
    """最小 AppConfig，vault_path 指向 vault_root。"""
    from config import AppConfig, VaultPaths
    return AppConfig(
        vault_path = str( vault_root ),
        paths      = VaultPaths(),
    )


# ────────────────────────────────────────────────────────────
# patch_vault
# ────────────────────────────────────────────────────────────

@pytest.fixture
def patch_vault( monkeypatch, vault_root ):
    """
    Stub VaultService in services.scheduler：
    - write_note → 直接寫檔至 vault_root（不依賴 ChromaDB）
    - get_project_status → 讀取 vault_root 下的 status.md
    """
    import services.scheduler as _SchedMod
    _Root = str( vault_root )

    class _FakeVault:

        @classmethod
        def write_note( cls, iFilePath: str, iContent: str, iMode: str = "overwrite" ):
            _Abs = os.path.join( _Root, iFilePath )
            os.makedirs( os.path.dirname( _Abs ), exist_ok=True )
            _FileMode = "a" if iMode == "append" else "w"
            _WriteContent = ( "\n" + iContent ) if iMode == "append" else iContent
            with open( _Abs, _FileMode, encoding="utf-8" ) as _F:
                _F.write( _WriteContent )
            return {
                "chars": len( iContent ),
                "total_chunks": 1,
                "index_stats": {},
                "total_files": 1,
            }, None

        @classmethod
        def get_project_status( cls, iOrg: str, iProject: str ):
            _StatusPath = os.path.join(
                _Root, "workspaces", iOrg, "projects", iProject, "status.md"
            )
            if not os.path.isfile( _StatusPath ):
                return None, "status not found"
            with open( _StatusPath, "r", encoding="utf-8" ) as _F:
                _Lines = _F.read().splitlines()
            _Todos = [
                _L.strip()[5:].strip()
                for _L in _Lines
                if _L.strip().startswith( "- [ ]" )
            ]
            return {
                "pending_todos": _Todos,
                "last_updated":  "2026.04.04",
                "context_summary": "test context",
                "path": f"workspaces/{iOrg}/projects/{iProject}/status.md",
            }, None

    monkeypatch.setattr( _SchedMod, "VaultService", _FakeVault )
    yield _FakeVault


# ────────────────────────────────────────────────────────────
# sched
# ────────────────────────────────────────────────────────────

@pytest.fixture
def sched( config, patch_vault ):
    """SchedulerService 實例（VaultService 已 mock）。"""
    from services.scheduler import SchedulerService
    return SchedulerService( config )
