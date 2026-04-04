"""
Discord Messaging API Channel
處理 Discord Bot 連線、訊息解析、回覆訊息。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 2.2
@date 2026.03.31
"""
import logging
import discord
import asyncio
from .base import BaseChannel, IncomingMessage, OutgoingMessage

logger = logging.getLogger(__name__)

PLATFORM_NAME = "discord"

class DiscordBotChannel(BaseChannel):
    """
    Discord Bot Channel 處理器。
    """
    def __init__(self, iBotToken: str, iChannelId: int):
        """
        Args:
            iBotToken: Discord Bot Token。
            iChannelId: Discord 頻道 ID（僅回覆該頻道訊息）。
        """
        self.m_BotToken = iBotToken
        self.m_ChannelId = iChannelId
        self.m_Client = discord.Client(intents=discord.Intents.default())
        self.m_MessageQueue = asyncio.Queue()
        self._register_events()

    @property
    def platform_name(self) -> str:
        return PLATFORM_NAME

    def _register_events(self):
        @self.m_Client.event
        async def on_ready():
            logger.info(f"Discord Bot 已上線：{self.m_Client.user}")

        @self.m_Client.event
        async def on_message(message):
            if message.author.bot:
                return
            if message.channel.id != self.m_ChannelId:
                return
            _Incoming = IncomingMessage(
                m_Text=message.content,
                m_UserId=str(message.author.id),
                m_Platform=PLATFORM_NAME,
                m_ReplyToken=str(message.id),
                m_Extra={"channel_id": message.channel.id}
            )
            await self.m_MessageQueue.put(_Incoming)

    async def verify_request(self, iBody: bytes, iHeaders: dict) -> bool:
        """
        Discord Bot 不需 Webhook 驗證，直接回傳 True。
        """
        return True

    async def parse_messages(self, iBody: bytes, iHeaders: dict) -> list[IncomingMessage]:
        """
        Discord Bot 由 on_message 事件觸發，這裡回傳 queue 中的訊息。
        """
        _Messages = []
        while not self.m_MessageQueue.empty():
            _Messages.append(await self.m_MessageQueue.get())
        return _Messages

    async def send_reply(self, iIncoming: IncomingMessage, iOutgoing: OutgoingMessage) -> None:
        """
        回覆 Discord 頻道訊息。
        """
        channel = self.m_Client.get_channel(self.m_ChannelId)
        if channel:
            await channel.send(iOutgoing.m_Text)
        else:
            logger.error(f"找不到 Discord 頻道：{self.m_ChannelId}")

    def run(self):
        """
        啟動 Discord Bot（需在主程式呼叫）。
        """
        self.m_Client.run(self.m_BotToken)
