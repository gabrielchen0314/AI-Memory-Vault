"""FastAPI 請求/回應資料模型。"""
from typing import Optional
from pydantic import BaseModel


class SyncResponse( BaseModel ):
    """同步結果。"""
    success: bool
    message: str
    stats: dict


class SearchRequest( BaseModel ):
    """搜尋請求。"""
    query: str
    category: str = ""
    doc_type: str = ""
    top_k: int = 5


class SearchResult( BaseModel ):
    """單筆搜尋結果。"""
    content: str
    source: str
    category: str
    doc_type: str = ""
    domain: str = ""
    tags: str = ""
    ai_summary: str = ""


class SearchResponse( BaseModel ):
    """搜尋回應。"""
    results: list[SearchResult]
    count: int


class ReadRequest( BaseModel ):
    """讀取請求。"""
    file_path: str


class ReadResponse( BaseModel ):
    """讀取回應。"""
    content: str
    file_path: str


class WriteRequest( BaseModel ):
    """寫入請求。"""
    file_path: str
    content: str
    mode: str = "overwrite"


class WriteResponse( BaseModel ):
    """寫入回應。"""
    success: bool
    file_path: str
    chars: int
    total_chunks: int


class ChatRequest( BaseModel ):
    """對話請求（未來用於 LINE Bot / Web UI）。"""
    message: str
    session_id: Optional[str] = None


class ChatResponse( BaseModel ):
    """對話回應。"""
    reply: str
