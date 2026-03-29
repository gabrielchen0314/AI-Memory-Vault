"""
LLM 工廠模組
依 .env 中的 LLM_PROVIDER 設定，建立對應的 LLM 實例。
支援 Ollama（本地免費）與 Gemini（Google API）。

@author gabrielchen
@version 2.0
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
from langchain_core.language_models import BaseChatModel
from config import settings


def create_llm() -> BaseChatModel:
    """依 LLM_PROVIDER 環境變數建立 LLM 實例。"""
    _Provider = settings.LLM_PROVIDER.lower().strip()

    if _Provider == "ollama":
        from langchain_ollama import ChatOllama
        print( f"🔧 LLM 供應商：Ollama（本地）| 模型：{settings.OLLAMA_MODEL}" )
        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            repeat_penalty=1.3,
            num_predict=2048,
        )

    if _Provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not settings.GOOGLE_API_KEY:
            raise EnvironmentError( "❌ 找不到 GOOGLE_API_KEY，請在 .env 檔案中設定。" )
        print( f"🔧 LLM 供應商：Gemini | 模型：{settings.GEMINI_MODEL}" )
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            convert_system_message_to_human=True,
        )

    raise ValueError( f"❌ 不支援的 LLM_PROVIDER：'{_Provider}'（請使用 ollama 或 gemini）" )
