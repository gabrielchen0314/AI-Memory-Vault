"""
統一 YAML Frontmatter 解析與渲染模組
消除 indexer / instinct / agent_router / server 各自實作的不一致問題。

解析統一使用 yaml.safe_load()（支援多行值、列表、轉義字元）。
渲染統一使用 yaml.dump()（確保輸出格式一致）。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.7
@date 2026.04.10
"""
import re
from typing import Any, Optional

import yaml

from core.logger import get_logger

_logger = get_logger( __name__ )

# ── Frontmatter 邊界正規表達式 ────────────────────────────
_FM_PATTERN = re.compile( r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL )


def parse( iContent: str ) -> tuple[dict, str]:
    """
    解析 YAML Frontmatter。

    Args:
        iContent: Markdown 原始內容（含 --- 標記）。

    Returns:
        (metadata_dict, body_content) — 無 frontmatter 則回傳 ({}, 原始內容)。
    """
    _Match = _FM_PATTERN.match( iContent )
    if not _Match:
        return {}, iContent

    try:
        _Meta = yaml.safe_load( _Match.group( 1 ) )
        if not isinstance( _Meta, dict ):
            return {}, iContent
        _Body = iContent[_Match.end():]
        return _Meta, _Body
    except yaml.YAMLError as _E:
        _logger.warning( "Frontmatter YAML 解析失敗：%s", _E )
        return {}, iContent


def render( iMeta: dict ) -> str:
    """
    渲染 YAML Frontmatter 字串。

    Args:
        iMeta: metadata 字典。

    Returns:
        包含 --- 標記的 frontmatter 字串。
    """
    _Lines = [ "---" ]
    for _K, _V in iMeta.items():
        if isinstance( _V, str ):
            # 含特殊字元時加引號
            if any( c in _V for c in ( ":", "#", "[", "]", "{", "}", ",", "&", "*", "?", "|", "-", "<", ">", "=", "!", "%", "@", "\\", "\n" ) ):
                _Lines.append( f'{_K}: "{_V}"' )
            else:
                _Lines.append( f"{_K}: {_V}" )
        elif isinstance( _V, list ):
            _Lines.append( f"{_K}: [{', '.join( str( x ) for x in _V )}]" )
        else:
            _Lines.append( f"{_K}: {_V}" )
    _Lines.append( "---" )
    return "\n".join( _Lines )


def has_field( iContent: str, iField: str, iValue: str = "" ) -> bool:
    """
    快速檢查 frontmatter 是否包含指定欄位（不完整解析）。

    Args:
        iContent: Markdown 原始內容。
        iField:   欄位名稱。
        iValue:   欄位值（空字串 = 只檢查欄位是否存在）。

    Returns:
        True = 欄位存在且值匹配（或不指定值）。
    """
    _Match = _FM_PATTERN.match( iContent )
    if not _Match:
        return False

    _Fm = _Match.group( 1 )
    if iValue:
        return f"{iField}: {iValue}" in _Fm or f'{iField}: "{iValue}"' in _Fm
    return f"{iField}:" in _Fm
