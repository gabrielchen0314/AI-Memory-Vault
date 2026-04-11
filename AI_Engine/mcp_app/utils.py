"""
MCP 工具共用工具函式
提供 stdout 重導向與 MCP tool 裝飾器。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.08
"""
from __future__ import annotations

import os
import sys
from functools import wraps

from core.logger import get_logger

_logger = get_logger( __name__ )


class StdoutToStderr:
    """
    Context manager: redirect stdout → stderr，保護 MCP stdio 通道純淨。
    同時重定向 Python 層（sys.stdout）與 OS 層（fd 1），
    攔截 C 擴展（torch / chromadb / sentence-transformers）直接寫入 fd 1 的輸出。
    """
    def __enter__( self ):
        self._old_sys_stdout = sys.stdout
        sys.stdout = sys.stderr
        self._saved_fd1 = os.dup( 1 )
        os.dup2( 2, 1 )

    def __exit__( self, *_ ):
        os.dup2( self._saved_fd1, 1 )
        os.close( self._saved_fd1 )
        sys.stdout = self._old_sys_stdout


def suppress_stdout( fn ):
    """
    MCP tool 裝飾器：自動用 StdoutToStderr 包裹，
    並在例外時回傳 "Error: ..." 字串而非崩潰。
    """
    @wraps( fn )
    def _wrapper( *args, **kwargs ):
        try:
            with StdoutToStderr():
                return fn( *args, **kwargs )
        except Exception as _E:
            _logger.exception( "MCP tool error in %s", fn.__name__ )
            return f"Error: {_E}"
    return _wrapper
