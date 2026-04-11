"""
MCP 工具模組 — 排程生成工具
generate_project_daily / generate_daily_review / generate_weekly_review /
generate_monthly_review / generate_ai_weekly_analysis / generate_ai_monthly_analysis /
generate_project_status / log_ai_conversation

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.08
"""
from __future__ import annotations
from typing import Optional
from mcp_app.utils import suppress_stdout


def register( mcp, get_sched ):
    """將排程生成工具註冊到 MCP Server。get_sched() 回傳 SchedulerService 單例。"""

    @mcp.tool()
    @suppress_stdout
    def generate_project_daily( organization: str, project: str, date: str = "" ) -> str:
        """
        生成指定專案的每日詳細進度模板。已存在則回傳路徑不覆蓋。
        organization: 組織名稱（例如 CHINESEGAMER, LIFEOFDEVELOPMENT）。
        project: 專案名稱（例如 game-server, ai-memory-vault）。
        date: 日期 YYYY-MM-DD（預設今天）。
        """
        _Path = get_sched().generate_project_daily( organization, project, date or None )
        return f"專案每日進度已就緒：{_Path}"

    @mcp.tool()
    @suppress_stdout
    def generate_daily_review( date: str = "", projects: list = [] ) -> str:
        """
        生成每日總進度表（所有專案重點摘要）。每次呼叫都會覆寫內容。
        文本放在 personal/reviews/daily/，連結放在 _global/reviews/daily/。
        date: 日期 YYYY-MM-DD（預設今天）。
        projects: 各專案摘要 list，每項含 organization/project/summary 欄位（選填）。
        """
        _Path = get_sched().generate_daily_summary( date or None, projects or None )
        return f"每日總進度表已就緒：{_Path}"

    @mcp.tool()
    @suppress_stdout
    def generate_weekly_review( date: str = "" ) -> str:
        """
        生成每週總進度表。自動計算 ISO 週數。
        文本放在 personal/reviews/weekly/，連結放在 _global/reviews/weekly/。
        date: 該週內的任一天 YYYY-MM-DD（預設今天）。
        """
        _Path = get_sched().generate_weekly_summary( date or None )
        return f"每週總進度表已就緒：{_Path}"

    @mcp.tool()
    @suppress_stdout
    def generate_monthly_review( date: str = "" ) -> str:
        """
        生成每月總進度表。
        文本放在 personal/reviews/monthly/，連結放在 _global/reviews/monthly/。
        date: 該月內的任一天 YYYY-MM-DD（預設今天）。
        """
        _Path = get_sched().generate_monthly_summary( date or None )
        return f"每月總進度表已就緒：{_Path}"

    @mcp.tool()
    @suppress_stdout
    def log_ai_conversation(
        organization:      str,
        project:           str,
        session_name:      str,
        content:           str,
        detail:            Optional[dict] = None,
        vscode_session_id: str = "",
    ) -> str:
        """
        記錄一次 AI 對話至指定專案的 conversations/ 目錄。
        organization: 組織名稱（例如 LIFEOFDEVELOPMENT）。
        project: 專案名稱（例如 ai-memory-vault）。
        session_name: 對話主題名（例如 vault-setup）。
        content: 對話摘要內容（Markdown 格式）。

        vscode_session_id: （選填）VS Code chatSession UUID。
          若提供，自動從 chatSessions/JSONL 解析 files_changed + commands 填入 detail，
          AI 只需填 topic / problems / learnings / decisions / interaction_issues。

        detail: （選填）結構化詳細紀錄 dict。可包含：
          - topic (str): 對話主題
          - qa_pairs (list)  ← 若有 vscode_session_id 可省略（session 檔已含完整 Q&A）
          - files_changed (list) ← 若有 vscode_session_id 可省略（自動提取）
          - commands (list)      ← 若有 vscode_session_id 可省略（自動提取）
          - problems (list): 問題與解決 [{"problem", "cause", "solution"}]
          - learnings (list): 學到的知識 (str 列表)
          - decisions (list): 決策記錄 [{"decision", "options", "chosen", "reason"}]
          - interaction_issues (list): 互動問題 [{"type", "description", ...}]
        """
        # ── 若提供 vscode_session_id，自動補全 files_changed + commands ──
        if vscode_session_id:
            from config import AppConfig, ConfigManager
            _Config = ConfigManager.load()
            if _Config.vscode_chat_dir:
                from services.session_extractor import SessionExtractor
                _SE   = SessionExtractor( _Config.vscode_chat_dir, _Config.vault_path )
                _Meta = _SE.extract_metadata( vscode_session_id )
                detail = detail or {}
                if _Meta.get( "files_changed" ) and not detail.get( "files_changed" ):
                    detail[ "files_changed" ] = _Meta[ "files_changed" ]
                if _Meta.get( "commands" ) and not detail.get( "commands" ):
                    detail[ "commands" ] = _Meta[ "commands" ]

        _Path = get_sched().log_conversation(
            organization, project, session_name, content, detail
        )
        return f"AI 對話已記錄：{_Path}"

    @mcp.tool()
    @suppress_stdout
    def extract_session_script(
        session_id:     str,
        script_type:    str = "powershell",
        output_to_file: bool = False,
        organization:   str = "",
        project:        str = "",
    ) -> str:
        """
        從指定 VS Code chatSession 提取所有 terminal 指令，輸出為可執行腳本。
        可用於將「AI 探索通的流程」固化為 0-Token 腳本。

        session_id: VS Code chatSession UUID（vscode_sessions_watermark.json 中可查）。
        script_type: "powershell"（預設）| "python"。
        output_to_file: True 時將腳本寫入 Vault conversations/ 目錄旁的 scripts/ 資料夾。
        organization: output_to_file=True 時需提供。
        project: output_to_file=True 時需提供。
        """
        from config import ConfigManager
        _Config = ConfigManager.load()
        if not _Config.vscode_chat_dir:
            return "錯誤：config.json 未設定 vscode_chat_dir"

        from services.session_extractor import SessionExtractor
        _SE     = SessionExtractor( _Config.vscode_chat_dir, _Config.vault_path )
        _Script = _SE.extract_script( session_id, script_type )

        if not _Script:
            return f"Session {session_id[:8]} 中無 terminal 指令可提取"

        if output_to_file and organization and project:
            from pathlib import Path
            _Dir = (
                Path( _Config.vault_path )
                / "workspaces" / organization / "projects" / project / "scripts"
            )
            _Dir.mkdir( parents=True, exist_ok=True )
            _Ext  = ".ps1" if script_type == "powershell" else ".py"
            _File = _Dir / f"extracted-{session_id[:8]}{_Ext}"
            _File.write_text( _Script, encoding="utf-8" )
            return f"腳本已寫入：{_File}\n\n```{script_type}\n{_Script}\n```"

        return f"```{script_type}\n{_Script}\n```"


    @mcp.tool()
    @suppress_stdout
    def generate_ai_weekly_analysis( date: str = "" ) -> str:
        """
        生成 AI 對話每週分析模板。自動掃描所有專案當週的對話紀錄。
        內容包含：對話準確率、Token 消耗、每專案統計、評分。
        date: 該週內的任一天 YYYY-MM-DD（預設今天）。
        """
        _Path = get_sched().generate_ai_weekly_analysis( date or None )
        return f"AI 對話週報已就緒：{_Path}"

    @mcp.tool()
    @suppress_stdout
    def generate_ai_monthly_analysis( date: str = "" ) -> str:
        """
        生成 AI 對話每月分析模板。自動掃描專案對話 + 彙整週報。
        內容包含：趨勢分析、優化建議、月度評分、成長追蹤。
        date: 該月內的任一天 YYYY-MM-DD（預設今天）。
        """
        _Path = get_sched().generate_ai_monthly_analysis( date or None )
        return f"AI 對話月報已就緒：{_Path}"

    @mcp.tool()
    @suppress_stdout
    def generate_project_status( organization: str, project: str ) -> str:
        """
        生成指定專案的 status.md 模板（待辦 + 工作脈絡 + 決策記錄）。
        冪等：已存在則回傳路徑，不覆蓋現有內容。
        organization: 組織名稱（例如 LIFEOFDEVELOPMENT）。
        project: 專案名稱（例如 ai-memory-vault）。
        """
        _Path = get_sched().generate_project_status( organization, project )
        return f"專案狀態檔已就緒：{_Path}"

    @mcp.tool()
    @suppress_stdout
    def list_scheduled_tasks() -> str:
        """
        列出所有可用的自動排程任務及其排程時間。
        回傳每個任務的 ID、名稱、說明、排程規則。
        """
        from services.auto_scheduler import AutoScheduler
        _Tasks = AutoScheduler.list_tasks()
        _Lines = [ f"共 {len(_Tasks)} 個排程任務：\n" ]
        for _T in _Tasks:
            _Lines.append( f"- **{_T['id']}**（{_T['name']}）：{_T['description']}  排程：{_T['schedule']}" )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def run_scheduled_task( task_id: str ) -> str:
        """
        手動觸發一個排程任務。
        task_id: 任務 ID（使用 list_scheduled_tasks 查看可用 ID）。
        可用 ID：daily-summary, weekly-summary, weekly-ai, monthly-summary, monthly-ai, vector-sync, morning-brief, auto-all
        """
        from services.auto_scheduler import AutoScheduler
        _Sched = get_sched()
        _Auto  = AutoScheduler( _Sched.m_Config )
        _Results = _Auto.run_task( task_id )
        return "\n".join( f"{_Label}: {_Detail}" for _Label, _Detail in _Results )
