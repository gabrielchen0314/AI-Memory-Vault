"""
統一日誌模組
為所有模組提供一致的日誌取得介面。
取代分散的 print() 呼叫，支援 stderr handler + file handler。

使用方式：
    from core.logger import get_logger
    _logger = get_logger( __name__ )
    _logger.info( "..." )

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.08
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

## <summary>是否已完成全域 handler 設定</summary>
_g_Configured: bool = False


def configure( iLevel: int = logging.INFO, iLogFile: str = "" ) -> None:
    """
    設定全域 logging handler（僅首次呼叫生效）。

    Args:
        iLevel:   日誌級別。
        iLogFile: 若非空則額外寫入 file handler。
    """
    global _g_Configured
    if _g_Configured:
        return
    _g_Configured = True

    _Root = logging.getLogger( "vault" )
    _Root.setLevel( iLevel )

    # ── stderr handler（MCP 安全：不汙染 stdout） ─────────
    _StderrHandler = logging.StreamHandler( sys.stderr )
    _StderrHandler.setLevel( iLevel )
    _StderrHandler.setFormatter( logging.Formatter(
        "[%(name)s] %(levelname)s: %(message)s"
    ) )
    _Root.addHandler( _StderrHandler )

    # ── file handler（選填）────────────────────────────────
    if iLogFile:
        _FileHandler = logging.FileHandler( iLogFile, encoding="utf-8" )
        _FileHandler.setLevel( iLevel )
        _FileHandler.setFormatter( logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ) )
        _Root.addHandler( _FileHandler )


def get_logger( iName: str ) -> logging.Logger:
    """
    取得子 logger（自動掛在 vault.* 命名空間下）。

    Args:
        iName: 模組名稱（通常傳 __name__）。

    Returns:
        logging.Logger 實例。
    """
    # 將 "services.vault" → "vault.services.vault"
    _Short = iName.replace( "AI_Engine.", "" )
    return logging.getLogger( f"vault.{_Short}" )
