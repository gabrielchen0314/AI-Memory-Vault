"""
FastAPI 應用程式
提供 REST API 端點與 Messaging Gateway Webhook，
供 MCP / LINE Bot / Web UI 等外部工具呼叫。

@author gabrielchen
@version 2.2
@since AI-Memory-Vault 2.0
@date 2026.03.29
"""
import logging

from fastapi import FastAPI, HTTPException, Request, Response
from .schemas import (
    SyncResponse, SearchRequest, SearchResponse, SearchResult,
    ReadRequest, ReadResponse, WriteRequest, WriteResponse,
)
from services.vault_service import VaultService
from config import settings


logger = logging.getLogger( __name__ )

app = FastAPI(
    title="AI Memory Vault",
    description="AI 第二大腦 — 記憶庫 REST API + Messaging Gateway",
    version="2.2",
)


# ── Messaging Gateway：ChatService + Channel 懶載入 ────────

_chat_service = None
_line_channel = None
_discord_channel = None


def _get_chat_service():
    """延遲初始化 ChatService（避免 import 時載入 LLM）。"""
    global _chat_service
    if _chat_service is None:
        from .chat_service import ChatService
        _chat_service = ChatService()
    return _chat_service



def _get_line_channel():
    """延遲初始化 LINE Channel（僅在有設定時啟用）。"""
    global _line_channel
    if _line_channel is None:
        if not settings.LINE_CHANNEL_SECRET or not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return None
        from .channels.line import LineChannel
        _line_channel = LineChannel(
            iChannelSecret=settings.LINE_CHANNEL_SECRET,
            iChannelAccessToken=settings.LINE_CHANNEL_ACCESS_TOKEN,
        )
    return _line_channel

def _get_discord_channel():
    """延遲初始化 Discord Channel（僅在有設定時啟用）。"""
    global _discord_channel
    if _discord_channel is None:
        if not settings.DISCORD_BOT_TOKEN or not settings.DISCORD_CHANNEL_ID:
            return None
        from .channels.discord import DiscordBotChannel
        _discord_channel = DiscordBotChannel(
            iBotToken=settings.DISCORD_BOT_TOKEN,
            iChannelId=settings.DISCORD_CHANNEL_ID,
        )
    return _discord_channel



@app.get( "/health" )
async def health():
    """健康檢查。"""
    _LineEnabled = bool(
        settings.LINE_CHANNEL_SECRET and settings.LINE_CHANNEL_ACCESS_TOKEN
    )
    _DiscordEnabled = bool(
        settings.DISCORD_BOT_TOKEN and settings.DISCORD_CHANNEL_ID
    )
    return {
        "status": "ok",
        "version": "2.2",
        "channels": {
            "line": _LineEnabled,
            "discord": _DiscordEnabled,
        },
    }


@app.post( "/sync", response_model=SyncResponse )
async def sync():
    """觸發 Vault 增量同步。"""
    try:
        _Stats = VaultService.sync()
        return SyncResponse( success=True, message="同步完成", stats=_Stats )
    except Exception as _Ex:
        raise HTTPException( status_code=500, detail=str( _Ex ) )


@app.post( "/search", response_model=SearchResponse )
async def search( iReq: SearchRequest ):
    """語意搜尋 Vault 記憶庫。"""
    try:
        _RawResults = VaultService.search(
            iReq.query, iReq.category, iReq.doc_type, iReq.top_k
        )
        _Results = [SearchResult( **_R ) for _R in _RawResults]
        return SearchResponse( results=_Results, count=len( _Results ) )
    except Exception as _Ex:
        raise HTTPException( status_code=500, detail=str( _Ex ) )


@app.post( "/read", response_model=ReadResponse )
async def read( iReq: ReadRequest ):
    """讀取 Vault 中指定筆記的完整內容。"""
    _Content, _Error = VaultService.read_note( iReq.file_path )
    if _Error:
        raise HTTPException( status_code=400, detail=_Error )
    return ReadResponse( content=_Content, file_path=iReq.file_path )


@app.post( "/write", response_model=WriteResponse )
async def write( iReq: WriteRequest ):
    """寫入或更新 Vault 中的筆記檔案。"""
    _Stats, _Error = VaultService.write_note( iReq.file_path, iReq.content, iReq.mode )
    if _Error:
        raise HTTPException( status_code=400, detail=_Error )
    return WriteResponse(
        success=True,
        file_path=_Stats["file_path"],
        chars=_Stats["chars"],
        total_chunks=_Stats["total_chunks"],
    )



# ── Webhook: LINE ──────────────────────────────────────────
@app.post( "/webhook/line" )
async def webhook_line( iRequest: Request ):
    """LINE Messaging API Webhook 端點。"""
    _Channel = _get_line_channel()
    if _Channel is None:
        raise HTTPException( status_code=503, detail="LINE channel not configured" )

    _Body = await iRequest.body()
    _Headers = dict( iRequest.headers )

    # 驗簽
    if not await _Channel.verify_request( _Body, _Headers ):
        raise HTTPException( status_code=403, detail="Invalid signature" )

    # 解析訊息
    _Messages = await _Channel.parse_messages( _Body, _Headers )
    if not _Messages:
        return Response( status_code=200 )

    # 逐則處理並回覆
    _Service = _get_chat_service()
    for _Msg in _Messages:
        try:
            _Reply = await _Service.handle_message( _Msg )
            await _Channel.send_reply( _Msg, _Reply )
        except Exception as _Ex:
            logger.error( f"LINE webhook handle error: {_Ex}", exc_info=True )

    return Response( status_code=200 )

# ── Webhook: Discord（輪詢訊息） ──────────────────────────
@app.post( "/webhook/discord/poll" )
async def webhook_discord_poll():
    """Discord Bot 輪詢訊息（由排程/外部觸發）。"""
    _Channel = _get_discord_channel()
    if _Channel is None:
        raise HTTPException( status_code=503, detail="Discord channel not configured" )

    # Discord Bot 由 on_message 事件收集訊息，這裡主動拉取並處理
    _Messages = await _Channel.parse_messages( b"", {} )
    if not _Messages:
        return { "count": 0 }

    _Service = _get_chat_service()
    for _Msg in _Messages:
        try:
            _Reply = await _Service.handle_message( _Msg )
            await _Channel.send_reply( _Msg, _Reply )
        except Exception as _Ex:
            logger.error( f"Discord webhook handle error: {_Ex}", exc_info=True )

    return { "count": len(_Messages) }
