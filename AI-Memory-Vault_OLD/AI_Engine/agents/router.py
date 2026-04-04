"""
Agent 路由器
根據使用者輸入判斷應使用哪個 Agent。
目前為關鍵字路由，未來可擴展為 LLM 意圖分類。

@author gabrielchen
@version 2.0
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
from .base import BaseAgent


class AgentRouter:
    """Agent 路由器：依使用者輸入的 @mention 或關鍵字選擇對應 Agent。"""

    def __init__( self ):
        self.m_Agents: dict = {}
        self.m_DefaultAgentName: str = ""

    def register( self, iName: str, iAgent: BaseAgent, iIsDefault: bool = False ):
        """註冊一個 Agent。

        Args:
            iName:      Agent 名稱（用於 @mention 匹配）。
            iAgent:     Agent 實例。
            iIsDefault: 是否為預設 Agent（無匹配時使用）。
        """
        self.m_Agents[iName.lower()] = iAgent
        if iIsDefault:
            self.m_DefaultAgentName = iName.lower()

    def route( self, iUserInput: str ) -> BaseAgent:
        """依使用者輸入選擇 Agent。

        匹配邏輯：
        1. 檢查輸入中是否包含 @AgentName
        2. 無匹配 → 回傳預設 Agent

        Args:
            iUserInput: 使用者的原始輸入文字。

        Returns:
            匹配到的 Agent 實例。
        """
        _Input = iUserInput.strip().lower()

        # 優先匹配 @mention
        for _Name, _Agent in self.m_Agents.items():
            if f"@{_Name}" in _Input:
                return _Agent

        # 無匹配 → 預設 Agent
        if self.m_DefaultAgentName and self.m_DefaultAgentName in self.m_Agents:
            return self.m_Agents[self.m_DefaultAgentName]

        # 保底：回傳第一個註冊的 Agent
        return next( iter( self.m_Agents.values() ) )
