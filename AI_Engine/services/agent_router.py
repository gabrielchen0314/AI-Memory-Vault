"""
Agent Router 服務
讀取 Vault templates/agents/ 目錄下的 Agent 模板，提供查詢與分發功能。

Agent 模板格式：YAML frontmatter（type: agent-template）+ Markdown 指令本體。
透過 trigger（@AgentName）或 domain 進行路由匹配。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.10
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Optional

from core.logger import get_logger

_logger = get_logger( __name__ )


@dataclass
class AgentTemplate:
    """Agent 模板資料結構。"""
    name:           str
    trigger:        str
    domain:         str
    summary:        str              = ""
    mcp_tools:      list[str]        = field( default_factory=list )
    related_rules:  list[str]        = field( default_factory=list )
    workspace:      str              = "_shared"
    body:           str              = ""
    file_path:      str              = ""


class AgentRouter:
    """
    Agent 路由器：從 Vault templates/agents/ 掃描 .md 模板。
    提供 list / get / resolve 三種查詢方式。
    """

    def __init__( self, iVaultPath: str, iTemplateDir: str = "templates/agents" ):
        self._vault_path   = iVaultPath
        self._template_dir = os.path.join( iVaultPath, iTemplateDir )
        self._agents: dict[str, AgentTemplate] = {}
        self._loaded = False

    # ── 載入 ──────────────────────────────────────────────

    def _ensure_loaded( self ) -> None:
        if not self._loaded:
            self._scan()

    def _scan( self ) -> None:
        """掃描 templates/agents/*.md 並解析 frontmatter。"""
        self._agents.clear()
        if not os.path.isdir( self._template_dir ):
            _logger.warning( "Agent template dir not found: %s", self._template_dir )
            self._loaded = True
            return

        for _FileName in sorted( os.listdir( self._template_dir ) ):
            if not _FileName.endswith( ".md" ):
                continue
            _AbsPath = os.path.join( self._template_dir, _FileName )
            try:
                _Tpl = self._parse_template( _AbsPath )
                if _Tpl:
                    _Key = _Tpl.name.lower()
                    self._agents[_Key] = _Tpl
            except Exception as _E:
                _logger.warning( "Failed to parse agent template %s: %s", _FileName, _E )

        self._loaded = True
        _logger.info( "Loaded %d agent templates", len( self._agents ) )

    @staticmethod
    def _parse_template( iPath: str ) -> Optional[AgentTemplate]:
        """解析單一 .md 模板檔案。回傳 AgentTemplate 或 None。"""
        with open( iPath, "r", encoding="utf-8" ) as _F:
            _Raw = _F.read()

        if not _Raw.startswith( "---" ):
            return None
        _End = _Raw.find( "---", 3 )
        if _End == -1:
            return None

        _Fm = _Raw[3:_End]
        _Body = _Raw[_End + 3:].strip()

        # 簡易 YAML 解析（避免引入 pyyaml 依賴）
        def _get( key: str, default="" ) -> str:
            _M = re.search( rf'^{key}:\s*["\']?(.+?)["\']?\s*$', _Fm, re.MULTILINE )
            return _M.group( 1 ).strip() if _M else default

        def _get_list( key: str ) -> list:
            _M = re.search( rf'^{key}:\s*\[(.+?)\]', _Fm, re.MULTILINE )
            if not _M:
                return []
            return [ _Item.strip().strip( "\"'" ) for _Item in _M.group( 1 ).split( "," ) ]

        _Type = _get( "type" )
        if _Type != "agent-template":
            return None

        return AgentTemplate(
            name=_get( "agent", os.path.splitext( os.path.basename( iPath ) )[0] ),
            trigger=_get( "trigger" ),
            domain=_get( "domain" ),
            summary=_get( "ai_summary" ),
            mcp_tools=_get_list( "mcp_tools" ),
            related_rules=_get_list( "related_rules" ),
            workspace=_get( "workspace", "_shared" ),
            body=_Body,
            file_path=iPath,
        )

    # ── 查詢 ──────────────────────────────────────────────

    def list_agents( self ) -> list[dict]:
        """回傳所有 Agent 的摘要清單。"""
        self._ensure_loaded()
        _Result = []
        for _Tpl in self._agents.values():
            _Result.append( {
                "name":    _Tpl.name,
                "trigger": _Tpl.trigger,
                "domain":  _Tpl.domain,
                "summary": _Tpl.summary,
                "tools":   _Tpl.mcp_tools,
            } )
        return _Result

    def get_agent( self, iName: str ) -> Optional[AgentTemplate]:
        """以名稱（不分大小寫）取得 Agent 模板。"""
        self._ensure_loaded()
        return self._agents.get( iName.lower() )

    def resolve( self, iQuery: str ) -> Optional[AgentTemplate]:
        """
        以 trigger 或 domain 模糊匹配 Agent。
        優先順序：trigger 完全匹配 > domain 完全匹配 > name 包含匹配。
        """
        self._ensure_loaded()
        _Q = iQuery.lower().strip().lstrip( "@" )

        # 1. trigger match
        for _Tpl in self._agents.values():
            if _Tpl.trigger.lower().lstrip( "@" ) == _Q:
                return _Tpl

        # 2. domain match
        for _Tpl in self._agents.values():
            if _Tpl.domain.lower() == _Q:
                return _Tpl

        # 3. name substring match
        for _Tpl in self._agents.values():
            if _Q in _Tpl.name.lower():
                return _Tpl

        return None

    def reload( self ) -> int:
        """強制重新掃描模板目錄。回傳載入的 Agent 數量。"""
        self._loaded = False
        self._ensure_loaded()
        return len( self._agents )
