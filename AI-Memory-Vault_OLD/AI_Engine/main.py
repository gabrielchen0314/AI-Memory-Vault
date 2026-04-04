"""
AI 第二大腦 — 入口程式
支援 CLI 互動模式與 FastAPI 伺服器模式。

用法：
    python main.py              → 啟動 CLI 互動模式（預設）
    python main.py --mode api   → 啟動 FastAPI 伺服器

@author gabrielchen
@version 2.0
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
import argparse
import sys
import os

# 確保 _AI_Engine 目錄在 sys.path 中（不依賴 cwd）
_ENGINE_DIR = os.path.dirname( os.path.abspath( __file__ ) )
if _ENGINE_DIR not in sys.path:
    sys.path.insert( 0, _ENGINE_DIR )
os.chdir( _ENGINE_DIR )


def main():
    from env_setup import check_and_setup_env
    check_and_setup_env()

    _Parser = argparse.ArgumentParser( description="AI 第二大腦 — 記憶庫引擎 v2.0" )
    _Parser.add_argument(
        "--mode",
        choices=["cli", "api", "mcp"],
        default="cli",
        help="啟動模式：cli（互動終端）/ api（FastAPI 伺服器）/ mcp（MCP stdio 伺服器）",
    )
    _Args = _Parser.parse_args()

    if _Args.mode == "api":
        _start_api()
    elif _Args.mode == "mcp":
        _start_mcp()
    else:
        _start_cli()


def _start_cli():
    """啟動 CLI 互動模式。"""
    from env_setup import check_mode_prerequisites
    check_mode_prerequisites( "cli" )

    from core.llm_factory import create_llm
    from agents.memory_agent import MemoryAgent
    from cli.repl import InteractiveRepl

    _Llm = create_llm()
    _Agent = MemoryAgent( _Llm )
    _Repl = InteractiveRepl( _Agent )
    _Repl.run()


def _start_api():
    """啟動 FastAPI 伺服器。"""
    import uvicorn
    from config import settings
    from api.app import app
    from env_setup import check_mode_prerequisites

    check_mode_prerequisites( "api", settings.API_PORT )

    print( f"[START] FastAPI server: http://{settings.API_HOST}:{settings.API_PORT}" )
    print( f"        API Docs:        http://{settings.API_HOST}:{settings.API_PORT}/docs\n" )
    uvicorn.run( app, host=settings.API_HOST, port=settings.API_PORT )


def _start_mcp():
    """啟動 MCP stdio 伺服器（供 VS Code / Claude Desktop 呼叫）。"""
    from env_setup import check_mode_prerequisites
    check_mode_prerequisites( "mcp" )

    from mcp_server import run_mcp_server
    run_mcp_server()


if __name__ == "__main__":
    main()
