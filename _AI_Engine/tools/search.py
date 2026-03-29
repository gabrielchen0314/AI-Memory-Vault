"""search_notes 工具 — Hybrid 語意搜尋 Vault 記憶庫（LangChain @tool 薄封裝）。"""
from langchain_core.tools import tool
from services.vault_service import VaultService


@tool
def search_notes( query: str, category: str = "", doc_type: str = "" ) -> str:
    """當使用者詢問記憶庫內容時呼叫。使用 BM25 關鍵字 + 向量語意混合搜尋。

    Args:
        query:    搜尋問題或關鍵字。
        category: 可選，限定分類範圍：work / life / knowledge。留空則搜尋全部。
        doc_type: 可選，限定文件類型：rule / project / meeting 等。留空則不限。
    """
    return VaultService.search_formatted( query, category, doc_type )
