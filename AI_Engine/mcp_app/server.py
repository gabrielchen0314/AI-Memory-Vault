"""
AI Memory Vault v3 — MCP Server (Official SDK)
使用官方 mcp[cli] FastMCP 實作 Model Context Protocol stdio server。

VS Code / Claude Desktop / Cursor 透過 stdio 呼叫此伺服器，
即可直接存取 Vault 的搜尋、同步、讀取、寫入功能。

啟動時自動注入 _config/ 含 inject: true 的 .md 作為 MCP instructions，
讓任何 AI Client 連線即取得 Vault 結構與上次交接上下文。

v3.5 — 拆分工具至 mcp_app/tools/ 子模組，SchedulerService 改為 lifespan 單例。
v3.6 — 新增 Agent/Skill/Instinct 系統（agent_tools + instinct_tools），共 39 個 MCP 工具。

@author gabrielchen
@version 3.6
@since AI-Memory-Vault 3.0
@date 2026.04.10
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from core.logger import get_logger

_logger = get_logger( __name__ )

# ── 模組級單例（lifespan 啟動時填入） ──────────────────────
_g_Scheduler = None
_g_Instinct  = None


def _get_scheduler():
    """取得 SchedulerService 單例。由 tool 模組在呼叫時透過閉包存取。"""
    return _g_Scheduler


def _get_instinct():
    """取得 InstinctService 單例。由 tool 模組在呼叫時透過閉包存取。"""
    return _g_Instinct


# ── Instructions 載入 ──────────────────────────────────────
def _load_vault_instructions() -> str:
    """
    自動掃描 Vault _config/ 目錄，注入所有含 `inject: true` frontmatter 的 .md 檔。
    新增 _config/ 檔案時只需在 frontmatter 加 `inject: true`，無需修改程式碼。
    若 Vault 尚未初始化則回傳空字串。
    """
    from config import ConfigManager

    if not ConfigManager.is_initialized():
        return ""

    _Config    = ConfigManager.load()
    _VaultRoot = _Config.vault_path
    _ConfigDir = os.path.join( _VaultRoot, _Config.paths.config )
    _Sections  = []

    if not os.path.isdir( _ConfigDir ):
        return ""

    for _FileName in sorted( os.listdir( _ConfigDir ) ):
        if not _FileName.endswith( ".md" ):
            continue
        _AbsPath = os.path.join( _ConfigDir, _FileName )
        try:
            with open( _AbsPath, "r", encoding="utf-8" ) as _F:
                _Raw = _F.read()
        except OSError:
            continue

        if not _Raw.startswith( "---" ):
            continue
        _End = _Raw.find( "---", 3 )
        if _End == -1:
            continue
        _Frontmatter = _Raw[3:_End]
        if "inject: true" not in _Frontmatter:
            continue

        _Label = _FileName[:-3]
        _Sections.append( f"## {_Label}\n\n{_Raw}" )

    return "\n\n---\n\n".join( _Sections ) if _Sections else ""


# ── Lifespan ───────────────────────────────────────────────
@asynccontextmanager
async def _lifespan( _ ) -> AsyncIterator[None]:
    """
    MCP Server 生命週期 hook。

    - startup：建立 SchedulerService 單例 + 確保組織目錄骨架。
    - shutdown：預留擴充。
    """
    global _g_Scheduler, _g_Instinct
    # ── startup ────────────────────────────────────
    _provision_org_skeleton()
    try:
        from config import ConfigManager
        if ConfigManager.is_initialized():
            from services.scheduler import SchedulerService
            from services.instinct import InstinctService
            _Config      = ConfigManager.load()
            _g_Scheduler = SchedulerService( _Config )
            _g_Instinct  = InstinctService( _Config )
            _logger.info( "SchedulerService + InstinctService singletons initialized" )
    except Exception as _E:
        _logger.warning( "Failed to init services: %s", _E )
    yield
    # ── shutdown ───────────────────────────────────
    _g_Scheduler = None
    _g_Instinct  = None


def _provision_org_skeleton() -> None:
    """
    確保 config.user.organizations 每個組織的目錄骨架已建立。
    無論使用者是否曾寫入任何專案檔案，連線時都能看到組織目錄。
    """
    from config import ConfigManager

    if not ConfigManager.is_initialized():
        return

    _Config = ConfigManager.load()
    _Orgs = _Config.user.organizations
    if not _Orgs:
        _logger.warning(
            "尚未設定任何組織 (organizations)。請在終端機執行：python main.py --setup-org"
        )
        return

    _VaultRoot = _Config.vault_path
    _P = _Config.paths

    for _Org in _Orgs:
        _OrgRulesAbs = os.path.join( _VaultRoot, _P.org_rules_dir( _Org ) )
        os.makedirs( _OrgRulesAbs, exist_ok=True )
        _OrgProjectsAbs = os.path.join( _VaultRoot, _P.org_projects_dir( _Org ) )
        os.makedirs( _OrgProjectsAbs, exist_ok=True )


# ── FastMCP 實例 + 工具註冊 ────────────────────────────────
mcp = FastMCP( "ai-memory-vault", lifespan=_lifespan, instructions=_load_vault_instructions() )

from mcp_app.tools import vault_tools, scheduler_tools, project_tools, todo_tools, index_tools, agent_tools, instinct_tools

vault_tools.register( mcp )
scheduler_tools.register( mcp, _get_scheduler )
project_tools.register( mcp )
todo_tools.register( mcp )
index_tools.register( mcp )
agent_tools.register( mcp )
instinct_tools.register( mcp, _get_instinct )

_logger.info(
    "MCP tools registered: vault=%d, scheduler=%d, project=%d, todo=%d, index=%d, agent=%d, instinct=%d → total=%d",
    10, 10, 3, 3, 4, 4, 5,
    10 + 10 + 3 + 3 + 4 + 4 + 5,
)


def run_mcp_server() -> None:
    """啟動 MCP stdio 伺服器。"""
    mcp.run( transport="stdio" )
