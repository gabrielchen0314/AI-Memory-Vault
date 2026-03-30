"""
AI Memory Vault — MCP Server (Official SDK)
使用官方 mcp[cli] FastMCP 實作 Model Context Protocol stdio server。
需要 Python 3.10+。

VS Code / Claude Desktop / Cursor 透過 stdio 呼叫此伺服器，
即可直接存取 Vault 的搜尋、同步、讀取、寫入功能。

@author gabrielchen
@version 2.2
@since AI-Memory-Vault 2.0
@date 2026.03.30
"""
import os
import sys

from mcp.server.fastmcp import FastMCP
from services.vault_service import VaultService

mcp = FastMCP( "ai-memory-vault" )


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
        # OS 層：複製 fd 1，將 fd 1 重定向至 fd 2（stderr）
        self._saved_fd1 = os.dup( 1 )
        os.dup2( 2, 1 )

    def __exit__( self, *_ ):
        # 還原 OS 層 fd 1（必須在 Python 層之前還原，確保 FastMCP 能正常寫入回應）
        os.dup2( self._saved_fd1, 1 )
        os.close( self._saved_fd1 )
        # 還原 Python 層 sys.stdout
        sys.stdout = self._old_sys_stdout


# ── Tool: search_vault ─────────────────────────────────────
@mcp.tool()
def search_vault( query: str, category: str = "", doc_type: str = "" ) -> str:
    """
    搜尋 AI Memory Vault 記憶庫（BM25 關鍵字 + 向量語意混合搜尋）。
    可依 category（work/life/knowledge）或 doc_type（rule/project/meeting）過濾。
    """
    with _StdoutToStderr():
        _Result = VaultService.search_formatted( query, category, doc_type )
    return _Result if _Result else "記憶庫中找不到相關資料。"


# ── Tool: sync_vault ───────────────────────────────────────
@mcp.tool()
def sync_vault() -> str:
    """掃描 Vault 所有 .md 檔案，更新 ChromaDB 向量庫（增量同步）。"""
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
    file_path 為相對於 Vault 根目錄的路徑（例如：_system/handoff.md）。
    """
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
    with _StdoutToStderr():
        _Stats, _Error = VaultService.write_note( file_path, content )
    if _Error:
        return _Error

    _Added = _Stats["index_stats"].get( "num_added", 0 )
    _Updated = _Stats["index_stats"].get( "num_updated", 0 )
    return (
        f"Written: {file_path} ({_Stats['chars']} chars). "
        f"Indexed: {_Stats['total_chunks']} chunks (added={_Added}, updated={_Updated})."
    )


# ── Tool: setup_workspace ────────────────────────────────────
@mcp.tool()
def setup_workspace() -> str:
    """
    偵測 Vault Agent 定義與規則，自動建立 VS Code 全域設定檔案。
    已存在的檔案跳過（冪等），不覆蓋使用者手動修改的內容。
    建立內容：templates/agents/*.md → {name}.agent.md、work/*/rules/*.md → vault-coding-rules.instructions.md。
    """
    with _StdoutToStderr():
        from services.workspace_setup import WorkspaceSetupService
        _Stats = WorkspaceSetupService.setup()

    if _Stats["error"]:
        return f"Setup failed: {_Stats['error']}"

    _Parts = []
    if _Stats["agents_created"]:
        _Parts.append( f"Agents created: {', '.join( _Stats['agents_created'] )}" )
    if _Stats["agents_skipped"]:
        _Parts.append( f"Agents skipped (exist): {', '.join( _Stats['agents_skipped'] )}" )
    if _Stats["rules_created"]:
        _Parts.append( "Rules instructions file created." )
    if _Stats["rules_skipped"]:
        _Parts.append( "Rules instructions file already exists, skipped." )

    return "\n".join( _Parts ) if _Parts else "Nothing to setup — all files already exist."


# ── Entry Point ────────────────────────────────────────────
def run_mcp_server():
    """
    MCP Server 入口點（由 main.py --mode mcp 呼叫）。

    Pre-warm：在 mcp.run() 建立 stdio 通道之前，預先載入嵌入模型與向量庫。
    原因：首次 write_note / search_vault 會觸發 400MB 模型懶載入（5-30s），
    期間 C 擴展可能直接寫 fd 1，污染 JSON-RPC 通道並造成工具回應卡頓。
    Pre-warm 在通道建立前完成，所有輸出透過 _StdoutToStderr 導向 stderr。
    """
    with _StdoutToStderr():
        from core.embeddings import get_embeddings
        from core.vectorstore import get_vectorstore, get_record_manager
        from services.workspace_setup import WorkspaceSetupService
        get_embeddings()
        get_vectorstore()
        get_record_manager()
        WorkspaceSetupService.setup()  # 冪等：偵測並補建缺少的 VS Code 設定檔案

    mcp.run( transport="stdio" )

