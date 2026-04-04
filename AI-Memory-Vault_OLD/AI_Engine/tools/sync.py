"""sync_notes 工具 — 增量同步 Vault 至向量庫（LangChain @tool 薄封裝）。"""
from langchain_core.tools import tool
from services.vault_service import VaultService


@tool
def sync_notes() -> str:
    """當使用者要求更新、同步筆記時呼叫。只會處理有變動的檔案。"""
    _Stats = VaultService.sync()
    return (
        f"同步完成！共 {_Stats['total_files']} 個檔案、{_Stats['total_chunks']} 個片段\n"
        f"分類統計：{_Stats['category_summary']}\n"
        f"類型統計：{_Stats['type_summary']}\n"
        f"索引結果：{_Stats['index_stats']}"
    )
