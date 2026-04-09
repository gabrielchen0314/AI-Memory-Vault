"""
MCP 工具模組 — Agent 與 Skill 管理
list_agents / dispatch_agent / list_skills / load_skill

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.10
"""
from __future__ import annotations
from mcp_app.utils import suppress_stdout


def register( mcp ):
    """將 Agent / Skill 管理工具註冊到 MCP Server。"""

    @mcp.tool()
    @suppress_stdout
    def list_agents() -> str:
        """
        列出 Vault 中所有可用的 Agent 模板。
        每個 Agent 包含名稱、觸發指令、領域、摘要。
        Agent 模板存放在 Vault templates/agents/ 目錄。
        """
        from config import ConfigManager
        from services.agent_router import AgentRouter
        _Config = ConfigManager.load()
        _Router = AgentRouter( _Config.vault_path )
        _Agents = _Router.list_agents()
        if not _Agents:
            return "Vault 中沒有任何 Agent 模板（templates/agents/ 為空）。"
        _Lines = [ f"Available Agents ({len(_Agents)}):", "" ]
        for _A in _Agents:
            _Lines.append( f"  {_A['trigger']:<20}  {_A['domain']:<16}  {_A['summary']}" )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def dispatch_agent( agent_name: str ) -> str:
        """
        載入並回傳指定 Agent 的完整指令（Markdown 本體 + 關聯規則路徑）。
        agent_name: Agent 名稱、觸發指令（@Architect）、或領域（architecture）。
        典型用途：AI Client 根據回傳的指令調整行為模式。
        """
        from config import ConfigManager
        from services.agent_router import AgentRouter
        _Config = ConfigManager.load()
        _Router = AgentRouter( _Config.vault_path )
        _Tpl = _Router.resolve( agent_name )
        if not _Tpl:
            _Available = _Router.list_agents()
            _Names = ", ".join( _A["name"] for _A in _Available )
            return f"找不到 Agent '{agent_name}'。可用：{_Names}"
        _Lines = [
            f"# {_Tpl.name} Agent",
            f"領域：{_Tpl.domain}",
            f"工具：{', '.join(_Tpl.mcp_tools)}",
        ]
        if _Tpl.related_rules:
            _Lines.append( f"相關規則：{', '.join(_Tpl.related_rules)}" )
        _Lines.append( "" )
        _Lines.append( _Tpl.body )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def list_skills() -> str:
        """
        列出 Vault 中 workspaces/_global/skills/ 下所有 Skill 知識包。
        回傳檔案清單與大小，可搭配 load_skill 讀取完整內容。
        """
        import os
        from config import ConfigManager
        _Config = ConfigManager.load()
        _SkillDir = os.path.join( _Config.vault_path, "workspaces", "_global", "skills" )
        if not os.path.isdir( _SkillDir ):
            return "Skill 目錄不存在（workspaces/_global/skills/）。"
        _Files = sorted(
            _F for _F in os.listdir( _SkillDir )
            if _F.endswith( ".md" ) and _F != "index.md"
        )
        if not _Files:
            return "workspaces/_global/skills/ 目錄下沒有任何 Skill 技能包。"
        _Lines = [ f"可用技能包（{len(_Files)} 個）：", "" ]
        for _F in _Files:
            _Abs = os.path.join( _SkillDir, _F )
            _Kb = os.path.getsize( _Abs ) / 1024
            _Lines.append( f"  {_F:<40} ({_Kb:.1f}KB)" )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def load_skill( skill_name: str ) -> str:
        """
        讀取指定 Skill 知識包的完整內容。
        skill_name: 檔案名（如 CSharpCodingStyle_Skill.md）或不含副檔名的名稱。
        """
        import os
        from config import ConfigManager
        _Config = ConfigManager.load()
        _SkillDir = os.path.join( _Config.vault_path, "workspaces", "_global", "skills" )
        if not skill_name.endswith( ".md" ):
            skill_name += ".md"
        _Abs = os.path.join( _SkillDir, skill_name )
        # 防止路徑穿越
        _Real = os.path.realpath( _Abs )
        if not _Real.startswith( os.path.realpath( _SkillDir ) ):
            return "❌ 路徑安全驗證失敗，拒絕存取。"
        if not os.path.isfile( _Abs ):
            return f"找不到技能包 '{skill_name}'（workspaces/_global/skills/）"
        with open( _Abs, "r", encoding="utf-8" ) as _F:
            return _F.read()
