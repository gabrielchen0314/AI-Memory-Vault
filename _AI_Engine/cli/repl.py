"""
CLI 互動介面
提供終端機互動式對話，支援串流輸出與工具呼叫。

@author gabrielchen
@version 2.0
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from agents.base import BaseAgent
from tools import ALL_TOOLS
from config import settings
from datetime import datetime


TOOL_MAP = {t.name: t for t in ALL_TOOLS}


class InteractiveRepl:
    """互動式 REPL：支援串流輸出、工具呼叫、對話上下文。"""

    def __init__( self, iAgent: BaseAgent ):
        self.m_Agent: BaseAgent = iAgent
        self.m_ChatHistory: list = []

    def run( self ):
        """啟動互動式對話迴圈。"""
        print( "\n✅ AI 記憶庫 v2.0 啟動！" )
        print( "   輸入 'q' 離開 | 'clear' 清除對話 | 'sync' 強制同步 | 'save' 存擋本次對話\n" )

        self._auto_sync()
        self._repl_loop()

        print( "\n👋 已離開 AI 記憶庫。\n" )

    def _auto_sync( self ):
        """啟動時自動同步一次。"""
        try:
            from tools.sync import sync_notes
            _Result = sync_notes.invoke( {} )
            print( f"✅ 自動同步完成：{_Result}\n" )
        except Exception as _Ex:
            print( f"⚠️  自動同步失敗（不影響對話）：{_Ex}\n" )

    def _repl_loop( self ):
        """主要對話迴圈。"""
        try:
            while True:
                _Input = input( "👤 > " ).strip()

                if _Input.lower() == "q":
                    self._auto_save_session()
                    break
                if _Input.lower() == "clear":
                    self.m_ChatHistory.clear()
                    print( "🗑️  對話紀錄已清除。\n" )
                    continue
                if _Input.lower() == "sync":
                    self._force_sync()
                    continue
                if _Input.lower() == "save":
                    self._auto_save_session( iSilent=False )
                    continue
                if not _Input:
                    continue

                self._process_turn( _Input )

        except KeyboardInterrupt:
            self._auto_save_session()
            pass

    def _process_turn( self, iInput: str ):
        """處理一輪對話（使用者輸入 → 工具呼叫 → LLM 回覆）。"""
        self.m_ChatHistory.append( HumanMessage( content=iInput ) )
        _Messages = self._get_trimmed_messages()

        # 第一輪：偵測是否需要呼叫工具（用 invoke 取完整回應）
        print( "💭 思考中...", end="\r", flush=True )
        _Response, _Ok = self._invoke_llm( _Messages )
        if not _Ok:
            print( "              ", end="\r" )
            self.m_ChatHistory.pop()
            return

        self.m_ChatHistory.append( _Response )

        if _Response.tool_calls:
            # 執行所有工具呼叫
            for _Call in _Response.tool_calls:
                try:
                    _Fn = TOOL_MAP.get( _Call["name"] )
                    _Result = _Fn.invoke( _Call["args"] ) if _Fn else f"未知工具：{_Call['name']}"
                except Exception as _Ex:
                    _Result = f"⚠️  工具執行失敗：{_Ex}"
                self.m_ChatHistory.append(
                    ToolMessage( content=str( _Result ), tool_call_id=_Call["id"] )
                )

            # 第二輪：串流輸出最終回答
            _Final, _Ok = self._stream_response( self._get_trimmed_messages() )
            if _Ok:
                self.m_ChatHistory.append( _Final )
        else:
            # 無工具呼叫：移除 invoke 結果，改用串流重新輸出
            self.m_ChatHistory.pop()
            print( "              ", end="\r" )
            _Final, _Ok = self._stream_response( self._get_trimmed_messages() )
            if _Ok:
                self.m_ChatHistory.append( _Final )
            else:
                self.m_ChatHistory.pop()

    def _get_trimmed_messages( self ) -> list:
        """取 SystemMessage + 最近 N 輪對話。"""
        _Limit = settings.MAX_HISTORY_TURNS * 3
        _Recent = (
            self.m_ChatHistory[-_Limit:]
            if len( self.m_ChatHistory ) > _Limit
            else self.m_ChatHistory
        )
        return [self.m_Agent.system_message] + _Recent

    def _invoke_llm( self, iMessages: list ):
        """呼叫 LLM（非串流），回傳 (response, is_ok)。"""
        try:
            return self.m_Agent.llm_with_tools.invoke( iMessages ), True
        except KeyboardInterrupt:
            raise
        except Exception as _Ex:
            self._handle_error( _Ex )
            return None, False

    def _stream_response( self, iMessages: list ):
        """串流印出 LLM 回應（逐字輸出），回傳 (AIMessage, is_ok)。"""
        try:
            print( "\n🤖 ", end="", flush=True )
            _Accumulated = None
            _HasContent = False
            for _Chunk in self.m_Agent.llm_with_tools.stream( iMessages ):
                if _Chunk.content:
                    print( _Chunk.content, end="", flush=True )
                    _HasContent = True
                _Accumulated = _Chunk if _Accumulated is None else _Accumulated + _Chunk
            print( "\n" )
            if not _HasContent:
                print( "🤖 （AI 已完成執行，但未產生文字回應）\n" )
            return _Accumulated, True
        except KeyboardInterrupt:
            raise
        except Exception as _Ex:
            self._handle_error( _Ex )
            return None, False

    def _force_sync( self ):
        """手動觸發同步。"""
        try:
            from tools.sync import sync_notes
            _Result = sync_notes.invoke( {} )
            print( f"\n✅ {_Result}\n" )
        except Exception as _Ex:
            print( f"\n⚠️  同步失敗：{_Ex}\n" )

    def _auto_save_session( self, iSilent: bool = True ):
        """Session 結束 / 主動存擋：將本次對話的使用者與 AI 訊息寫入 .ai_memory/logs/。"""
        _HumanTurns = [
            m for m in self.m_ChatHistory
            if isinstance( m, HumanMessage )
        ]
        if not _HumanTurns:
            return

        _Date = datetime.now().strftime( "%Y-%m-%d" )
        _Time = datetime.now().strftime( "%H%M%S" )
        _FilePath = f".ai_memory/logs/chat-history-{_Date}_{_Time}.md"

        _Lines = [
            f"---",
            f"type: session-log",
            f"date: {_Date}",
            f"turns: {len( _HumanTurns )}",
            f"ai_summary: \"{_Date} 對話紀錄，共 {len( _HumanTurns )} 輪\"",
            f"---",
            f"",
            f"# Session 紀錄 {_Date}\n",
        ]

        for _Msg in self.m_ChatHistory:
            if isinstance( _Msg, HumanMessage ):
                _Lines.append( f"**👤 你**：{_Msg.content}\n" )
            elif isinstance( _Msg, AIMessage ) and _Msg.content:
                _Lines.append( f"**🤖 AI**：{_Msg.content}\n" )

        try:
            from tools.write import write_note
            _Result = write_note.invoke( {
                "file_path": _FilePath,
                "content": "\n".join( _Lines ),
                "mode": "overwrite",
            } )
            if not iSilent:
                print( f"\n💾 {_Result}\n" )
            else:
                print( f"\n💾 已自動存擋對話紀錄：{_FilePath}\n" )
        except Exception as _Ex:
            if not iSilent:
                print( f"\n⚠️  存擋失敗：{_Ex}\n" )

    @staticmethod
    def _handle_error( iEx: Exception ):
        """統一處理 LLM 錯誤訊息。"""
        _Msg = str( iEx )
        if "429" in _Msg or "ResourceExhausted" in _Msg or "quota" in _Msg.lower():
            print( "\n🚫 Gemini API 免費額度已用盡！" )
            print( "   解法一：切換至 Ollama → 在 .env 設定 LLM_PROVIDER=ollama" )
            print( "   解法二：等待今日配額重置（太平洋時間午夜）" )
            print( "   解法三：前往 https://aistudio.google.com/ 開啟付費方案\n" )
        elif "connection" in _Msg.lower() or "refused" in _Msg.lower():
            print( f"\n🚫 無法連線至 LLM 服務！請確認服務正在運行。\n" )
        else:
            print( f"\n⚠️  API 呼叫失敗：{iEx}\n" )
