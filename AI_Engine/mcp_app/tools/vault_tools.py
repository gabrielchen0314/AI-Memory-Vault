"""
MCP 工具模組 — Vault 筆記操作
search / read / write / edit / delete / rename / list / batch_write / grep

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.08
"""
from __future__ import annotations
from mcp_app.utils import suppress_stdout


def register( mcp ):
    """將 Vault 筆記操作工具註冊到 MCP Server。"""

    @mcp.tool()
    @suppress_stdout
    def search_vault( query: str, category: str = "", doc_type: str = "", mode: str = "" ) -> str:
        """
        搜尋 AI Memory Vault 記憶庫（BM25 關鍵字 + 向量語意混合搜尋）。
        可依 category（workspaces/personal/knowledge）或 doc_type（rule/project/meeting）過濾。
        mode 可指定搜尋偏好：\"keyword\"（BM25 偏重，適合精確關鍵字）、\"semantic\"（Vector 偏重，適合語意查詢）；
        留空為均衡模式（BM25 40% + Vector 60%）。
        """
        from services.vault import VaultService
        return VaultService.search_formatted( query, category, doc_type, mode )

    @mcp.tool()
    @suppress_stdout
    def sync_vault() -> str:
        """
        對 Vault 所有 .md 執行增量向量同步，自動清除已刪除檔案的孤立記錄。
        通常在手動移動/刪除 .md 後呼叫。VS Code 以外的編輯器修改後也建議呼叫一次。
        """
        from services.vault import VaultService
        _Stats = VaultService.sync()
        return (
            f"同步完成：{_Stats['total_chunks']} chunks，{_Stats['total_files']} 個檔案\n"
            f"新增={_Stats['index_stats']['num_added']}，"
            f"更新={_Stats['index_stats']['num_updated']}，"
            f"刪除={_Stats['index_stats']['num_deleted']}"
        )

    @mcp.tool()
    @suppress_stdout
    def read_note( file_path: str ) -> str:
        """
        讀取 Vault 中指定筆記的完整原始內容。
        file_path 為相對於 Vault 根目錄的路徑，例如 \"knowledge/chromadb-sync.md\"。
        """
        from services.vault import VaultService
        _Content, _Error = VaultService.read_note( file_path )
        return _Error if _Error else _Content

    @mcp.tool()
    @suppress_stdout
    def write_note( file_path: str, content: str, mode: str = "overwrite" ) -> str:
        """
        寫入或更新 Vault 中的筆記檔案，並立即索引至向量庫。
        file_path 為相對於 Vault 根目錄的路徑。
        mode: "overwrite"（預設，全覆蓋）或 "append"（追加內容到現有檔案末尾）。
        """
        from services.vault import VaultService
        _Stats, _Error = VaultService.write_note( file_path, content, mode )
        if _Error:
            return _Error
        _Added = _Stats["index_stats"].get( "num_added", 0 )
        _Updated = _Stats["index_stats"].get( "num_updated", 0 )
        _NewProj = "（已建立新專案目錄）" if _Stats.get( "new_project" ) else ""
        return (
            f"已寫入：{file_path}（{_Stats['chars']} 字元）{_NewProj}\n"
            f"已索引：{_Stats['total_chunks']} chunks（新增={_Added}，更新={_Updated}）"
        )

    @mcp.tool()
    @suppress_stdout
    def edit_note( file_path: str, old_text: str, new_text: str ) -> str:
        """
        在指定 .md 檔案中執行精確的文字替換（不全文覆寫）。
        old_text 必須在檔案中恰好出現一次，將被替換為 new_text。
        適用於局部修改筆記內容，比 write_note(overwrite) 更安全。
        """
        from services.vault import VaultService
        _Stats, _Error = VaultService.edit_note( file_path, old_text, new_text )
        if _Error:
            return _Error
        return (
            f"已編輯：{file_path}（移除 {_Stats['chars_removed']} 字元，新增 {_Stats['chars_added']} 字元）\n"
            f"已索引：{_Stats['total_chunks']} chunks"
        )

    @mcp.tool()
    @suppress_stdout
    def delete_note( file_path: str ) -> str:
        """
        刪除 Vault 中的指定 .md 筆記，並移除 ChromaDB 中對應的所有向量記錄。
        file_path 為相對於 Vault 根目錄的路徑。
        注意：此操作不可逆，請確認後再呼叫。
        """
        from services.vault import VaultService
        _Stats, _Error = VaultService.delete_note( file_path )
        if _Error:
            return _Error
        return f"已刪除：{file_path}（移除 {_Stats['deleted_chunks']} 個向量）"

    @mcp.tool()
    @suppress_stdout
    def rename_note( old_path: str, new_path: str ) -> str:
        """
        將 Vault 中的 .md 筆記移動（重新命名）到新路徑，並自動同步 ChromaDB 向量索引。
        - old_path：來源路徑（相對於 Vault 根目錄）。
        - new_path：目標路徑（相對於 Vault 根目錄，不可與現有檔案相同）。
        目標目錄若不存在會自動建立。
        """
        from services.vault import VaultService
        _Stats, _Error = VaultService.rename_note( old_path, new_path )
        if _Error:
            return _Error
        return (
            f"已移動：{_Stats['old_path']} → {_Stats['new_path']}\n"
            f"移除 {_Stats['deleted_chunks']} 舊 chunks，索引 {_Stats['indexed_chunks']} 新 chunks"
        )

    @mcp.tool()
    @suppress_stdout
    def list_notes( path: str = "", recursive: bool = False, max_results: int = 50 ) -> str:
        """
        列出 Vault 中指定目錄下所有 .md 檔案，方便在 read_note 前先探索結構。
        - path：相對於 Vault 根目錄的目錄路徑（空字串 = 根目錄）。
        - recursive：True = 遞迴包含所有子目錄；False（預設）= 僅目前層。
        - max_results：最多回傳幾筆（預設 50），避免大目錄浪費 Token。
        """
        import datetime
        from services.vault import VaultService
        _Result, _Err = VaultService.list_notes( path, recursive )
        if _Err:
            return f"❌ {_Err}"
        _Total = _Result["total"]
        if _Total == 0:
            return f"找不到任何 .md 檔案：'{path or '/'}' ({'遞迴' if recursive else '非遞迴'})"
        _Notes = _Result["notes"][:max_results]
        _Truncated = _Total > max_results
        _Lines = [
            f"### {_Result['path']}  （顯示 {len(_Notes)}/{_Total} 個檔案{'  遞迴' if recursive else ''}）",
            "",
        ]
        for _N in _Notes:
            _Dt = datetime.datetime.fromtimestamp( _N["modified"] ).strftime( "%Y-%m-%d" )
            _Kb = f"{_N['size'] / 1024:.1f}KB" if _N["size"] >= 1024 else f"{_N['size']}B"
            _Lines.append( f"- `{_N['path']}`  ({_Kb}, {_Dt})" )
        if _Truncated:
            _Lines.append( f"\n> ⚠️ 還有 {_Total - max_results} 個檔案未顯示，請縮小 path 範圍或增加 max_results。" )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def batch_write_notes( notes: list ) -> str:
        """
        批次寫入多個 Vault 筆記，一次 ChromaDB 索引（比多次 write_note 效率高）。
        notes: list of {"file_path": str, "content": str, "mode": "overwrite"|"append"}
        """
        from services.vault import VaultService
        _Results, _BatchStats, _Error = VaultService.batch_write_notes( notes )
        if _Error:
            return _Error
        _OkCount = sum( 1 for _R in _Results if _R["ok"] )
        _FailCount = len( _Results ) - _OkCount
        _Added = _BatchStats["index_stats"].get( "num_added", 0 )
        _Updated = _BatchStats["index_stats"].get( "num_updated", 0 )
        _Lines = [ f"批次寫入：{_OkCount} 成功，{_FailCount} 失敗。已索引：{_BatchStats['total_chunks']} chunks（新增={_Added}，更新={_Updated}）" ]
        for _R in _Results:
            if _R["ok"]:
                _Lines.append( f"  ✅  {_R['file_path']}（{_R['chars']} 字元）" )
            else:
                _Lines.append( f"  ❌  {_R['file_path']} — {_R['error']}" )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def grep_vault( pattern: str, path: str = "", is_regex: bool = False, max_results: int = 50 ) -> str:
        """
        在 Vault .md 檔案中執行純文字或正規表達式搜尋（精確比對，非語意搜尋）。
        類似 grep / ripgrep。適用於需要精確關鍵字、檔案內容定位的場景。
        - pattern：搜尋文字或正規表達式。
        - path：限定搜尋目錄（相對路徑；空字串 = 全 Vault）。
        - is_regex：True = 以正規表達式比對；False（預設）= 純文字（不分大小寫）。
        - max_results：最大回傳筆數（預設 50）。
        """
        from services.vault import VaultService
        _Results, _Err = VaultService.grep( pattern, path, is_regex, max_results )
        if _Err:
            return _Err
        if not _Results:
            return f"找不到符合 '{pattern}' 的結果（搜尋範圍：'{path or '/'}'）"
        _Lines = [ f"找到 {len(_Results)} 筆：", "" ]
        for _R in _Results:
            _Lines.append( f"  {_R['file']}:{_R['line']}:{_R['col']}  {_R['text']}" )
        return "\n".join( _Lines )
