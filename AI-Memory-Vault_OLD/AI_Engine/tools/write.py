"""write_note 工具 — 寫入或更新筆記檔案（LangChain @tool 薄封裝）。"""
from langchain_core.tools import tool
from services.vault_service import VaultService


@tool
def write_note( file_path: str, content: str, mode: str = "overwrite" ) -> str:
    """寫入或更新 Vault 中的筆記檔案。

    Args:
        file_path: 相對於 Vault 根目錄的檔案路徑（例如：_system/handoff.md）。
        content:   要寫入的內容。overwrite 模式為完整新內容；append 模式為追加內容。
        mode:      寫入模式。'overwrite' = 覆寫整個檔案（預設）；'append' = 在末尾追加。
    """
    _Label = "追加至" if mode == "append" else "覆寫"
    print( f"\n[系統執行中] ✍️  正在{_Label}：{file_path}" )

    _Stats, _Error = VaultService.write_note( file_path, content, mode )
    if _Error:
        return f"❌ {_Error}"

    _Added = _Stats["index_stats"].get( "num_added", 0 )
    _Updated = _Stats["index_stats"].get( "num_updated", 0 )
    return (
        f"✅ 已成功{_Label}：{file_path}（共 {_Stats['chars']} 字元）"
        f" | 索引：{_Stats['total_chunks']} chunks (added={_Added}, updated={_Updated})"
    )
