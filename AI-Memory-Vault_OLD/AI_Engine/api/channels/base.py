"""
Messaging Channel 抽象基底
所有通訊平台（LINE / Telegram / Slack / Teams）共用介面。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 2.2
@date 2026.03.29
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IncomingMessage:
    """
    平台無關的統一訊息格式。
    各 Channel 將平台原生格式轉為此結構，交給 ChatService 處理。
    """

    ## <summary>使用者文字訊息</summary>
    m_Text: str

    ## <summary>使用者在該平台的唯一識別碼</summary>
    m_UserId: str

    ## <summary>平台名稱（line / telegram / slack / teams）</summary>
    m_Platform: str

    ## <summary>回覆用 Token 或 Channel ID（平台特定，用於回傳訊息）</summary>
    m_ReplyToken: Optional[str] = None

    ## <summary>平台原始 Context（各 Channel 自行傳遞額外資訊）</summary>
    m_Extra: dict = field( default_factory=dict )


@dataclass
class OutgoingMessage:
    """
    平台無關的統一回覆格式。
    ChatService 產出此結構，各 Channel 轉為平台原生回覆。
    """

    ## <summary>回覆文字</summary>
    m_Text: str

    ## <summary>是否為錯誤訊息</summary>
    m_IsError: bool = False


class BaseChannel( ABC ):
    """
    通訊平台 Channel 抽象基底。
    每個平台（LINE / Telegram / Slack / Teams）實作此介面。
    """

    @property
    @abstractmethod
    def platform_name( self ) -> str:
        """平台名稱識別字串（如 'line', 'telegram'）。"""
        ...

    @abstractmethod
    async def verify_request( self, iBody: bytes, iHeaders: dict ) -> bool:
        """
        驗證 Webhook 請求的合法性（簽章驗證）。

        Args:
            iBody: 原始 HTTP Body（bytes）。
            iHeaders: HTTP Headers dict。

        Returns:
            驗證通過回傳 True，否則 False。
        """
        ...

    @abstractmethod
    async def parse_messages( self, iBody: bytes, iHeaders: dict ) -> list[IncomingMessage]:
        """
        解析 Webhook 請求為平台無關的 IncomingMessage 列表。
        一次 Webhook 可能包含多則訊息（如 LINE 的 events 陣列）。

        Args:
            iBody: 原始 HTTP Body（bytes）。
            iHeaders: HTTP Headers dict。

        Returns:
            IncomingMessage 列表（僅文字訊息，非文字型忽略）。
        """
        ...

    @abstractmethod
    async def send_reply( self, iIncoming: IncomingMessage, iOutgoing: OutgoingMessage ) -> None:
        """
        將回覆送回該平台。

        Args:
            iIncoming: 原始收到的訊息（含 reply token 等平台資訊）。
            iOutgoing: ChatService 產出的回覆。
        """
        ...
