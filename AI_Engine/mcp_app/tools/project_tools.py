"""
MCP 工具模組 — 專案與知識管理
list_projects / get_project_status / extract_knowledge

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.08
"""
from __future__ import annotations
from mcp_app.utils import suppress_stdout


def register( mcp ):
    """將專案管理工具註冊到 MCP Server。"""

    @mcp.tool()
    @suppress_stdout
    def list_projects() -> str:
        """
        列出 Vault 中所有組織及其下的專案清單。
        回傳格式化的 Markdown 表格，每個組織一個區段。
        """
        import os
        from config import ConfigManager
        _Config = ConfigManager.load()
        _P = _Config.paths
        _WorkspacesAbs = os.path.join( _Config.vault_path, _P.workspaces )

        if not os.path.isdir( _WorkspacesAbs ):
            return "Vault workspaces 目錄不存在。"

        _Lines = []
        for _OrgEntry in sorted( os.listdir( _WorkspacesAbs ) ):
            if _OrgEntry.startswith( "_" ):
                continue
            _OrgDir = os.path.join( _WorkspacesAbs, _OrgEntry )
            if not os.path.isdir( _OrgDir ):
                continue

            _ProjectsDir = os.path.join( _OrgDir, _P.org_projects )
            _Projects = []
            if os.path.isdir( _ProjectsDir ):
                for _ProjEntry in sorted( os.listdir( _ProjectsDir ) ):
                    if os.path.isdir( os.path.join( _ProjectsDir, _ProjEntry ) ):
                        _Projects.append( _ProjEntry )

            _Lines.append( f"\n## {_OrgEntry}\n" )
            if _Projects:
                for _Proj in _Projects:
                    _StatusPath = _P.project_status_file( _OrgEntry, _Proj )
                    _StatusAbs = os.path.join( _Config.vault_path, _StatusPath )
                    _HasStatus = "✅" if os.path.isfile( _StatusAbs ) else "⬜"
                    _Lines.append( f"- {_HasStatus} `{_Proj}`" )
            else:
                _Lines.append( "（尚無專案）" )

        return "\n".join( _Lines ).strip() if _Lines else "未找到任何組織或專案。"

    @mcp.tool()
    @suppress_stdout
    def get_project_status( organization: str, project: str ) -> str:
        """
        讀取指定專案的 status.md 並回傳結構化資料：
        待辦事項清單、已完成數量、工作脈絡。
        比 read_note 更適合 AI 讀取待辦項目（不需解析 Markdown）。
        organization: 組織名稱。
        project: 專案名稱。
        """
        from services.vault import VaultService
        _Result, _Err = VaultService.get_project_status( organization, project )
        if _Err:
            return f"❌ {_Err}"
        _Pending = _Result["pending_todos"]
        _Lines = [
            f"path: {_Result['path']}",
            f"last_updated: {_Result['last_updated']}",
            f"pending_todos: {len( _Pending )}",
            f"completed_count: {_Result['completed_count']}",
        ]
        if _Pending:
            _Lines.append( "\nPending:" )
            _Lines.extend( f"  - {_T}" for _T in _Pending )
        if _Result["context_summary"]:
            _Lines.append( f"\nContext:\n{_Result['context_summary']}" )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def extract_knowledge( organization: str, project: str, topic: str, session: str = "" ) -> str:
        """
        從指定專案的 conversations/ 萃取知識卡片，寫入 knowledge/{date}-{topic}.md。
        掃描對話檔案的標題與重點條列，生成知識卡片草稿供人工審閱。
        冪等：已存在同 topic 的卡片時，以追加模式補充新來源連結。
        organization: 組織名稱（例如 LIFEOFDEVELOPMENT）。
        project:      專案名稱（例如 ai-memory-vault）。
        topic:        知識主題（英文 slug，例如 chromadb-sync）。
        session:      篩選特定 session 名稱（留空 = 掃描所有）。
        """
        from config import ConfigManager
        from services.knowledge_extractor import KnowledgeExtractor
        _Config = ConfigManager.load()
        _Extractor = KnowledgeExtractor( _Config )
        _Path, _Err = _Extractor.extract( organization, project, topic, session or None )
        if _Err:
            return _Err
        return f"知識卡片已就緒：{_Path}"
