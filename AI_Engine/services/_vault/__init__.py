"""
services/_vault/ — VaultService 內部實作模組

由 vault.py Facade 委派呼叫，外部不直接 import。
拆分目的：將 982 行的 God Object 拆為 3 個職責明確的子模組。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.6
@date 2026.04.10
"""
from services._vault.note_ops import (
    read_note, write_note, batch_write_notes,
    edit_note, delete_note, rename_note, list_notes,
    update_todo, add_todo, remove_todo,
)
from services._vault.search_ops import (
    search, search_formatted, grep,
)
from services._vault.index_ops import (
    sync, check_integrity, clean_orphans, get_project_status,
)
