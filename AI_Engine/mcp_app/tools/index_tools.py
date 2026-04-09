"""
MCP 工具模組 — 向量索引管理
check_vault_integrity / clean_orphans / check_index_status / reindex_vault

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.08
"""
from __future__ import annotations
from mcp_app.utils import suppress_stdout


def register( mcp ):
    """將向量索引管理工具註冊到 MCP Server。"""

    @mcp.tool()
    @suppress_stdout
    def check_vault_integrity() -> str:
        """
        比對 ChromaDB 已索引的 source 路徑與 Vault 檔案系統，
        找出孤立記錄（DB 中存在但對應 .md 檔案已刪除）。
        可用於定期清理或 debug sync 異常。
        """
        from services.vault import VaultService
        _Result, _Err = VaultService.check_integrity()
        if _Err:
            return f"❌ {_Err}"
        _Orphaned = _Result["orphaned"]
        _Lines = [
            f"DB 向量來源：{_Result['total_db_sources']} 筆",
            f"檔案系統 .md：{_Result['total_files']} 個",
            f"孤立向量：{len( _Orphaned )} 筆",
        ]
        if _Orphaned:
            _Lines.append( "\n孤立來源：" )
            _Lines.extend( f"  - {_S}" for _S in _Orphaned )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def clean_orphans() -> str:
        """
        移除 ChromaDB 中所有孤立向量記錄（來源 .md 已刪除但 DB 仍存在）。
        比 reindex_vault 更輕量：只外科手術式刪除孤立記錄，不重新建立全部索引。
        通常在使用 delete_note 或手動刪除 .md 後呼叫，可快速清理 DB。
        """
        from services.vault import VaultService
        _Result, _Err = VaultService.clean_orphans()
        if _Err:
            return f"❌ {_Err}"
        _Removed  = _Result["removed"]
        _NSources = len( _Result["orphaned_sources"] )
        if _Removed == 0:
            return "✅ DB 已整潔，沒有孤立向量記錄。"
        _Lines = [
            f"已清除 {_Removed} 個孤立向量，來自 {_NSources} 個來源。",
        ]
        for _S in _Result["orphaned_sources"][:20]:
            _Lines.append( f"  - {_S}" )
        if _NSources > 20:
            _Lines.append( f"  ... 及其他 {_NSources - 20} 筆" )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def check_index_status() -> str:
        """
        檢查 ChromaDB 向量索引是否因設定變更而需要重建。
        比對目前設定（embedding_model、chunk_size、chunk_overlap、collection_name）
        與上次建立索引時的設定，若有差異則提示需執行 reindex_vault。
        """
        from config import ConfigManager
        from core.migration import MigrationManager
        _Config = ConfigManager.load()
        _NeedsReindex, _Changes = MigrationManager.check( _Config )
        if not _NeedsReindex:
            return "✅ 向量索引狀態正常，無需重建。"
        _Desc = MigrationManager.describe_changes( _Changes )
        return f"⚠️  索引已過期——以下設定已變更：\n{_Desc}\n請執行 reindex_vault() 重建索引。"

    @mcp.tool()
    @suppress_stdout
    def reindex_vault() -> str:
        """
        清除 ChromaDB 向量索引並從頭重建（等同 CLI 的 --reindex 指令）。
        當 embedding_model、chunk_size、chunk_overlap 或 collection_name 設定變更後呼叫。
        警告：此操作會清除現有索引，重建期間搜尋功能無法使用（通常 < 1 分鐘）。
        """
        from config import ConfigManager
        from core.migration import MigrationManager
        from services.vault import VaultService
        _Config = ConfigManager.load()
        _Ok, _Msg = MigrationManager.reset_index( _Config )
        if not _Ok:
            return f"❌ 重置索引失敗：{_Msg}"
        _Stats = VaultService.sync()
        return (
            f"重建完成：{_Stats['total_chunks']} chunks，{_Stats['total_files']} 個檔案\n"
            f"新增={_Stats['index_stats']['num_added']}，"
            f"更新={_Stats['index_stats']['num_updated']}，"
            f"刪除={_Stats['index_stats']['num_deleted']}"
        )
