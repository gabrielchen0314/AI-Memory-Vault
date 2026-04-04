"""
Chat Service — 平台無關的對話邏輯
接收 IncomingMessage，透過 MemoryAgent 回覆，回傳 OutgoingMessage。
由各 Channel Webhook 呼叫，不依賴任何特定平台 SDK。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 2.2
@date 2026.03.29
"""
import re
import logging
from langchain_core.messages import HumanMessage, ToolMessage

from agents.memory_agent import MemoryAgent
from core.llm_factory import create_llm
from tools import ALL_TOOLS
from config import settings
from api.channels.base import IncomingMessage, OutgoingMessage


logger = logging.getLogger( __name__ )


#region 常數定義
MAX_TOOL_ROUNDS: int = 10
ERROR_REPLY: str = "抱歉，處理訊息時發生錯誤，請稍後再試。"

## <summary>需要從回覆中過濾掉的工具相關關鍵字</summary>
_TOOL_LEAK_KEYWORDS: tuple = (
    "search_notes", "read_note", "write_note", "sync_notes",
    "工具call", "工具 call", "tool call", "query參數", "query 參數",
    "\"name\":", "\"parameters\":", "file_path\":",
)
#endregion


def _strip_markdown( iText: str ) -> str:
    """
    強制移除 Markdown 語法符號，確保 LINE 等純文字平台正確顯示。
    """
    _Result = iText
    # 移除粗體 / 斜體
    _Result = re.sub( r'\*{1,3}(.+?)\*{1,3}', r'\1', _Result )
    # 移除行內程式碼
    _Result = re.sub( r'`{1,3}[^`]*`{1,3}', '', _Result )
    # 移除標題符號
    _Result = re.sub( r'^#{1,6}\s+', '', _Result, flags=re.MULTILINE )
    # 移除分隔線
    _Result = re.sub( r'^-{3,}$', '', _Result, flags=re.MULTILINE )
    # 移除連結
    _Result = re.sub( r'\[([^\]]+)\]\([^)]+\)', r'\1', _Result )
    # 移除跳脫的 \* 符號
    _Result = re.sub( r'\\([*_`#])', r'\1', _Result )
    # 移除常見結構標籤（LLM 自言自語殘留）
    _LABEL_PATTERNS = [
        r'^使用者\s*Request[：:][^\n]*\n?',
        r'^工具執行後[：:][^\n]*\n?',
        r'^回覆[：:][\s]*',
        r'^查詢結果[：:][\s]*',
        r'^查找[^，。\n]*[，：:][\s]*',
        r'^正在搜尋[^\n]*\n?',
        r'^讓我[^\n]*\n?',
        r'^處理您的請求[^\n]*\n?',
    ]
    for _Pat in _LABEL_PATTERNS:
        _Result = re.sub( _Pat, '', _Result, flags=re.MULTILINE )
    # 壓縮連續空白行
    _Result = re.sub( r'\n{3,}', '\n\n', _Result )
    return _Result.strip()

## <summary>工具名稱 → 工具物件對照表</summary>
TOOL_MAP: dict = { _T.name: _T for _T in ALL_TOOLS }


class ChatService:
    """
    平台無關的對話服務。
    每個使用者以 (platform, user_id) 為鍵保留獨立的對話歷史。
    """

    def __init__( self ):
        ## <summary>LLM 實例</summary>
        _Llm = create_llm()

        ## <summary>MemoryAgent 實例</summary>
        self.m_Agent: MemoryAgent = MemoryAgent( _Llm )

        ## <summary>對話歷史，key = "{platform}:{user_id}"</summary>
        self.m_Histories: dict[str, list] = {}

    async def handle_message( self, iMessage: IncomingMessage ) -> OutgoingMessage:
        """
        處理一則使用者訊息，回傳 AI 回覆。

        Args:
            iMessage: 平台無關的統一訊息格式。

        Returns:
            OutgoingMessage — 回覆文字。
        """
        _SessionKey = f"{iMessage.m_Platform}:{iMessage.m_UserId}"
        _History = self.m_Histories.setdefault( _SessionKey, [] )

        _History.append( HumanMessage( content=iMessage.m_Text ) )
        _Messages = self._build_messages( _History )

        try:
            _ReplyText = await self._run_agent_turn( _Messages, _History )
            _ReplyText = _strip_markdown( _ReplyText )
            # 若回覆洩漏工具內部資訊，替換為通用錯誤訊息
            if any( _Kw in _ReplyText for _Kw in _TOOL_LEAK_KEYWORDS ):
                _ReplyText = ERROR_REPLY
            return OutgoingMessage( m_Text=_ReplyText )
        except Exception as _Ex:
            logger.error( "handle_message error: %s", _Ex, exc_info=True )
            return OutgoingMessage( m_Text=ERROR_REPLY, m_IsError=True )

    async def _run_agent_turn( self, iMessages: list, iHistory: list ) -> str:
        """
        執行一輪 Agent 對話（偵測工具呼叫 → 執行 → 最終回覆）。

        Args:
            iMessages: 完整訊息列表（含 SystemMessage）。
            iHistory: 該使用者的對話歷史引用（會被修改）。

        Returns:
            AI 回覆文字。
        """
        _Response = await self.m_Agent.llm_with_tools.ainvoke( iMessages )
        iHistory.append( _Response )

        _Round = 0
        while _Response.tool_calls and _Round < MAX_TOOL_ROUNDS:
            for _Call in _Response.tool_calls:
                _Fn = TOOL_MAP.get( _Call["name"] )
                try:
                    _Result = await _Fn.ainvoke( _Call["args"] ) if _Fn else f"未知工具：{_Call['name']}"
                except Exception as _Ex:
                    _Result = f"工具執行失敗：{_Ex}"
                iHistory.append(
                    ToolMessage( content=str( _Result ), tool_call_id=_Call["id"] )
                )

            # 工具輪次之間，清掉上一輪 AIMessage 的 content（自言自語），只保留 tool_calls
            if _Response.content and _Response.tool_calls:
                _Response.content = ""

            _Messages = self._build_messages( iHistory )
            _Response = await self.m_Agent.llm_with_tools.ainvoke( _Messages )
            iHistory.append( _Response )
            _Round += 1

        _FinalText = _Response.content if _Response.content else "（已完成操作，但未產生文字回覆）"

        # 強制清除英文 thinking 痕跡
        _FinalText = re.sub( r'(?i)^let\s*(?:al\s*)?me\s+(?:search|look|find|check)[^\n]*\n?', '', _FinalText )
        _FinalText = re.sub( r'(?i)^(?:I\s+found|here\s+are|searching)[^\n]*\n?', '', _FinalText )
        _FinalText = re.sub( r'(?i)\bundry\b', '', _FinalText )

        return _FinalText.strip() if _FinalText.strip() else "（已完成操作，但未產生文字回覆）"

    def _build_messages( self, iHistory: list ) -> list:
        """
        組裝完整訊息列表：SystemMessage + 最近 N 輪歷史。

        Args:
            iHistory: 該使用者的對話歷史。

        Returns:
            訊息列表。
        """
        _Limit = settings.MAX_HISTORY_TURNS * 3
        _Recent = iHistory[-_Limit:] if len( iHistory ) > _Limit else iHistory
        return [self.m_Agent.system_message] + _Recent
