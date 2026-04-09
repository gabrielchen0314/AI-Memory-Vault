"""
統一錯誤模型
定義 VaultError 例外階層，
確保 MCP / CLI / API / Scheduler 四個界面使用一致的錯誤處理。

@author gabrielchen
@version 1.1
@since AI-Memory-Vault 3.5
@date 2026.04.10
"""
from __future__ import annotations


# ── 例外階層 ──────────────────────────────────────────────

class VaultError( Exception ):
    """Vault 操作基礎例外。"""

    def __init__( self, message: str, code: str = "VAULT_ERROR" ):
        super().__init__( message )
        self.code = code


class PathTraversalError( VaultError ):
    """路徑遍歷攻擊。"""

    def __init__( self, message: str = "path traversal not allowed." ):
        super().__init__( message, "PATH_TRAVERSAL" )


class FileNotFoundError_( VaultError ):
    """檔案不存在。"""

    def __init__( self, file_path: str ):
        super().__init__( f"file not found — {file_path}", "NOT_FOUND" )


class ExtensionError( VaultError ):
    """不允許的副檔名。"""

    def __init__( self, message: str = "only .md files are allowed." ):
        super().__init__( message, "EXTENSION" )


class NotInitializedError( VaultError ):
    """服務尚未初始化。"""

    def __init__( self, service: str = "VaultService" ):
        super().__init__( f"{service} not initialized. Call initialize() first.", "NOT_INITIALIZED" )


class TodoNotFoundError( VaultError ):
    """找不到 Todo 項目。"""

    def __init__( self, todo_text: str ):
        super().__init__( f"找不到包含 '{todo_text}' 的 todo 行。", "TODO_NOT_FOUND" )


class NoteAlreadyExistsError( VaultError ):
    """目標路徑已有檔案。"""

    def __init__( self, file_path: str ):
        super().__init__( f"target already exists — {file_path}", "ALREADY_EXISTS" )


class EditMatchError( VaultError ):
    """edit_note 文字比對失敗。"""

    def __init__( self, old_text: str, match_count: int ):
        if match_count == 0:
            super().__init__( f"old_text not found in file.", "EDIT_NO_MATCH" )
        else:
            super().__init__( f"old_text found {match_count} times; expected exactly 1.", "EDIT_MULTI_MATCH" )


