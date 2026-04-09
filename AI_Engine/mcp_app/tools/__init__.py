"""
MCP 工具模組集合

每個子模組對外提供 register(mcp, ...) 函式，
由 server.py 在建立 FastMCP 後統一呼叫。
"""
from mcp_app.tools import (
    vault_tools,
    scheduler_tools,
    project_tools,
    todo_tools,
    index_tools,
    agent_tools,
    instinct_tools,
)

__all__ = [
    "vault_tools",
    "scheduler_tools",
    "project_tools",
    "todo_tools",
    "index_tools",
    "agent_tools",
    "instinct_tools",
]
