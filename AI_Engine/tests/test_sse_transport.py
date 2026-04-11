"""
SSE Transport 整合測試

覆蓋：
  1. SSE app 建立 — FastMCP.sse_app() 回傳 Starlette 應用
  2. 路由驗證 — /sse (GET) 與 /messages (POST) 路由存在
  3. 端對端 — 啟動 uvicorn SSE Server → MCP Client 連線 → list_tools → call_tool
  4. run_mcp_sse_server 參數驗證 — host / port 預設值正確
  5. DNS rebinding 保護 — 預設啟用、測試模式可關閉

所有測試不依賴真實 Vault / ChromaDB，使用獨立 FastMCP 實例。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.7
@date 2026.04.10
"""
import asyncio
import socket
import threading
import time

import pytest
import pytest_asyncio
import uvicorn
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette


# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

def _free_port() -> int:
    """取得一個可用的隨機 port。"""
    with socket.socket( socket.AF_INET, socket.SOCK_STREAM ) as s:
        s.bind( ( "127.0.0.1", 0 ) )
        return s.getsockname()[1]


def _make_test_mcp() -> FastMCP:
    """建立測試用 FastMCP 實例（關閉 DNS rebinding 保護供測試用）。"""
    m = FastMCP(
        "test-sse",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        ),
    )

    @m.tool()
    def ping() -> str:
        """回傳 pong — 用於驗證 MCP 工具呼叫。"""
        return "pong"

    @m.tool()
    def echo( message: str ) -> str:
        """回傳輸入訊息 — 用於驗證參數傳遞。"""
        return f"echo: {message}"

    return m


# ────────────────────────────────────────────────────────────
# 1. SSE App 建立
# ────────────────────────────────────────────────────────────

class TestSseAppCreation:
    """驗證 FastMCP.sse_app() 回傳正確的 Starlette 應用。"""

    def test_sse_app_returns_starlette( self ):
        m = _make_test_mcp()
        app = m.sse_app()
        assert isinstance( app, Starlette )

    def test_sse_app_has_routes( self ):
        m = _make_test_mcp()
        app = m.sse_app()
        _route_paths = []
        for r in app.routes:
            _path = getattr( r, "path", None )
            if _path:
                _route_paths.append( _path )
        assert "/sse" in _route_paths
        assert "/messages" in _route_paths


# ────────────────────────────────────────────────────────────
# 2. run_mcp_sse_server 參數簽名
# ────────────────────────────────────────────────────────────

class TestRunMcpSseServer:
    """驗證 run_mcp_sse_server 函式簽名正確。"""

    def test_function_exists_and_callable( self ):
        from mcp_app.server import run_mcp_sse_server
        assert callable( run_mcp_sse_server )

    def test_default_parameters( self ):
        import inspect
        from mcp_app.server import run_mcp_sse_server

        sig = inspect.signature( run_mcp_sse_server )
        params = sig.parameters

        assert "iHost" in params
        assert "iPort" in params
        assert params["iHost"].default == "127.0.0.1"
        assert params["iPort"].default == 8765


# ────────────────────────────────────────────────────────────
# 3. DNS Rebinding Security
# ────────────────────────────────────────────────────────────

class TestDnsRebindingProtection:
    """驗證 DNS rebinding 保護設定。"""

    def test_default_protection_enabled( self ):
        """預設設定啟用 DNS rebinding 保護。"""
        settings = TransportSecuritySettings()
        assert settings.enable_dns_rebinding_protection is True

    def test_test_mode_protection_disabled( self ):
        """測試模式可關閉保護。"""
        settings = TransportSecuritySettings( enable_dns_rebinding_protection=False )
        assert settings.enable_dns_rebinding_protection is False


# ────────────────────────────────────────────────────────────
# 4. 端對端整合測試 — uvicorn + MCP Client
# ────────────────────────────────────────────────────────────

@pytest.fixture( scope="module" )
def sse_server():
    """
    啟動一個真實的 uvicorn SSE Server（後台執行緒），
    測試結束後自動關閉。
    """
    port = _free_port()
    mcp_instance = _make_test_mcp()
    app = mcp_instance.sse_app()

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="error",
    )
    server = uvicorn.Server( config )

    thread = threading.Thread( target=server.run, daemon=True )
    thread.start()

    # 等待 server 啟動
    for _ in range( 50 ):
        try:
            with socket.create_connection( ( "127.0.0.1", port ), timeout=0.2 ):
                break
        except OSError:
            time.sleep( 0.1 )
    else:
        pytest.fail( "SSE server failed to start within 5 seconds" )

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join( timeout=5 )


@pytest.mark.asyncio
async def test_sse_client_connect_and_list_tools( sse_server ):
    """MCP Client 透過 SSE 連線並取得工具清單。"""
    async with sse_client( sse_server + "/sse", timeout=5 ) as ( read, write ):
        async with ClientSession( read, write ) as session:
            await session.initialize()
            result = await session.list_tools()
            tool_names = [ t.name for t in result.tools ]
            assert "ping" in tool_names
            assert "echo" in tool_names


@pytest.mark.asyncio
async def test_sse_call_tool_ping( sse_server ):
    """透過 SSE 呼叫 ping 工具並驗證回傳值。"""
    async with sse_client( sse_server + "/sse", timeout=5 ) as ( read, write ):
        async with ClientSession( read, write ) as session:
            await session.initialize()
            result = await session.call_tool( "ping", {} )
            assert any( "pong" in c.text for c in result.content )


@pytest.mark.asyncio
async def test_sse_call_tool_echo_with_params( sse_server ):
    """透過 SSE 呼叫 echo 工具並驗證參數傳遞。"""
    async with sse_client( sse_server + "/sse", timeout=5 ) as ( read, write ):
        async with ClientSession( read, write ) as session:
            await session.initialize()
            result = await session.call_tool( "echo", { "message": "hello vault" } )
            assert any( "echo: hello vault" in c.text for c in result.content )


@pytest.mark.asyncio
async def test_sse_multiple_calls_same_session( sse_server ):
    """同一 SSE Session 內可連續呼叫多個工具。"""
    async with sse_client( sse_server + "/sse", timeout=5 ) as ( read, write ):
        async with ClientSession( read, write ) as session:
            await session.initialize()

            r1 = await session.call_tool( "ping", {} )
            r2 = await session.call_tool( "echo", { "message": "test1" } )
            r3 = await session.call_tool( "echo", { "message": "test2" } )

            assert any( "pong" in c.text for c in r1.content )
            assert any( "echo: test1" in c.text for c in r2.content )
            assert any( "echo: test2" in c.text for c in r3.content )
