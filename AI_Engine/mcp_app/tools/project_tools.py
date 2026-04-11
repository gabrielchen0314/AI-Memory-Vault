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
        from services.vault import VaultService
        _Result, _Err = VaultService.list_projects()
        if _Err:
            return f"❌ {_Err}"
        if not _Result:
            return "未找到任何組織或專案。"

        _Lines = []
        for _Org in _Result:
            _Lines.append( f"\n## {_Org['organization']}\n" )
            if _Org["projects"]:
                for _Proj in _Org["projects"]:
                    _Icon = "✅" if _Proj["has_status"] else "⬜"
                    _Lines.append( f"- {_Icon} `{_Proj['name']}`" )
            else:
                _Lines.append( "（尚無專案）" )

        return "\n".join( _Lines ).strip()

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
