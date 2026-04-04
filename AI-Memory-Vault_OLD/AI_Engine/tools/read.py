"""read_note 工具 — 讀取指定筆記的完整內容（LangChain @tool 薄封裝）。"""
from langchain_core.tools import tool
from services.vault_service import VaultService


@tool
def read_note( file_path: str ) -> str:
    """讀取 Vault 中指定筆記檔案的完整原始內容。

    Args:
        file_path: 相對於 Vault 根目錄的檔案路徑（例如：_system/handoff.md）。
    """
    print( f"\n[系統執行中] 📖 正在讀取：{file_path}" )

    _Content, _Error = VaultService.read_note( file_path )
    if _Error:
        return f"❌ {_Error}"

    return f"【{file_path}】\n\n{_Content}"
