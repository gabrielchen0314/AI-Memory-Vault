"""
LLM 工廠模組
依 LLMConfig 設定建立對應的 LLM 實例。
支援 Ollama（本地）、Gemini（Google API）、Copilot（GitHub SDK）。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
import os
import sys
from langchain_core.language_models import BaseChatModel
from config import LLMConfig


def create_llm( iConfig: LLMConfig ) -> BaseChatModel:
    """
    依 LLMConfig 建立 LLM 實例。

    Args:
        iConfig: LLM 設定。

    Returns:
        LangChain BaseChatModel 實例。
    """
    _Provider = iConfig.provider.lower().strip()

    if _Provider == "ollama":
        from langchain_ollama import ChatOllama

        _Model = iConfig.model or "llama3.2"
        print( f"🔧 LLM 供應商：Ollama（本地）| 模型：{_Model}", file=sys.stderr )
        return ChatOllama(
            base_url=iConfig.ollama_base_url,
            model=_Model,
            repeat_penalty=1.3,
            num_predict=2048,
        )

    if _Provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        _ApiKey = os.environ.get( iConfig.api_key_env, "" ) if iConfig.api_key_env else ""
        if not _ApiKey:
            raise EnvironmentError( f"❌ 找不到環境變數 {iConfig.api_key_env}，請設定 API Key。" )

        _Model = iConfig.model or "gemini-2.0-flash-lite"
        print( f"🔧 LLM 供應商：Gemini | 模型：{_Model}", file=sys.stderr )
        return ChatGoogleGenerativeAI(
            model=_Model,
            google_api_key=_ApiKey,
            convert_system_message_to_human=True,
        )

    raise ValueError( f"❌ 不支援的 LLM provider：'{_Provider}'（請使用 ollama 或 gemini）" )
