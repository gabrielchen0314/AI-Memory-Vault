"""
AI Memory Vault v3 — MCP Server (Official SDK)
使用官方 mcp[cli] FastMCP 實作 Model Context Protocol stdio server。

VS Code / Claude Desktop / Cursor 透過 stdio 呼叫此伺服器，
即可直接存取 Vault 的搜尋、同步、讀取、寫入功能。

啟動時自動注入 _config/nav.md + _config/handoff.md 作為 MCP instructions，
讓任何 AI Client 連線即取得 Vault 結構與上次交接上下文。

@author gabrielchen
@version 3.5
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP


def _load_vault_instructions() -> str:
    """
    自動掃描 Vault _config/ 目錄，注入所有含 `inject: true` frontmatter 的 .md 檔。
    新增 _config/ 檔案時只需在 frontmatter 加 `inject: true`，無需修改程式碼。
    若 Vault 尚未初始化則回傳空字串。

    Returns:
        拼接後的 instructions 字串（以 --- 分隔各節）。
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

        # 解析 frontmatter：只注入含 inject: true 的檔案
        if not _Raw.startswith( "---" ):
            continue
        _End = _Raw.find( "---", 3 )
        if _End == -1:
            continue
        _Frontmatter = _Raw[3:_End]
        if "inject: true" not in _Frontmatter:
            continue

        # 以 h2 標題包裹（用檔名去掉 .md 作標籤）
        _Label = _FileName[:-3]
        _Sections.append( f"## {_Label}\n\n{_Raw}" )

    return "\n\n---\n\n".join( _Sections ) if _Sections else ""


@asynccontextmanager
async def _lifespan( iServer: FastMCP ) -> AsyncIterator[None]:
    """
    MCP Server 生命週期 hook。

    - startup：VS Code 每次連線時執行 — 確保使用者組織目錄骨架存在。
    - shutdown：VS Code 斷線時執行（預留擴充）。
    """
    # ── startup ────────────────────────────────────────────
    _provision_org_skeleton()
    yield
    # ── shutdown ───────────────────────────────────────────
    # （預留：可在此寫 handoff.md 或清理暫存）


def _provision_org_skeleton() -> None:
    """
    確保 config.user.organizations 每個組織的目錄骨架已建立。
    無論使用者是否曾寫入任何專案檔案，連線時都能看到組織目錄。
    若未設定任何組織，則輸出提示訊息至 stderr。
    """
    from config import ConfigManager

    if not ConfigManager.is_initialized():
        return

    _Config = ConfigManager.load()
    _Orgs = _Config.user.organizations
    if not _Orgs:
        print(
            "[ai-memory-vault] ⚠️  尚未設定任何組織 (organizations)。\n"
            "                     請在終端機執行：\n"
            "                     python main.py --setup-org",
            file=sys.stderr,
        )
        return

    _VaultRoot = _Config.vault_path
    _P = _Config.paths

    for _Org in _Orgs:
        # 確保組織 rules 目錄存在
        _OrgRulesAbs = os.path.join( _VaultRoot, _P.org_rules_dir( _Org ) )
        os.makedirs( _OrgRulesAbs, exist_ok=True )

        # 確保組織 projects 目錄存在
        _OrgProjectsAbs = os.path.join( _VaultRoot, _P.org_projects_dir( _Org ) )
        os.makedirs( _OrgProjectsAbs, exist_ok=True )


mcp = FastMCP( "ai-memory-vault", lifespan=_lifespan, instructions=_load_vault_instructions() )


# ── 工具執行時把 stdout 導向 stderr，防止污染 MCP 通道 ──────
class _StdoutToStderr:
    """
    Context manager: redirect stdout → stderr，保護 MCP stdio 通道純淨。
    同時重定向 Python 層（sys.stdout）與 OS 層（fd 1），
    攔截 C 擴展（torch / chromadb / sentence-transformers）直接寫入 fd 1 的輸出。
    """
    def __enter__( self ):
        self._old_sys_stdout = sys.stdout
        sys.stdout = sys.stderr
        self._saved_fd1 = os.dup( 1 )
        os.dup2( 2, 1 )

    def __exit__( self, *_ ):
        os.dup2( self._saved_fd1, 1 )
        os.close( self._saved_fd1 )
        sys.stdout = self._old_sys_stdout


# ── Tool: search_vault ─────────────────────────────────────
@mcp.tool()
def search_vault( query: str, category: str = "", doc_type: str = "" ) -> str:
    """
    搜尋 AI Memory Vault 記憶庫（BM25 關鍵字 + 向量語意混合搜尋）。
    可依 category（workspaces/personal/knowledge）或 doc_type（rule/project/meeting）過濾。
    """
    from services.vault import VaultService
    with _StdoutToStderr():
        _Result = VaultService.search_formatted( query, category, doc_type )
    return _Result if _Result else "記憶庫中找不到相關資料。"


# ── Tool: sync_vault ───────────────────────────────────────
@mcp.tool()
def sync_vault() -> str:
    """掃描 Vault 所有 .md 檔案，更新 ChromaDB 向量庫（增量同步）。"""
    from services.vault import VaultService
    with _StdoutToStderr():
        _Stats = VaultService.sync()
    return (
        f"Sync complete: {_Stats['total_chunks']} chunks, "
        f"{_Stats['total_files']} files. "
        f"Added={_Stats['index_stats']['num_added']}, "
        f"Updated={_Stats['index_stats']['num_updated']}, "
        f"Deleted={_Stats['index_stats']['num_deleted']}."
    )


# ── Tool: read_note ────────────────────────────────────────
@mcp.tool()
def read_note( file_path: str ) -> str:
    """
    讀取 Vault 中指定筆記的完整原始內容。
    file_path 為相對於 Vault 根目錄的路徑（例如：_config/handoff.md）。
    """
    from services.vault import VaultService
    _Content, _Error = VaultService.read_note( file_path )
    if _Error:
        return _Error
    return _Content


# ── Tool: write_note ───────────────────────────────────────
@mcp.tool()
def write_note( file_path: str, content: str ) -> str:
    """
    寫入或更新 Vault 中的筆記檔案（覆蓋全文），並立即索引至向量庫。
    file_path 為相對於 Vault 根目錄的路徑。
    """
    from services.vault import VaultService
    with _StdoutToStderr():
        _Stats, _Error = VaultService.write_note( file_path, content )
    if _Error:
        return _Error

    _Added = _Stats["index_stats"].get( "num_added", 0 )
    _Updated = _Stats["index_stats"].get( "num_updated", 0 )
    _NewProj = " [NEW PROJECT created]" if _Stats.get( "new_project" ) else ""
    return (
        f"Written: {file_path} ({_Stats['chars']} chars).{_NewProj} "
        f"Indexed: {_Stats['total_chunks']} chunks (added={_Added}, updated={_Updated})."
    )


# ── Tool: generate_project_daily ───────────────────────────
@mcp.tool()
def generate_project_daily( organization: str, project: str, date: str = "" ) -> str:
    """
    生成指定專案的每日詳細進度模板。已存在則回傳路徑不覆蓋。
    organization: 組織名稱（例如 CHINESEGAMER, LIFEOFDEVELOPMENT）。
    project: 專案名稱（例如 game-server, ai-memory-vault）。
    date: 日期 YYYY-MM-DD（預設今天）。
    """
    from config import ConfigManager
    from services.scheduler import SchedulerService
    _Config = ConfigManager.load()
    _Sched = SchedulerService( _Config )
    _Path = _Sched.generate_project_daily( organization, project, date or None )
    return f"Project daily ready: {_Path}"


# ── Tool: generate_daily_review ────────────────────────────
@mcp.tool()
def generate_daily_review( date: str = "", projects: list = [] ) -> str:
    """
    生成每日總進度表（所有專案重點摘要）。每次呼叫都會覆寫內容。
    文本放在 personal/reviews/daily/，連結放在 _global/reviews/daily/。
    date: 日期 YYYY-MM-DD（預設今天）。
    projects: 各專案摘要 list，每項含 organization/project/summary 欄位（選填）。
    """
    from config import ConfigManager
    from services.scheduler import SchedulerService
    _Config = ConfigManager.load()
    _Sched = SchedulerService( _Config )
    _Path = _Sched.generate_daily_summary( date or None, projects or None )
    return f"Daily summary ready: {_Path}"


# ── Tool: generate_weekly_review ───────────────────────────
@mcp.tool()
def generate_weekly_review( date: str = "" ) -> str:
    """
    生成每週總進度表。自動計算 ISO 週數。
    文本放在 personal/reviews/weekly/，連結放在 _global/reviews/weekly/。
    date: 該週內的任一天 YYYY-MM-DD（預設今天）。
    """
    from config import ConfigManager
    from services.scheduler import SchedulerService
    _Config = ConfigManager.load()
    _Sched = SchedulerService( _Config )
    _Path = _Sched.generate_weekly_summary( date or None )
    return f"Weekly summary ready: {_Path}"


# ── Tool: generate_monthly_review ──────────────────────────
@mcp.tool()
def generate_monthly_review( date: str = "" ) -> str:
    """
    生成每月總進度表。
    文本放在 personal/reviews/monthly/，連結放在 _global/reviews/monthly/。
    date: 該月內的任一天 YYYY-MM-DD（預設今天）。
    """
    from config import ConfigManager
    from services.scheduler import SchedulerService
    _Config = ConfigManager.load()
    _Sched = SchedulerService( _Config )
    _Path = _Sched.generate_monthly_summary( date or None )
    return f"Monthly summary ready: {_Path}"


# ── Tool: log_ai_conversation ─────────────────────────────
@mcp.tool()
def log_ai_conversation( organization: str, project: str, session_name: str, content: str ) -> str:
    """
    記錄一次 AI 對話至指定專案的 conversations/ 目錄。
    organization: 組織名稱（例如 LIFEOFDEVELOPMENT）。
    project: 專案名稱（例如 ai-memory-vault）。
    session_name: 對話主題名（例如 vault-setup）。
    content: 對話內容摘要（Markdown 格式）。
    """
    from config import ConfigManager
    from services.scheduler import SchedulerService
    with _StdoutToStderr():
        _Config = ConfigManager.load()
        _Sched = SchedulerService( _Config )
        _Path = _Sched.log_conversation( organization, project, session_name, content )
    return f"Conversation logged: {_Path}"


# ── Tool: generate_ai_weekly_analysis ───────────────
@mcp.tool()
def generate_ai_weekly_analysis( date: str = "" ) -> str:
    """
    生成 AI 對話每週分析模板。自動掃描所有專案當週的對話紀錄。
    內容包含：對話準確率、Token 消耗、每專案統計、評分。
    date: 該週內的任一天 YYYY-MM-DD（預設今天）。
    """
    from config import ConfigManager
    from services.scheduler import SchedulerService
    _Config = ConfigManager.load()
    _Sched = SchedulerService( _Config )
    _Path = _Sched.generate_ai_weekly_analysis( date or None )
    return f"AI weekly analysis ready: {_Path}"


# ── Tool: generate_ai_monthly_analysis ──────────────
@mcp.tool()
def generate_ai_monthly_analysis( date: str = "" ) -> str:
    """
    生成 AI 對話每月分析模板。自動掃描專案對話 + 彙整週報。
    內容包含：趨勢分析、優化建議、月度評分、成長追蹤。
    date: 該月內的任一天 YYYY-MM-DD（預設今天）。
    """
    from config import ConfigManager
    from services.scheduler import SchedulerService
    _Config = ConfigManager.load()
    _Sched = SchedulerService( _Config )
    _Path = _Sched.generate_ai_monthly_analysis( date or None )
    return f"AI monthly analysis ready: {_Path}"


# ── Tool: generate_project_status ─────────────────────────
@mcp.tool()
def generate_project_status( organization: str, project: str ) -> str:
    """
    生成指定專案的 status.md 模板（待辦 + 工作脈絡 + 決策記錄）。
    冪等：已存在則回傳路徑，不覆蓋現有內容。
    organization: 組織名稱（例如 LIFEOFDEVELOPMENT）。
    project: 專案名稱（例如 ai-memory-vault）。
    """
    from config import ConfigManager
    from services.scheduler import SchedulerService
    _Config = ConfigManager.load()
    _Sched = SchedulerService( _Config )
    _Path = _Sched.generate_project_status( organization, project )
    return f"Project status ready: {_Path}"


# ── Tool: list_projects ────────────────────────────────────
@mcp.tool()
def list_projects() -> str:
    """
    列出 Vault 中所有組織及其下的專案清單。
    回傳格式化的 Markdown 表格，每個組織一個區段。
    """
    import os
    from config import ConfigManager
    _Config = ConfigManager.load()
    _P = _Config.paths
    _WorkspacesAbs = os.path.join( _Config.vault_path, _P.workspaces )

    if not os.path.isdir( _WorkspacesAbs ):
        return "Vault workspaces 目錄不存在。"

    _Lines = []
    for _OrgEntry in sorted( os.listdir( _WorkspacesAbs ) ):
        if _OrgEntry.startswith( "_" ):
            continue
        _OrgDir = os.path.join( _WorkspacesAbs, _OrgEntry )
        if not os.path.isdir( _OrgDir ):
            continue

        _ProjectsDir = os.path.join( _OrgDir, _P.org_projects )
        _Projects = []
        if os.path.isdir( _ProjectsDir ):
            for _ProjEntry in sorted( os.listdir( _ProjectsDir ) ):
                if os.path.isdir( os.path.join( _ProjectsDir, _ProjEntry ) ):
                    _Projects.append( _ProjEntry )

        _Lines.append( f"\n## {_OrgEntry}\n" )
        if _Projects:
            for _Proj in _Projects:
                _StatusPath = _P.project_status_file( _OrgEntry, _Proj )
                _StatusAbs = os.path.join( _Config.vault_path, _StatusPath )
                _HasStatus = "✅" if os.path.isfile( _StatusAbs ) else "⬜"
                _Lines.append( f"- {_HasStatus} `{_Proj}`" )
        else:
            _Lines.append( "（尚無專案）" )

    return "\n".join( _Lines ).strip() if _Lines else "未找到任何組織或專案。"


# ── Tool: batch_write_notes ────────────────────────────────
@mcp.tool()
def batch_write_notes( notes: list ) -> str:
    """
    批次寫入多個 Vault 筆記，一次 ChromaDB 索引（比多次 write_note 效率高）。
    notes: list of {"file_path": str, "content": str, "mode": "overwrite"|"append"}
           mode 為可選，預設 overwrite。
    回傳每筆寫入結果 + 總索引統計。
    """
    from services.vault import VaultService
    with _StdoutToStderr():
        _Results, _BatchStats, _Error = VaultService.batch_write_notes( notes )
    if _Error:
        return _Error

    _OkCount = sum( 1 for _R in _Results if _R["ok"] )
    _FailCount = len( _Results ) - _OkCount
    _Added = _BatchStats["index_stats"].get( "num_added", 0 )
    _Updated = _BatchStats["index_stats"].get( "num_updated", 0 )

    _Lines = [ f"Batch write: {_OkCount} ok, {_FailCount} failed. Indexed: {_BatchStats['total_chunks']} chunks (added={_Added}, updated={_Updated})." ]
    for _R in _Results:
        if _R["ok"]:
            _Lines.append( f"  OK  {_R['file_path']} ({_R['chars']} chars)" )
        else:
            _Lines.append( f"  ERR {_R['file_path']} — {_R['error']}" )
    return "\n".join( _Lines )


# ── Tool: update_todo ──────────────────────────────────────
@mcp.tool()
def update_todo( file_path: str, todo_text: str, done: bool ) -> str:
    """
    在指定 .md 檔案的 todo 列表中更新一個項目的勾選狀態（不全文覆蓋）。
    file_path: 相對於 Vault 根目錄的路徑（通常是某個 status.md）。
    todo_text: todo 項目的部分文字（用來比對對應行）。
    done: True = 標為完成 [x]，False = 標為未完成 [ ]。
    """
    from services.vault import VaultService
    with _StdoutToStderr():
        _Stats, _Error = VaultService.update_todo( file_path, todo_text, done )
    if _Error:
        return _Error
    if not _Stats["matched"]:
        return f"no match: 找不到包含 '{todo_text}' 的 todo 行。"
    _Added = _Stats["index_stats"].get( "num_added", 0 )
    _Updated = _Stats["index_stats"].get( "num_updated", 0 )
    return (
        f"Todo updated: {_Stats['updated_line']}\n"
        f"Indexed: {_Stats['total_chunks']} chunks (added={_Added}, updated={_Updated})."
    )


# ── Tool: check_vault_integrity ──────────────────────────────
@mcp.tool()
def check_vault_integrity() -> str:
    """
    比對 ChromaDB 已索引的 source 路徑與 Vault 檔案系統，
    找出孤立記錄（DB 中存在但對應 .md 檔案已刪除）。
    可用於定期清理或 debug sync 異常。
    """
    from services.vault import VaultService
    with _StdoutToStderr():
        _Result, _Err = VaultService.check_integrity()
    if _Err:
        return f"Error: {_Err}"
    _Orphaned = _Result["orphaned"]
    _Lines = [
        f"DB sources: {_Result['total_db_sources']}",
        f"Filesystem .md: {_Result['total_files']}",
        f"Orphaned: {len( _Orphaned )}",
    ]
    if _Orphaned:
        _Lines.append( "\nOrphaned sources:" )
        _Lines.extend( f"  - {_S}" for _S in _Orphaned )
    return "\n".join( _Lines )


# ── Tool: get_project_status ────────────────────────────────
@mcp.tool()
def get_project_status( organization: str, project: str ) -> str:
    """
    讀取指定專案的 status.md 並回傳結構化資料：
    待辦事項清單、已完成數量、工作脈絡。
    比 read_note 更適合 AI 讀取待辦項目（不需解析 Markdown）。
    organization: 組織名稱。
    project: 專案名稱。
    """
    from services.vault import VaultService
    with _StdoutToStderr():
        _Result, _Err = VaultService.get_project_status( organization, project )
    if _Err:
        return f"Error: {_Err}"
    _Pending = _Result["pending_todos"]
    _Lines = [
        f"path: {_Result['path']}",
        f"last_updated: {_Result['last_updated']}",
        f"pending_todos: {len( _Pending )}",
        f"completed_count: {_Result['completed_count']}",
    ]
    if _Pending:
        _Lines.append( "\nPending:" )
        _Lines.extend( f"  - {_T}" for _T in _Pending )
    if _Result["context_summary"]:
        _Lines.append( f"\nContext:\n{_Result['context_summary']}" )
    return "\n".join( _Lines )


# ── Tool: delete_note ─────────────────────────────────────
@mcp.tool()
def delete_note( file_path: str ) -> str:
    """
    刪除 Vault 中的指定 .md 筆記，並移除 ChromaDB 中對應的所有向量記錄。
    file_path 為相對於 Vault 根目錄的路徑。
    注意：此操作不可逆，請確認後再呼叫。
    """
    from services.vault import VaultService
    with _StdoutToStderr():
        _Stats, _Error = VaultService.delete_note( file_path )
    if _Error:
        return f"Error: {_Error}"
    return f"Deleted: {file_path}. Removed {_Stats['deleted_chunks']} chunks from DB."


def run_mcp_server() -> None:
    """啟動 MCP stdio 伺服器。"""
    mcp.run( transport="stdio" )
