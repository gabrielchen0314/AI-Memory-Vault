"""
Agent 基底類別
定義所有 Agent 的共通介面，確保可插拔式擴展。

@author gabrielchen
@version 2.0
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage


class BaseAgent( ABC ):
    """Agent 抽象基底類別。所有具體 Agent 必須繼承此類別。"""

    def __init__( self, iLlm: BaseChatModel ):
        self.m_Llm: BaseChatModel = iLlm
        self.m_Tools: list = self._define_tools()
        self.m_LlmWithTools = iLlm.bind_tools( self.m_Tools ) if self.m_Tools else iLlm
        self.m_SystemMessage: SystemMessage = SystemMessage( content=self._define_system_prompt() )

    @abstractmethod
    def _define_system_prompt( self ) -> str:
        """定義此 Agent 的 System Prompt。"""
        ...

    @abstractmethod
    def _define_tools( self ) -> list:
        """定義此 Agent 可使用的工具列表。"""
        ...

    @property
    def name( self ) -> str:
        """Agent 名稱（預設為類別名）。"""
        return self.__class__.__name__

    @property
    def tools( self ) -> list:
        return self.m_Tools

    @property
    def system_message( self ) -> SystemMessage:
        return self.m_SystemMessage

    @property
    def llm_with_tools( self ):
        return self.m_LlmWithTools
