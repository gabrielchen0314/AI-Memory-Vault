"""
MCP 工具模組 — Todo 管理
update_todo / add_todo / remove_todo

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.08
"""
from __future__ import annotations
from mcp_app.utils import suppress_stdout


def register( mcp ):
    """將 Todo 管理工具註冊到 MCP Server。"""

    @mcp.tool()
    @suppress_stdout
    def update_todo( file_path: str, todo_text: str, done: bool ) -> str:
        """
        在指定 .md 檔案的 todo 列表中更新一個項目的勾選狀態（不全文覆蓋）。
        file_path: 相對於 Vault 根目錄的路徑（通常是某個 status.md）。
        todo_text: todo 項目的部分文字（用來比對對應行）。
        done: True = 標為完成 [x]，False = 標為未完成 [ ]。
        """
        from services.vault import VaultService
        _Stats, _Error = VaultService.update_todo( file_path, todo_text, done )
        if _Error:
            return _Error
        if not _Stats["matched"]:
            return f"找不到包含 '{todo_text}' 的 todo 項目。"
        _Added = _Stats["index_stats"].get( "num_added", 0 )
        _Updated = _Stats["index_stats"].get( "num_updated", 0 )
        return (
            f"Todo 已更新：{_Stats['updated_line']}\n"
            f"已索引：{_Stats['total_chunks']} chunks（新增={_Added}，更新={_Updated}）"
        )

    @mcp.tool()
    @suppress_stdout
    def add_todo( file_path: str, todo_text: str, section: str = "" ) -> str:
        """
        在指定 .md 檔案中新增一個 todo 項目 (- [ ] text)。
        file_path: 相對於 Vault 根目錄的路徑（通常是某個 status.md）。
        todo_text: 要新增的 todo 文字（不需包含 '- [ ]' 前綴）。
        section: 目標段落標題（例如 '## 待辦'），若指定則在該段落末尾新增；
                 留空則在檔案末尾新增。
        """
        from services.vault import VaultService
        _Stats, _Error = VaultService.add_todo( file_path, todo_text, section or None )
        if _Error:
            return _Error
        _Added = _Stats["index_stats"].get( "num_added", 0 )
        _Updated = _Stats["index_stats"].get( "num_updated", 0 )
        return (
            f"Todo 已新增：- [ ] {todo_text}\n"
            f"已索引：{_Stats['total_chunks']} chunks（新增={_Added}，更新={_Updated}）"
        )

    @mcp.tool()
    @suppress_stdout
    def remove_todo( file_path: str, todo_text: str ) -> str:
        """
        從指定 .md 檔案中移除一個 todo 項目（整行刪除）。
        file_path: 相對於 Vault 根目錄的路徑。
        todo_text: todo 項目的部分文字（用來比對對應行）。
        """
        from services.vault import VaultService
        _Stats, _Error = VaultService.remove_todo( file_path, todo_text )
        if _Error:
            return _Error
        _Added = _Stats["index_stats"].get( "num_added", 0 )
        _Updated = _Stats["index_stats"].get( "num_updated", 0 )
        return (
            f"Todo removed: {_Stats['removed_line']}\n"
            f"Indexed: {_Stats['total_chunks']} chunks (added={_Added}, updated={_Updated})."
        )
