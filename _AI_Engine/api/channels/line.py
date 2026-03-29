"""
LINE Messaging API Channel
處理 LINE Webhook 驗簽、訊息解析、Reply API 回覆。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 2.2
@date 2026.03.29
"""
import hashlib
import hmac
import base64
import json
import logging

import httpx

from .base import BaseChannel, IncomingMessage, OutgoingMessage


logger = logging.getLogger( __name__ )

#region 常數定義
LINE_REPLY_URL: str = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH_URL: str = "https://api.line.me/v2/bot/message/push"
PLATFORM_NAME: str = "line"
ACK_TEXT: str = "收到您的訊息，正在處理中，請稍候..."
#endregion


class LineChannel( BaseChannel ):
    """LINE Messaging API Webhook 處理器。"""

    def __init__( self, iChannelSecret: str, iChannelAccessToken: str ):
        """
        Args:
            iChannelSecret: LINE Channel Secret（用於驗簽）。
            iChannelAccessToken: LINE Channel Access Token（用於回覆）。
        """
        ## <summary>LINE Channel Secret</summary>
        self.m_ChannelSecret: str = iChannelSecret

        ## <summary>LINE Channel Access Token</summary>
        self.m_ChannelAccessToken: str = iChannelAccessToken

    @property
    def platform_name( self ) -> str:
        return PLATFORM_NAME

    async def verify_request( self, iBody: bytes, iHeaders: dict ) -> bool:
        """
        驗證 LINE Webhook 簽章（X-Line-Signature）。

        Args:
            iBody: 原始 HTTP Body。
            iHeaders: HTTP Headers。

        Returns:
            簽章正確回傳 True。
        """
        _Signature = iHeaders.get( "x-line-signature", "" )
        if not _Signature:
            return False

        _Hash = hmac.new(
            self.m_ChannelSecret.encode( "utf-8" ),
            iBody,
            hashlib.sha256,
        ).digest()
        _Expected = base64.b64encode( _Hash ).decode( "utf-8" )

        return hmac.compare_digest( _Signature, _Expected )

    async def parse_messages( self, iBody: bytes, iHeaders: dict ) -> list[IncomingMessage]:
        """
        解析 LINE Webhook events，僅保留文字訊息。

        Args:
            iBody: 原始 HTTP Body。
            iHeaders: HTTP Headers。

        Returns:
            IncomingMessage 列表。
        """
        try:
            _Payload = json.loads( iBody )
        except ( json.JSONDecodeError, UnicodeDecodeError ):
            logger.warning( "LINE Webhook: invalid JSON body" )
            return []

        _Messages: list[IncomingMessage] = []

        for _Event in _Payload.get( "events", [] ):
            if _Event.get( "type" ) != "message":
                continue
            if _Event.get( "message", {} ).get( "type" ) != "text":
                continue

            _Text = _Event["message"]["text"].strip()
            if not _Text:
                continue

            _UserId = _Event.get( "source", {} ).get( "userId", "unknown" )
            _ReplyToken = _Event.get( "replyToken", "" )

            _Messages.append( IncomingMessage(
                m_Text=_Text,
                m_UserId=_UserId,
                m_Platform=PLATFORM_NAME,
                m_ReplyToken=_ReplyToken,
            ) )

        return _Messages

    async def send_ack( self, iIncoming: IncomingMessage ) -> None:
        """
        立即回覆「收到，處理中」的確認訊息（消耗 replyToken）。

        Args:
            iIncoming: 原始訊息（含 replyToken）。
        """
        _ReplyToken = iIncoming.m_ReplyToken
        if not _ReplyToken:
            return

        _Body = {
            "replyToken": _ReplyToken,
            "messages": [{ "type": "text", "text": ACK_TEXT }],
        }
        async with httpx.AsyncClient() as _Client:
            await _Client.post(
                LINE_REPLY_URL,
                json=_Body,
                headers={
                    "Authorization": f"Bearer {self.m_ChannelAccessToken}",
                    "Content-Type": "application/json",
                },
                timeout=5.0,
            )

    async def send_push( self, iUserId: str, iOutgoing: OutgoingMessage ) -> None:
        """
        透過 LINE Push API 主動推送訊息給指定使用者。

        Args:
            iUserId: LINE userId。
            iOutgoing: ChatService 產出的回覆。
        """
        _Body = {
            "to": iUserId,
            "messages": self._split_messages( iOutgoing.m_Text ),
        }
        async with httpx.AsyncClient() as _Client:
            _Resp = await _Client.post(
                LINE_PUSH_URL,
                json=_Body,
                headers={
                    "Authorization": f"Bearer {self.m_ChannelAccessToken}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            if _Resp.status_code != 200:
                logger.error( f"LINE Push API error: {_Resp.status_code} {_Resp.text}" )

    async def send_reply( self, iIncoming: IncomingMessage, iOutgoing: OutgoingMessage ) -> None:
        """
        透過 LINE Reply API 回覆訊息。

        Args:
            iIncoming: 原始訊息（含 replyToken）。
            iOutgoing: ChatService 產出的回覆。
        """
        _ReplyToken = iIncoming.m_ReplyToken
        if not _ReplyToken:
            logger.warning( "LINE send_reply: missing replyToken, skip" )
            return

        _Body = {
            "replyToken": _ReplyToken,
            "messages": self._split_messages( iOutgoing.m_Text ),
        }

        async with httpx.AsyncClient() as _Client:
            _Resp = await _Client.post(
                LINE_REPLY_URL,
                json=_Body,
                headers={
                    "Authorization": f"Bearer {self.m_ChannelAccessToken}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            if _Resp.status_code != 200:
                logger.error( f"LINE Reply API error: {_Resp.status_code} {_Resp.text}" )

    @staticmethod
    def _split_messages( iText: str ) -> list[dict]:
        """
        LINE 單則訊息上限 5000 字元，超過時自動拆分。

        Args:
            iText: 回覆文字。

        Returns:
            LINE message 物件列表（最多 5 則）。
        """
        MAX_CHARS: int = 5000
        MAX_MESSAGES: int = 5
        _Chunks: list[dict] = []

        _Remaining = iText
        while _Remaining and len( _Chunks ) < MAX_MESSAGES:
            _Part = _Remaining[:MAX_CHARS]
            _Remaining = _Remaining[MAX_CHARS:]
            _Chunks.append( { "type": "text", "text": _Part } )

        return _Chunks if _Chunks else [{ "type": "text", "text": "（無回覆內容）" }]
