"""
CLI 互動介面 (v3)
直接呼叫 VaultService / SchedulerService，對應全部 MCP 工具功能。
不依賴 LLM — 純工具操作介面，啟動快速、離線可用。

指令清單：
  search <query> [--cat <category>] [--type <doc_type>] [--mode keyword|semantic]
  read <path>
  write <path>
  edit <path>                      局部文字替換（精確替換，不全文覆寫）
  grep <pattern> [<path>] [-r]     精確文字 / 正規表達式搜尋
  delete <path>
  sync
  batchwrite <json>                批次寫入筆記（JSON 檔案路徑）
  status <org> <project>          讀取專案狀態 (get_project_status)
  todo <path> <text> [done|undone]
  addtodo <path> <text> [<section>]  新增 todo 項目
  rmtodo <path> <text>               移除 todo 項目
  daily <org> <project> [<date>]   生成專案每日進度
  review [<date>]                  生成每日總進度表 (generate_daily_review)
  weekly                           生成每週總進度表
  monthly                          生成每月總進度表
  genstatus <org> <project>        生成專案 status.md 模板 (generate_project_status)
  log <org> <project> <session>    記錄 AI 對話 (log_ai_conversation)
  aiweekly [<date>]                生成 AI 對話週報
  aimonthly [<date>]               生成 AI 對話月報
  projects                         列出所有組織與專案
  backup                           立即備份 ChromaDB（保留最新 7 份）
  integrity                        檢查 ChromaDB 向量完整性
  clean                            清除孤立向量記錄（對應 .md 已刪除）
  rename <old_path> <new_path>     移動或重命名 .md 檔案並同步向量索引
  checkindex                       檢查向量索引是否因設定變更需重建
  reindex                          清除並重建 ChromaDB 向量索引
  instincts [<domain>]             列出所有直覺卡片
  sinst <query> [<domain>]         語意搜尋直覺卡片
  newinst                          互動式建立直覺卡片
  updinst <id> <delta> [<evidence>] 更新直覺信心度
  retro [<YYYY-MM>]                生成月度復盤報告
  agents                           列出所有 Agent 模板
  dispatch <agent>                 載入 Agent 完整指令（名稱/觸發/領域）
  skills                           列出所有 Skill 知識包
  skill <name>                     讀取 Skill 知識包完整內容
  tasks                            列出所有排程任務
  runtask <task_id>                手動觸發排程任務
  exscript <session_id> [type]     從 VS Code Session 提取腳本
  help
  q / exit

@author gabrielchen
@version 3.3
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
import sys
from typing import Optional
from cli.registry import TOOL_REGISTRY, REGISTRY_BY_NAME


class VaultRepl:
    """AI Memory Vault v3 互動式 CLI。"""

    ## <summary>短指令別名表（全部自動產生自 TOOL_REGISTRY + help）</summary>
    _ALIASES: dict = {
        **{ t.alias: t.name for t in TOOL_REGISTRY },
        "h": "help",
    }

    ## <summary>應用程式設定</summary>
    m_Config: object
    ## <summary>排程服務實例</summary>
    m_Sched: object

    def __init__( self, iConfig ):
        """
        建立 REPL 實例。

        Args:
            iConfig: 已初始化的 AppConfig。
        """
        self.m_Config = iConfig
        from services.scheduler import SchedulerService
        self.m_Sched = SchedulerService( iConfig )
        self._setup_readline()
        self._HELP = self._build_help()

    def _setup_readline( self ) -> None:
        """啟用 readline（歷史記錄 + Tab 補全）；不可用時靜默降級。"""
        try:
            import readline as _rl
        except ImportError:
            try:
                import pyreadline3 as _rl  # type: ignore
            except ImportError:
                return

        _AllCmds = list( self._ALIASES.keys() ) + [ t.name for t in TOOL_REGISTRY ] + [ "help", "exit" ]

        def _completer( iText: str, iState: int ):
            _Matches = [ c for c in _AllCmds if c.startswith( iText ) ]
            return _Matches[iState] if iState < len( _Matches ) else None

        _rl.set_completer( _completer )
        _rl.parse_and_bind( "tab: complete" )

    #region 公開方法
    def run( self ) -> None:
        """啟動指令列模式（原始 REPL）。"""
        print( "\n✅ AI Memory Vault v3 — CLI 已就緒" )
        print( "   輸入 'help' 查看指令列表 | 'q' 離開 | '--menu' 切換選單模式\n" )

        try:
            while True:
                try:
                    _Line = input( "vault> " ).strip()
                except EOFError:
                    break

                if not _Line:
                    continue
                if _Line.lower() in ( "q", "exit" ):
                    print( "👋 已離開 AI Memory Vault CLI。" )
                    break
                if _Line.lower() == "--menu":
                    self.run_menu()
                    continue

                self._dispatch( _Line )

        except KeyboardInterrupt:
            print( "\n👋 已中斷，離開 CLI。" )

    def run_menu( self ) -> None:
        """啟動互動選單模式（方向鍵選擇）。"""
        try:
            import questionary
        except ImportError:
            print( "⚠️  需要 questionary：pip install questionary" )
            return

        # 全部自動產生自 TOOL_REGISTRY（依 group 分組，群組切換時插入分隔線）
        _MenuChoices = []
        _CurGroup = ""
        for _T in TOOL_REGISTRY:
            if _T.group != _CurGroup:
                _CurGroup = _T.group
                _MenuChoices.append( questionary.Separator( "─" * 40 ) )
            _MenuChoices.append( questionary.Choice( f"{_T.icon}  {_T.menu_label}", value=_T.name ) )
        _MenuChoices += [
            questionary.Separator( "─" * 40 ),
            questionary.Choice( "⌨️   切換指令列模式", value="_repl" ),
            questionary.Choice( "👋  離開",             value="_exit" ),
        ]

        print( "\n✅ AI Memory Vault v3 — 選單模式（↑↓ 選擇，Enter 確認）\n" )
        while True:
            try:
                _Choice = questionary.select(
                    "請選擇操作：",
                    choices=_MenuChoices,
                    use_shortcuts=False,
                ).ask()
            except KeyboardInterrupt:
                print( "\n👋 已中斷。" )
                break

            if _Choice is None or _Choice == "_exit":
                print( "👋 已離開 AI Memory Vault CLI。" )
                break
            if _Choice == "_repl":
                self.run()
                break

            print()  # 確保視覺分隔
            try:
                self._menu_dispatch( _Choice, questionary )
            except Exception as _Ex:
                print( f"\n❌ 執行失敗：{_Ex}" )
            input( "\n  ↵ 按 Enter 回到選單..." )

    def _menu_dispatch( self, iCmd: str, q ) -> None:
        """根據選單選擇，用 questionary prompt 收集參數後執行。"""
        # 1. Registry 工具（invoke 非 None）→ 通用收集器自動分發
        _Entry = REGISTRY_BY_NAME.get( iCmd )
        if not _Entry:
            print( f"❓ 未知操作：{iCmd}" )
            return

        if _Entry.invoke is not None:
            from services.vault import VaultService
            _Kwargs = self._collect_params( q, _Entry )
            if _Kwargs is None:
                return
            _Result = _Entry.invoke( self.m_Sched, VaultService, **_Kwargs )
            if isinstance( _Result, str ):
                print( f"✅ {_Result}" )
            return

        # 2. 手動工具（複雜互動或特殊輸出格式）
        if iCmd == "search":
            _Query = q.text( "搜尋關鍵字：" ).ask()
            if not _Query:
                return
            _Mode = q.select(
                "搜尋模式：",
                choices=[ "均衡（預設）", "keyword（關鍵字優先）", "semantic（語意優先）" ],
            ).ask()
            _ModeArg = "" if "均衡" in _Mode else ( "keyword" if "keyword" in _Mode else "semantic" )
            _TopFolder = self._pick_top_folder( q, title="限縮搜尋範圍（留空=全庫）：", allow_skip=True )
            _SearchArgs = [_Query]
            if _ModeArg:
                _SearchArgs += ["--mode", _ModeArg]
            if _TopFolder:
                _SearchArgs += ["--cat", _TopFolder]
            self._cmd_search( _SearchArgs )

        elif iCmd == "read":
            _Path = self._pick_vault_path( q )
            if _Path:
                self._cmd_read( [_Path] )

        elif iCmd == "write":
            _Where = q.select(
                "寫入位置：",
                choices=[
                    q.__class__.Choice( "📋  現有專案（workspaces）", value="project" ),
                    q.__class__.Choice( "💡  知識卡片（knowledge/）",  value="knowledge" ),
                    q.__class__.Choice( "👤  個人筆記（personal/）",   value="personal" ),
                    q.__class__.Choice( "⌨️   手動輸入完整路徑",        value="custom" ),
                ],
            ).ask()
            if _Where == "project":
                _Org  = self._pick_org( q )
                if not _Org:
                    return
                _Proj = self._pick_project( q, _Org )
                if not _Proj:
                    return
                _Sub = q.select(
                    "寫入子目錄：",
                    choices=[ "daily/", "notes/", "conversations/", "meetings/", "（根目錄）" ],
                ).ask()
                _P = self.m_Config.paths
                _Base = f"{_P.workspaces}/{_Org}/{_P.org_projects}/{_Proj}"
                _Sub  = "" if "根目錄" in _Sub else _Sub
                _Name = q.text( "檔案名稱（含 .md）：" ).ask()
                if not _Name:
                    return
                _Path = f"{_Base}/{_Sub}{_Name}"
            elif _Where == "knowledge":
                _Name = q.text( "檔名（含 .md）：" ).ask()
                if not _Name:
                    return
                _Path = f"knowledge/{_Name}"
            elif _Where == "personal":
                _Sub = q.select(
                    "子目錄：",
                    choices=[ "journal/", "reviews/daily/", "reviews/weekly/", "goals/", "ideas/", "（根目錄）" ],
                ).ask()
                _Sub  = "" if "根目錄" in _Sub else _Sub
                _Name = q.text( "檔名（含 .md）：" ).ask()
                if not _Name:
                    return
                _Path = f"personal/{_Sub}{_Name}"
            else:
                _Path = q.text( "完整相對路徑：" ).ask()
            if _Path:
                self._cmd_write( [_Path] )

        elif iCmd == "delete":
            _Path = self._pick_vault_path( q )
            if _Path:
                self._cmd_delete( [_Path] )

        elif iCmd == "rename":
            _OldPath = self._pick_vault_path( q )
            if not _OldPath:
                return
            _NewPath = q.text( "目標路徑（相對 Vault 根目錄）：", default=_OldPath ).ask()
            if _NewPath and _NewPath != _OldPath:
                self._cmd_rename( [_OldPath, _NewPath] )

        elif iCmd == "list":
            _Top = self._pick_top_folder( q, title="選擇目錄：", allow_skip=True )
            if _Top is None:
                return
            _Rec = q.confirm( "遞迴列出子目錄？", default=False ).ask()
            _Args = [_Top] if _Top else []
            if _Rec:
                _Args.append( "-r" )
            self._cmd_list( _Args )

        elif iCmd == "sync":
            self._cmd_sync( [] )

        elif iCmd == "batchwrite":
            _JsonPath = q.text( "JSON 檔案路徑：" ).ask()
            if _JsonPath:
                self._cmd_batchwrite( [_JsonPath] )

        elif iCmd == "status":
            _Org  = self._pick_org( q )
            if not _Org:
                return
            _Proj = self._pick_project( q, _Org )
            if _Proj:
                self._cmd_status( [_Org, _Proj] )

        elif iCmd == "todo":
            _Org  = self._pick_org( q )
            if not _Org:
                return
            _Proj = self._pick_project( q, _Org )
            if not _Proj:
                return
            _Path = self._pick_project_file( q, _Org, _Proj )
            if not _Path:
                return
            _Text  = q.text( "Todo 文字（部分比對）：" ).ask()
            if not _Text:
                return
            _State = q.select( "狀態：", choices=[ "✅ done（完成）", "⬜ undone（未完成）" ] ).ask()
            self._cmd_todo( [_Path, _Text, "done" if "done" in _State else "undone"] )

        elif iCmd == "projects":
            self._cmd_projects( [] )

        elif iCmd == "integrity":
            self._cmd_integrity( [] )

        elif iCmd == "clean":
            self._cmd_clean_orphans( [] )

        elif iCmd == "checkindex":
            self._cmd_checkindex( [] )

        elif iCmd == "reindex":
            self._cmd_reindex( [] )

        elif iCmd == "edit":
            _Path = self._pick_vault_path( q )
            if _Path:
                self._cmd_edit( [_Path] )

        elif iCmd == "grep":
            _Pattern = q.text( "搜尋文字（或 regex）：" ).ask()
            if not _Pattern:
                return
            _Top     = self._pick_top_folder( q, title="限縮目錄（留空=全 Vault）：", allow_skip=True )
            _IsRegex = q.confirm( "使用正規表達式？", default=False ).ask()
            _Args    = [_Pattern]
            if _Top:
                _Args.append( _Top )
            if _IsRegex:
                _Args.append( "-r" )
            self._cmd_grep( _Args )

        elif iCmd == "backup":
            self._cmd_backup( [] )

        elif iCmd == "addtodo":
            _Org  = self._pick_org( q )
            if not _Org:
                return
            _Proj = self._pick_project( q, _Org )
            if not _Proj:
                return
            _Path = self._pick_project_file( q, _Org, _Proj )
            if not _Path:
                return
            _Text    = q.text( "新增 Todo 文字：" ).ask()
            if not _Text:
                return
            _Section = q.text( "目標段落（留空=待處理）：" ).ask() or ""
            self._cmd_addtodo( [_Path, _Text] + ( [_Section] if _Section else [] ) )

        elif iCmd == "rmtodo":
            _Org  = self._pick_org( q )
            if not _Org:
                return
            _Proj = self._pick_project( q, _Org )
            if not _Proj:
                return
            _Path = self._pick_project_file( q, _Org, _Proj )
            if not _Path:
                return
            _Text = q.text( "要移除的 Todo 文字（部分比對）：" ).ask()
            if _Text:
                self._cmd_rmtodo( [_Path, _Text] )

        elif iCmd == "instincts":
            _Domain = q.text( "篩選 domain（留空=全部）：" ).ask() or ""
            self._cmd_instincts( [_Domain] if _Domain else [] )

        elif iCmd == "sinst":
            _Query = q.text( "搜尋關鍵字：" ).ask()
            if not _Query:
                return
            _Domain = q.text( "篩選 domain（留空=全部）：" ).ask() or ""
            _Args = [_Query]
            if _Domain:
                _Args.append( _Domain )
            self._cmd_sinst( _Args )

        elif iCmd == "newinst":
            self._cmd_newinst( [] )

        elif iCmd == "updinst":
            _Id    = q.text( "卡片 ID（slug 格式）：" ).ask()
            if not _Id:
                return
            _Delta = q.text( "信心度增減（如 +0.1 / -0.05）：" ).ask()
            if not _Delta:
                return
            _Evid  = q.text( "新增證據（留空=不加）：" ).ask() or ""
            _Args  = [_Id, _Delta]
            if _Evid:
                _Args.append( _Evid )
            self._cmd_updinst( _Args )

        elif iCmd == "retro":
            _Month = q.text( "月份（YYYY-MM，留空=上月）：" ).ask() or ""
            self._cmd_retro( [_Month] if _Month else [] )

        elif iCmd == "agents":
            self._cmd_agents( [] )

        elif iCmd == "dispatch":
            _Name = q.text( "Agent 名稱（@Architect / architecture / 名稱）：" ).ask()
            if _Name:
                self._cmd_dispatch( [_Name] )

        elif iCmd == "skills":
            self._cmd_skills( [] )

        elif iCmd == "skill":
            _Name = q.text( "Skill 名稱（檔名或不含 .md）：" ).ask()
            if _Name:
                self._cmd_skill( [_Name] )

        elif iCmd == "tasks":
            self._cmd_tasks( [] )

        elif iCmd == "runtask":
            _TaskId = q.text( "任務 ID（用 tasks 查看可用 ID）：" ).ask()
            if _TaskId:
                self._cmd_runtask( [_TaskId] )

        elif iCmd == "exscript":
            _Sid  = q.text( "Session UUID：" ).ask()
            if not _Sid:
                return
            _Type = q.select(
                "腳本類型：",
                choices=[ "powershell", "python" ],
            ).ask()
            self._cmd_exscript( [_Sid, _Type or "powershell"] )

    #region 私有方法 — 選單輔助
    def _read_multiline( self ) -> str:
        """讀取多行輸入，連續兩個空行或 Ctrl+D 結束。"""
        _Lines: list = []
        _EmptyCount  = 0
        try:
            while True:
                _L = input()
                if _L == "":
                    _EmptyCount += 1
                    if _EmptyCount >= 2:
                        break
                    _Lines.append( _L )
                else:
                    _EmptyCount = 0
                    _Lines.append( _L )
        except EOFError:
            pass
        while _Lines and _Lines[-1] == "":
            _Lines.pop()
        return "\n".join( _Lines )

    def _pick_org( self, q ) -> Optional[str]:
        """列出所有組織讓使用者選擇。"""
        import os
        _WsRoot = os.path.join( self.m_Config.vault_path, self.m_Config.paths.workspaces )
        if not os.path.isdir( _WsRoot ):
            print( "（找不到 workspaces 目錄）" )
            return None
        _Orgs = sorted( o for o in os.listdir( _WsRoot )
                        if not o.startswith( "_" ) and os.path.isdir( os.path.join( _WsRoot, o ) ) )
        if not _Orgs:
            print( "（尚無組織）" )
            return None
        return q.select( "選擇組織：", choices=_Orgs ).ask()

    def _pick_project( self, q, iOrg: str ) -> Optional[str]:
        """列出指定組織下的所有專案讓使用者選擇。"""
        import os
        _P       = self.m_Config.paths
        _ProjDir = os.path.join( self.m_Config.vault_path, _P.workspaces, iOrg, _P.org_projects )
        if not os.path.isdir( _ProjDir ):
            print( "（尚無專案）" )
            return None
        _Projs = sorted( p for p in os.listdir( _ProjDir )
                         if os.path.isdir( os.path.join( _ProjDir, p ) ) )
        if not _Projs:
            print( "（尚無專案）" )
            return None
        return q.select( "選擇專案：", choices=_Projs ).ask()

    def _pick_project_file( self, q, iOrg: str, iProject: str ) -> Optional[str]:
        """列出專案內常用檔案讓使用者選擇，回傳相對 Vault 路徑。"""
        import os, questionary as _q
        _P        = self.m_Config.paths
        _ProjRoot = os.path.join( self.m_Config.vault_path, _P.workspaces, iOrg, _P.org_projects, iProject )
        _RelBase  = f"{_P.workspaces}/{iOrg}/{_P.org_projects}/{iProject}"
        _Choices  = []

        if os.path.isfile( os.path.join( _ProjRoot, "status.md" ) ):
            _Choices.append( _q.Choice( "📋  status.md", value=f"{_RelBase}/status.md" ) )

        _DailyDir = os.path.join( _ProjRoot, "daily" )
        if os.path.isdir( _DailyDir ):
            for _F in list( reversed( sorted( f for f in os.listdir( _DailyDir ) if f.endswith( ".md" ) ) ) )[:5]:
                _Choices.append( _q.Choice( f"📅  daily/{_F}", value=f"{_RelBase}/daily/{_F}" ) )

        _NotesDir = os.path.join( _ProjRoot, "notes" )
        if os.path.isdir( _NotesDir ):
            for _F in sorted( f for f in os.listdir( _NotesDir ) if f.endswith( ".md" ) ):
                _Choices.append( _q.Choice( f"📝  notes/{_F}", value=f"{_RelBase}/notes/{_F}" ) )

        _Choices.append( _q.Choice( "⌨️   手動輸入路徑", value="_custom" ) )
        _Sel = q.select( "選擇檔案：", choices=_Choices ).ask()
        if _Sel == "_custom":
            return q.text( "輸入完整相對路徑：" ).ask()
        return _Sel

    def _pick_top_folder( self, q, title: str = "選擇位置：", allow_skip: bool = False ) -> Optional[str]:
        """列出 Vault 頂層資料夾讓使用者選擇。"""
        import os, questionary as _q
        _Root    = self.m_Config.vault_path
        _Icons   = { "workspaces": "🗂️ ", "knowledge": "💡", "personal": "👤",
                     "templates": "📐", "_config": "⚙️ ", "attachments": "📎" }
        _Choices = [
            _q.Choice( f"{_Icons.get( d, '📁')}  {d}/", value=d )
            for d in sorted( os.listdir( _Root ) )
            if os.path.isdir( os.path.join( _Root, d ) ) and not d.startswith( "." )
        ]
        if allow_skip:
            _Choices.insert( 0, _q.Choice( "🔍  全庫搜尋（不限範圍）", value="" ) )
        return q.select( title, choices=_Choices ).ask()

    def _pick_vault_path( self, q ) -> Optional[str]:
        """兩段式路徑選擇：先選頂層資料夾，再依類型導引。"""
        import os, questionary as _q
        _Top = self._pick_top_folder( q )
        if _Top is None:
            return None

        if _Top == "workspaces":
            _Org = self._pick_org( q )
            if not _Org:
                return None
            _Proj = self._pick_project( q, _Org )
            if not _Proj:
                return None
            return self._pick_project_file( q, _Org, _Proj )

        # 其他頂層目錄：列出第一層 .md 檔
        _SubRoot  = os.path.join( self.m_Config.vault_path, _Top )
        _MdFiles  = sorted( f for f in os.listdir( _SubRoot ) if f.endswith( ".md" ) )
        _Choices  = [ _q.Choice( f, value=f"{_Top}/{f}" ) for f in _MdFiles ]
        _Choices.append( _q.Choice( "⌨️   手動輸入子路徑", value="_custom" ) )
        _Sel = q.select( "選擇檔案：", choices=_Choices ).ask()
        if _Sel == "_custom":
            return q.text( "輸入路徑：", default=f"{_Top}/" ).ask()
        return _Sel
    #endregion

    #region 私有方法 — 指令分發
    def _build_help( self ) -> str:
        """根據 TOOL_REGISTRY 全自動建立 help 文字（每次 __init__ 呼叫一次）。"""
        _GroupLabels = {
            "files":     "檔案操作",
            "projects":  "專案管理",
            "reviews":   "進度表",
            "ai":        "AI 對話",
            "other":     "維護工具",
            "instincts": "直覺記憶",
            "agents":    "Agent / Skill",
            "scheduler": "排程",
        }
        _Lines = [
            "",
            "╔══════════════════════════════════════════════════════════╗",
            "║        AI Memory Vault v3 — CLI 指令列表                ║",
            "╠══════════════════════════════════════════════════════════╣",
        ]
        _CurGroup = ""
        for _T in TOOL_REGISTRY:
            if _T.group != _CurGroup:
                _CurGroup = _T.group
                _Label = _GroupLabels.get( _CurGroup, _CurGroup )
                _Lines.append( "╠══════════════════════════════════════════════════════════╣" )
                _Lines.append( f"║  [{_Label}]" )
            _Lines.append( f"║  {_T.help_line}" )
        _Lines += [
            "╠══════════════════════════════════════════════════════════╣",
            "║  help  /  q / exit                                       ║",
            "╠══════════════════════════════════════════════════════════╣",
        ]
        _AliasStr = "  ".join( f"{t.alias}={t.name}" for t in TOOL_REGISTRY )
        _Lines.append( f"║  別名：{_AliasStr}" )
        _Lines.append( "╚══════════════════════════════════════════════════════════╝" )
        _Lines.append( "" )
        return "\n".join( _Lines )

    def _collect_params( self, q, iEntry ) -> Optional[dict]:
        """選單模式：依 ToolEntry.params 逐一用 questionary 收集參數。
        若使用者取消必填項目，回傳 None。"""
        _Kwargs: dict = {}
        for _P in iEntry.params:
            if _P.kind == "org":
                _Val = self._pick_org( q )
            elif _P.kind == "project":
                _Val = self._pick_project( q, _Kwargs.get( "org", "" ) )
            elif _P.kind == "date":
                _Val = q.text( _P.prompt, default="" ).ask() or None
            elif _P.kind == "session":
                _Val = q.text( _P.prompt ).ask()
            elif _P.kind == "multiline":
                print( _P.prompt )
                _Lines: list = []
                while True:
                    try:
                        _L = input()
                    except EOFError:
                        break
                    if _L == "":
                        break
                    _Lines.append( _L )
                _Val = "\n".join( _Lines )
            else:  # "text"
                _Val = q.text( _P.prompt ).ask()

            if _Val is None and _P.required:
                return None
            _Kwargs[_P.name] = _Val
        return _Kwargs

    def _run_registry( self, iEntry, iArgs: list ) -> None:
        """REPL 模式：將 positional args 依序映射到 ToolEntry.params 後呼叫 invoke。"""
        from services.vault import VaultService
        _Kwargs: dict = {}
        _AI = 0   # positional arg 索引

        for _P in iEntry.params:
            if _P.kind == "multiline":
                # 剩餘所有 args 合併為內容；若無 args 則互動讀取
                if _AI < len( iArgs ):
                    _Kwargs[_P.name] = "\n".join( iArgs[_AI:] )
                    _AI = len( iArgs )
                else:
                    print( "輸入對話內容（空行結束）：" )
                    _MLines: list = []
                    while True:
                        try:
                            _L = input()
                        except EOFError:
                            break
                        if _L == "":
                            break
                        _MLines.append( _L )
                    _Kwargs[_P.name] = "\n".join( _MLines )

            elif _P.kind == "date":
                # 日期為可選；若有 arg 且符合格式就取用
                _Val = iArgs[_AI] if _AI < len( iArgs ) else None
                _Kwargs[_P.name] = _Val
                if _Val is not None:
                    _AI += 1

            else:
                # org / project / session / text — 取下一個 positional arg
                if _AI < len( iArgs ):
                    _Kwargs[_P.name] = iArgs[_AI]; _AI += 1
                elif _P.required:
                    _Usage = " ".join(
                        f"<{p.name}>" if p.required else f"[<{p.name}>]"
                        for p in iEntry.params
                    )
                    print( f"用法：{iEntry.name} {_Usage}" )
                    return
                else:
                    _Kwargs[_P.name] = _P.default or None

        _Result = iEntry.invoke( self.m_Sched, VaultService, **_Kwargs )
        if isinstance( _Result, str ):
            print( f"✅ {_Result}" )

    ## <summary>手動指令到 _cmd_* 方法名的映射（invoke=None 的 registry 工具）</summary>
    _CMD_MAP: dict = {
        "search":     "_cmd_search",
        "read":       "_cmd_read",
        "write":      "_cmd_write",
        "delete":     "_cmd_delete",
        "rename":     "_cmd_rename",
        "list":       "_cmd_list",
        "sync":       "_cmd_sync",
        "batchwrite": "_cmd_batchwrite",
        "status":     "_cmd_status",
        "todo":       "_cmd_todo",
        "projects":   "_cmd_projects",
        "integrity":  "_cmd_integrity",
        "clean":      "_cmd_clean_orphans",
        "checkindex": "_cmd_checkindex",
        "reindex":    "_cmd_reindex",
        "edit":       "_cmd_edit",
        "grep":       "_cmd_grep",
        "backup":     "_cmd_backup",
        "addtodo":    "_cmd_addtodo",
        "rmtodo":     "_cmd_rmtodo",
        "instincts":  "_cmd_instincts",
        "sinst":      "_cmd_sinst",
        "newinst":    "_cmd_newinst",
        "updinst":    "_cmd_updinst",
        "retro":      "_cmd_retro",
        "agents":     "_cmd_agents",
        "dispatch":   "_cmd_dispatch",
        "skills":     "_cmd_skills",
        "skill":      "_cmd_skill",
        "tasks":      "_cmd_tasks",
        "runtask":    "_cmd_runtask",
        "exscript":   "_cmd_exscript",
    }

    def _dispatch( self, iLine: str ) -> None:
        """解析並執行一行指令（支援短別名）。"""
        _Parts = iLine.split()
        _Raw   = _Parts[0].lower()
        _Cmd   = self._ALIASES.get( _Raw, _Raw )   # 展開別名
        _Args  = _Parts[1:]

        # help 特殊處理
        if _Cmd == "help":
            print( self._HELP )
            return

        # Registry 查找
        _Entry = REGISTRY_BY_NAME.get( _Cmd )
        if not _Entry:
            print( f"❓ 未知指令：{_Cmd}（輸入 'help' 查看可用指令）" )
            return

        try:
            if _Entry.invoke is not None:
                # 自動分發（positional args → params → invoke()）
                self._run_registry( _Entry, _Args )
            else:
                # 手動工具（_cmd_* 方法）
                _MethodName = self._CMD_MAP.get( _Cmd )
                if _MethodName:
                    getattr( self, _MethodName )( _Args )
                else:
                    print( f"❌ {_Cmd} 尚無對應的 _cmd_* 實作" )
        except Exception as _Ex:
            print( f"❌ 執行失敗：{_Ex}" )

    def _cmd_search( self, iArgs: list ) -> None:
        """search <query> [--cat C] [--type T] [--mode M]"""
        if not iArgs:
            print( "用法：search <query> [--cat <category>] [--type <doc_type>] [--mode keyword|semantic]" )
            return

        _Query, _Cat, _DocType, _Mode = "", "", "", ""
        _QueryParts = []
        _I = 0
        while _I < len( iArgs ):
            if iArgs[_I] == "--cat" and _I + 1 < len( iArgs ):
                _Cat = iArgs[_I + 1]; _I += 2
            elif iArgs[_I] == "--type" and _I + 1 < len( iArgs ):
                _DocType = iArgs[_I + 1]; _I += 2
            elif iArgs[_I] == "--mode" and _I + 1 < len( iArgs ):
                _Mode = iArgs[_I + 1]; _I += 2
            else:
                _QueryParts.append( iArgs[_I] ); _I += 1
        _Query = " ".join( _QueryParts )

        if not _Query:
            print( "❌ 請提供搜尋關鍵字" )
            return

        from services.vault import VaultService
        _Result = VaultService.search_formatted( _Query, _Cat, _DocType, _Mode )
        print( "\n" + ( _Result or "記憶庫中找不到相關資料。" ) + "\n" )

    def _cmd_read( self, iArgs: list ) -> None:
        """read <path>"""
        if not iArgs:
            print( "用法：read <path>" )
            return
        from services.vault import VaultService
        _Content, _Err = VaultService.read_note( iArgs[0] )
        if _Err:
            print( f"❌ {_Err}" )
        else:
            print( "\n" + _Content + "\n" )

    def _cmd_write( self, iArgs: list ) -> None:
        """write <path>  — 多行輸入，空行兩次或 Ctrl+D 結束"""
        if not iArgs:
            print( "用法：write <path>" )
            return
        _Path = iArgs[0]
        print( f"✏️  寫入 {_Path}（輸入內容，連續兩個空行或 Ctrl+D 結束）：" )
        _Content = self._read_multiline()
        if not _Content:
            print( "⚠️  內容為空，取消寫入。" )
            return

        from services.vault import VaultService
        _Stats, _Err = VaultService.write_note( _Path, _Content )
        if _Err:
            print( f"❌ {_Err}" )
        else:
            print( f"✅ 已寫入：{_Path}（{_Stats.get('chars', 0)} 字元，{_Stats.get('total_chunks', 0)} chunks）" )

    def _cmd_delete( self, iArgs: list ) -> None:
        """delete <path>"""
        if not iArgs:
            print( "用法：delete <path>" )
            return
        _Path = iArgs[0]
        _Confirm = input( f"⚠️  確認刪除 {_Path}？（y/N）: " ).strip().lower()
        if _Confirm != "y":
            print( "取消。" )
            return
        from services.vault import VaultService
        _Stats, _Err = VaultService.delete_note( _Path )
        if _Err:
            print( f"❌ {_Err}" )
        else:
            print( f"✅ 已刪除：{_Path}（移除 {_Stats.get('deleted_chunks', 0)} 個向量）" )

    def _cmd_rename( self, iArgs: list ) -> None:
        """rename <old_path> <new_path>"""
        if len( iArgs ) < 2:
            print( "用法：rename <old_path> <new_path>  （別名：mv）" )
            return
        _OldPath, _NewPath = iArgs[0], iArgs[1]
        if _OldPath == _NewPath:
            print( "⚠️  來源與目的地相同，無需操作。" )
            return
        from services.vault import VaultService
        _Stats, _Err = VaultService.rename_note( _OldPath, _NewPath )
        if _Err:
            print( f"❌ {_Err}" )
        else:
            print(
                f"✅ 已移動：{_Stats['old_path']} → {_Stats['new_path']}\n"
                f"   移除 {_Stats['deleted_chunks']} 舊 chunks，索引 {_Stats['indexed_chunks']} 新 chunks。"
            )

    def _cmd_list( self, iArgs: list ) -> None:
        """list [<path>] [-r]  — 列出目錄下所有 .md 檔案（-r 遞迴）"""
        import datetime
        _Path      = ""
        _Recursive = False
        for _A in iArgs:
            if _A == "-r":
                _Recursive = True
            elif not _Path:
                _Path = _A

        from services.vault import VaultService
        _Result, _Err = VaultService.list_notes( _Path, _Recursive )
        if _Err:
            print( f"❌ {_Err}" )
            return
        _Total = _Result["total"]
        _Label = _Result["path"]
        _Rec   = "（遞迴）" if _Recursive else ""
        if _Total == 0:
            print( f"📂 {_Label}{_Rec}：無 .md 檔案。" )
            return
        print( f"📂 {_Label}{_Rec}  — {_Total} 個 .md 檔案\n" )
        for _N in _Result["notes"]:
            _Dt = datetime.datetime.fromtimestamp( _N["modified"] ).strftime( "%Y-%m-%d" )
            _Kb = f"{_N['size'] / 1024:.1f}KB" if _N["size"] >= 1024 else f"{_N['size']}B"
            print( f"  {_Dt}  {_Kb:>8}  {_N['path']}" )

    def _cmd_sync( self, iArgs: list ) -> None:
        """sync"""
        from services.vault import VaultService
        print( "🔄 同步中...", end="", flush=True )
        _Stats = VaultService.sync()
        _IS = _Stats["index_stats"]
        print(
            f"\r✅ 同步完成：{_Stats['total_files']} 檔 / {_Stats['total_chunks']} chunks"
            f"  Added={_IS['num_added']} Updated={_IS['num_updated']} Deleted={_IS['num_deleted']}"
        )

    def _cmd_status( self, iArgs: list ) -> None:
        """status <org> <project>"""
        if len( iArgs ) < 2:
            print( "用法：status <org> <project>" )
            return
        from services.vault import VaultService
        _Data, _Err = VaultService.get_project_status( iArgs[0], iArgs[1] )
        if _Err:
            print( f"❌ {_Err}" )
            return
        print( f"\n📋 {iArgs[0]}/{iArgs[1]}  (更新：{_Data['last_updated']})" )
        print( f"   待辦（{len(_Data['pending_todos'])} 項）：" )
        for _T in _Data["pending_todos"]:
            print( f"     - [ ] {_T}" )
        print( f"   已完成：{_Data['completed_count']} 項" )
        if _Data.get( "context_summary" ):
            _Lines = _Data["context_summary"].splitlines()[:3]
            print( "   工作脈絡：" + " / ".join( _L.strip() for _L in _Lines if _L.strip() ) )
        print()

    def _cmd_todo( self, iArgs: list ) -> None:
        """todo <path> <text> [done|undone]"""
        if len( iArgs ) < 2:
            print( "用法：todo <path> <text> [done|undone]" )
            return
        _Path  = iArgs[0]
        _State = iArgs[-1].lower() if iArgs[-1].lower() in ( "done", "undone" ) else "done"
        _Text  = " ".join( iArgs[1:] if _State not in iArgs[-1].lower() else iArgs[1:-1] )
        _Done  = ( _State == "done" )

        from services.vault import VaultService
        _Stats, _Err = VaultService.update_todo( _Path, _Text, _Done )
        if _Err:
            print( f"❌ {_Err}" )
        elif not _Stats or not _Stats.get( "matched" ):
            print( "⚠️  找不到符合的 todo 項目。" )
        else:
            _Mark = "[x]" if _Done else "[ ]"
            print( f"✅ {_Mark} {_Text}" )

    def _cmd_projects( self, iArgs: list ) -> None:
        """projects"""
        import os
        _P       = self.m_Config.paths
        _WsRoot  = os.path.join( self.m_Config.vault_path, _P.workspaces )
        if not os.path.isdir( _WsRoot ):
            print( "（workspaces 目錄不存在）" )
            return
        _Lines   = []
        for _Org in sorted( os.listdir( _WsRoot ) ):
            if _Org.startswith( "_" ):
                continue
            _ProjDir = os.path.join( _WsRoot, _Org, _P.org_projects )
            if not os.path.isdir( _ProjDir ):
                continue
            for _Proj in sorted( os.listdir( _ProjDir ) ):
                if os.path.isdir( os.path.join( _ProjDir, _Proj ) ):
                    _Lines.append( f"  {_Org} / {_Proj}" )
        if _Lines:
            print( "\n".join( _Lines ) )
        else:
            print( "（尚無專案）" )

    def _cmd_integrity( self, iArgs: list ) -> None:
        """integrity"""
        from services.vault import VaultService
        _Result, _Err = VaultService.check_integrity()
        if _Err:
            print( f"❌ {_Err}" )
            return
        _Orphaned = _Result.get( "orphaned", [] )
        print(
            f"✅ 完整性檢查：{_Result['total_files']} 個 .md 檔 / "
            f"{_Result['total_db_sources']} 個 DB 來源 / "
            f"{len( _Orphaned )} 個孤立向量"
        )
        if _Orphaned:
            print( "  孤立向量（僅在 DB，無對應 .md）：" )
            for _S in _Orphaned[:10]:
                print( f"    {_S}" )
            if len( _Orphaned ) > 10:
                print( f"    ... 及 {len( _Orphaned ) - 10} 筆更多" )
            print( "   輸入 'clean' 或 'cl' 清除孤立向量。" )

    def _cmd_clean_orphans( self, iArgs: list ) -> None:
        """clean — 清除 ChromaDB 中的孤立向量記錄"""
        from services.vault import VaultService

        # 先檢查，确認有孤立向量後再向使用者確認
        _Integrity, _Err = VaultService.check_integrity()
        if _Err:
            print( f"❌ 檢查失敗：{_Err}" )
            return

        _Orphaned = _Integrity.get( "orphaned", [] )
        if not _Orphaned:
            print( "✅ DB 已整潔，無孤立向量。" )
            return

        print( f"⚠️  找到 {len( _Orphaned )} 個孤立來源（對應 .md 已删除）：" )
        for _S in _Orphaned[:5]:
            print( f"    {_S}" )
        if len( _Orphaned ) > 5:
            print( f"    ... 及 {len( _Orphaned ) - 5} 筆更多" )

        _Confirm = input( "   確認清除？ [yes/N] " ).strip().lower()
        if _Confirm != "yes":
            print( "❌ 已取消。" )
            return

        _Result, _ClErr = VaultService.clean_orphans()
        if _ClErr:
            print( f"❌ 清除失敗：{_ClErr}" )
            return
        print( f"✅ 已清除 {_Result['removed']} 個孤立向量，來自 {len( _Result['orphaned_sources'] )} 個來源。" )

    def _cmd_checkindex( self, iArgs: list ) -> None:
        """checkindex — 檢查向量索引是否因設定變更需重建"""
        from config import ConfigManager
        from core.migration import MigrationManager
        _Config = ConfigManager.load()
        _NeedsReindex, _Changes = MigrationManager.check( _Config )
        if not _NeedsReindex:
            print( "✅ 向量索引狀態：正常（設定未變更，無需重建）" )
            return
        print( "⚠️  向量索引需要重建，以下設定已變更：" )
        print( MigrationManager.describe_changes( _Changes ) )
        print( "   請輸入 'reindex' 或 'ri' 重建索引。" )

    def _cmd_reindex( self, iArgs: list ) -> None:
        """reindex — 清除並重建 ChromaDB 向量索引"""
        print( "⚠️  即將清除向量索引並完整重建，此操作不可逆。" )
        _Confirm = input( "   確認重建？ [yes/N] " ).strip().lower()
        if _Confirm != "yes":
            print( "❌ 已取消。" )
            return

        from config import ConfigManager
        from core.migration import MigrationManager
        from services.vault import VaultService

        print( "🔄 正在清除索引..." )
        _Config = ConfigManager.load()
        _Ok, _Msg = MigrationManager.reset_index( _Config )
        if not _Ok:
            print( f"❌ 清除失敗：{_Msg}" )
            return

        print( "🔄 正在重建索引..." )
        _Stats = VaultService.sync()
        print(
            f"✅ 重建完成：{_Stats['total_chunks']} chunks / "
            f"{_Stats['total_files']} 個 .md 檔 / "
            f"新增 {_Stats['index_stats']['num_added']} 筆"
        )

    def _cmd_edit( self, iArgs: list ) -> None:
        """edit <path>  — 精確文字替換（多行輸入）"""
        if not iArgs:
            print( "用法：edit <path>" )
            return
        _Path = iArgs[0]
        print( f"✍️  編輯 {_Path}" )
        print( "--- 輸入要替換的文字（連續兩個空行結束）---" )
        _OldText = self._read_multiline()
        if not _OldText:
            print( "⚠️  舊文字為空，取消。" )
            return
        print( "--- 輸入替換後的文字（連續兩個空行結束）---" )
        _NewText = self._read_multiline()
        from services.vault import VaultService
        _Stats, _Err = VaultService.edit_note( _Path, _OldText, _NewText )
        if _Err:
            print( f"❌ {_Err}" )
        else:
            print(
                f"✅ 已編輯：{_Path}"
                f"（移除 {_Stats.get('chars_removed', 0)} 字元，新增 {_Stats.get('chars_added', 0)} 字元，"
                f"{_Stats.get('total_chunks', 0)} chunks）"
            )

    def _cmd_grep( self, iArgs: list ) -> None:
        """grep <pattern> [<path>] [-r]  — 精確文字 / regex 搜尋"""
        if not iArgs:
            print( "用法：grep <pattern> [<path>] [-r]" )
            return
        _IsRegex = "-r" in iArgs
        _RestArgs = [ a for a in iArgs if a != "-r" ]
        _Pattern = _RestArgs[0]
        _Path    = _RestArgs[1] if len( _RestArgs ) > 1 else ""
        from services.vault import VaultService
        _Results, _Err = VaultService.grep( _Pattern, _Path, _IsRegex )
        if _Err:
            print( f"❌ {_Err}" )
            return
        if not _Results:
            _Scope = _Path or "/"
            print( f"找不到符合 '{_Pattern}' 的結果（範圍：{_Scope}）" )
            return
        print( f"找到 {len( _Results )} 筆：\n" )
        for _R in _Results:
            print( f"  {_R['file']}:{_R['line']}:{_R['col']}  {_R['text']}" )

    def _cmd_backup( self, iArgs: list ) -> None:
        """backup — 立即備份 ChromaDB"""
        from config import ConfigManager
        from services.backup import BackupService
        print( "💾 備份中...", end="", flush=True )
        _Config = ConfigManager.load()
        _Svc    = BackupService( _Config )
        _Path, _Err = _Svc.backup_chromadb()
        if _Err:
            print( f"\r❌ 備份失敗：{_Err}" )
            return
        _Cleaned = _Svc.cleanup()
        _Backups = _Svc.list_backups()
        print( f"\r✅ 備份完成：{_Path}" )
        print( f"   清除 {_Cleaned} 份舊備份，目前保留 {len( _Backups )} 份" )
        if _Backups:
            print( "   現有備份：" )
            for _B in _Backups:
                print( f"     - {_B['name']}（{_B['size_mb']:.1f} MB）" )

    def _cmd_addtodo( self, iArgs: list ) -> None:
        """addtodo <path> <text> [<section>]  — 新增 todo 項目"""
        if len( iArgs ) < 2:
            print( "用法：addtodo <path> <text> [<section>]" )
            return
        _Path    = iArgs[0]
        _Section = iArgs[-1] if len( iArgs ) > 2 else ""
        _Text    = " ".join( iArgs[1:] if not _Section else iArgs[1:-1] )
        # 若 section 看起來像 todo 文字（無 ## 前綴），清空
        if _Section and not _Section.startswith( "##" ) and len( iArgs ) == 2:
            _Section = ""
        from services.vault import VaultService
        _Stats, _Err = VaultService.add_todo( _Path, _Text, _Section or None )
        if _Err:
            print( f"❌ {_Err}" )
        else:
            print( f"✅ 已新增：- [ ] {_Text}" )

    def _cmd_rmtodo( self, iArgs: list ) -> None:
        """rmtodo <path> <text>  — 移除 todo 項目（整行刪除）"""
        if len( iArgs ) < 2:
            print( "用法：rmtodo <path> <text>" )
            return
        _Path = iArgs[0]
        _Text = " ".join( iArgs[1:] )
        _Confirm = input( f"⚠️  確認移除 todo「{_Text}」？（y/N）: " ).strip().lower()
        if _Confirm != "y":
            print( "取消。" )
            return
        from services.vault import VaultService
        _Stats, _Err = VaultService.remove_todo( _Path, _Text )
        if _Err:
            print( f"❌ {_Err}" )
        else:
            print( f"✅ 已移除：{_Stats.get( 'removed_line', _Text )}" )

    def _get_instinct_service( self ):
        """取得 InstinctService 單例。"""
        from config import ConfigManager
        from services.instinct import InstinctService
        _Config = ConfigManager.load()
        return InstinctService( _Config )

    def _cmd_instincts( self, iArgs: list ) -> None:
        """instincts [<domain>]  — 列出所有直覺卡片"""
        _Domain = iArgs[0] if iArgs else ""
        _Svc     = self._get_instinct_service()
        _Results = _Svc.list_all( iDomain=_Domain )
        if not _Results:
            print( "目前沒有直覺卡片。" )
            return

        _Sorted = sorted( _Results, key=lambda x: float( x.get( "confidence", 0 ) ), reverse=True )
        _Cfg    = _Svc._load_config()
        _Thresh = _Cfg["instincts"]["auto_apply_threshold"]

        print( f"\n共 {len( _Sorted )} 張直覺卡片（自動套用閾值：{_Thresh}）\n" )
        print( f"  {'ID':<35} {'信心':>4}  {'Domain':<14} {'建立日':<12} 狀態" )
        print( "  " + "─" * 80 )
        for _R in _Sorted:
            _Conf   = float( _R.get( "confidence", 0 ) )
            _Status = "🟢 自動" if _Conf >= _Thresh else "🟡 參考"
            print(
                f"  {_R.get( 'id', '' ):<35} {_Conf:>4.1f}  "
                f"{_R.get( 'domain', '' ):<14} {_R.get( 'created', '' ):<12} {_Status}"
            )
        print()

    def _cmd_sinst( self, iArgs: list ) -> None:
        """sinst <query> [<domain>]  — 語意搜尋直覺卡片"""
        if not iArgs:
            print( "用法：sinst <query> [<domain>]" )
            return
        _Query  = iArgs[0]
        _Domain = iArgs[1] if len( iArgs ) > 1 else ""
        _Svc     = self._get_instinct_service()
        _Results = _Svc.search( iQuery=_Query, iDomain=_Domain )
        if not _Results:
            print( f"找不到符合「{_Query}」的直覺卡片。" )
            return
        print( f"\n找到 {len( _Results )} 張直覺卡片：\n" )
        for _R in _Results:
            print(
                f"  🧠 {_R.get( 'id', '?' )}（{_R.get( 'domain', '?' )}，"
                f"信心 {_R.get( 'confidence', '?' )}）"
            )
            print( f"     觸發：{_R.get( 'trigger', '' )[:100]}" )
            _Snippet = _R.get( "snippet", "" )[:150]
            if _Snippet:
                print( f"     摘要：{_Snippet}" )
            print()

    def _cmd_newinst( self, iArgs: list ) -> None:
        """newinst — 互動式建立直覺卡片"""
        print( "➕ 建立直覺卡片\n" )
        _Id      = input( "  ID（slug 格式，如 debug-one-change）：" ).strip()
        if not _Id:
            print( "⚠️  ID 不可為空。" )
            return
        _Title   = input( "  標題：" ).strip()
        if not _Title:
            print( "⚠️  標題不可為空。" )
            return
        _Trigger = input( "  觸發條件（什麼情境下想起這條）：" ).strip()
        if not _Trigger:
            print( "⚠️  觸發條件不可為空。" )
            return
        _Domain  = input( "  Domain（debugging/workflow/csharp/lua/python/architecture）：" ).strip()
        if not _Domain:
            print( "⚠️  Domain 不可為空。" )
            return
        _Action  = input( "  遇到觸發條件時該怎麼做：" ).strip()
        if not _Action:
            print( "⚠️  Action 不可為空。" )
            return
        _Pattern    = input( "  正確模式範例（留空跳過，連續兩空行結束）：" ).strip()
        if _Pattern:
            print( "  （繼續輸入，連續兩空行結束）" )
            _Pattern += "\n" + self._read_multiline()
        _Evidence   = input( "  證據（留空跳過）：" ).strip()
        _Reflection = input( "  錯誤反思（留空跳過）：" ).strip()
        _ConfStr    = input( "  初始信心度（0.0~1.0，留空=0.6）：" ).strip()
        _Confidence = float( _ConfStr ) if _ConfStr else 0.0

        _Svc  = self._get_instinct_service()
        _Path = _Svc.create(
            iId=_Id, iTrigger=_Trigger, iDomain=_Domain, iTitle=_Title,
            iAction=_Action, iCorrectPattern=_Pattern,
            iEvidence=_Evidence, iReflection=_Reflection,
            iConfidence=_Confidence,
        )
        print( f"\n✅ 直覺卡片已建立：{_Path}" )

    def _cmd_updinst( self, iArgs: list ) -> None:
        """updinst <id> <delta> [<evidence>]  — 更新信心度"""
        if len( iArgs ) < 2:
            print( "用法：updinst <id> <delta> [<evidence>]" )
            return
        _Id    = iArgs[0]
        try:
            _Delta = float( iArgs[1] )
        except ValueError:
            print( f"❌ delta 必須是數字（如 +0.1），收到：{iArgs[1]}" )
            return
        _Evid  = " ".join( iArgs[2:] ) if len( iArgs ) > 2 else ""
        _Svc   = self._get_instinct_service()
        _Meta  = _Svc.update( iId=_Id, iConfidenceDelta=_Delta, iNewEvidence=_Evid )
        print( f"✅ 已更新 {_Id}（信心度 → {_Meta.get( 'confidence', '?' )}）" )

    def _cmd_retro( self, iArgs: list ) -> None:
        """retro [<YYYY-MM>]  — 生成月度復盤報告"""
        _Month = iArgs[0] if iArgs else ""
        _Svc   = self._get_instinct_service()
        print( "📊 生成復盤報告中...", end="", flush=True )
        _Path  = _Svc.generate_retrospective( iMonth=_Month )
        print( f"\r✅ 月度復盤報告已生成：{_Path}" )

    def _cmd_agents( self, iArgs: list ) -> None:
        """agents — 列出所有 Agent 模板"""
        from config import ConfigManager
        from services.agent_router import AgentRouter
        _Config = ConfigManager.load()
        _Router = AgentRouter( _Config.vault_path )
        _Agents = _Router.list_agents()
        if not _Agents:
            print( "Vault 中沒有任何 Agent 模板。" )
            return
        print( f"\n共 {len( _Agents )} 個 Agent：\n" )
        print( f"  {'觸發指令':<20} {'領域':<16} 說明" )
        print( "  " + "─" * 60 )
        for _A in _Agents:
            print( f"  {_A['trigger']:<20} {_A['domain']:<16} {_A['summary']}" )
        print()

    def _cmd_dispatch( self, iArgs: list ) -> None:
        """dispatch <agent> — 載入 Agent 完整指令"""
        if not iArgs:
            print( "用法：dispatch <agent>（名稱 / @觸發指令 / 領域）" )
            return
        from config import ConfigManager
        from services.agent_router import AgentRouter
        _Config = ConfigManager.load()
        _Router = AgentRouter( _Config.vault_path )
        _Query  = " ".join( iArgs )
        _Tpl    = _Router.resolve( _Query )
        if not _Tpl:
            _Available = _Router.list_agents()
            _Names = ", ".join( _A["trigger"] for _A in _Available )
            print( f"❌ 找不到 Agent '{_Query}'。可用：{_Names}" )
            return
        print( f"\n# {_Tpl.name} Agent" )
        print( f"  領域：{_Tpl.domain}" )
        print( f"  觸發：{_Tpl.trigger}" )
        print( f"  工具：{', '.join( _Tpl.mcp_tools )}" )
        if _Tpl.related_rules:
            print( f"  規則：{', '.join( _Tpl.related_rules )}" )
        print( f"\n{_Tpl.body}\n" )

    def _cmd_batchwrite( self, iArgs: list ) -> None:
        """batchwrite <json> — 批次寫入筆記（JSON 檔案路徑）"""
        if not iArgs:
            print( "用法：batchwrite <json_file>" )
            print( "  JSON 格式：[{\"file_path\": \"...\", \"content\": \"...\", \"mode\": \"overwrite|append\"}, ...]" )
            return
        import json, os
        _JsonPath = iArgs[0]
        if not os.path.isfile( _JsonPath ):
            print( f"❌ 找不到檔案：{_JsonPath}" )
            return
        try:
            with open( _JsonPath, "r", encoding="utf-8" ) as _F:
                _Notes = json.load( _F )
        except ( json.JSONDecodeError, UnicodeDecodeError ) as _E:
            print( f"❌ JSON 解析失敗：{_E}" )
            return
        if not isinstance( _Notes, list ) or not _Notes:
            print( "❌ JSON 必須是非空陣列" )
            return
        for _N in _Notes:
            if not isinstance( _N, dict ) or "file_path" not in _N or "content" not in _N:
                print( "❌ 每筆必須含 file_path 和 content 欄位" )
                return

        print( f"📝 即將批次寫入 {len( _Notes )} 筆筆記：" )
        for _N in _Notes:
            _Mode = _N.get( "mode", "overwrite" )
            print( f"  {_N['file_path']}（{_Mode}）" )
        _Confirm = input( "  確認寫入？（y/N）: " ).strip().lower()
        if _Confirm != "y":
            print( "取消。" )
            return

        from services.vault import VaultService
        _Results, _BatchStats, _Err = VaultService.batch_write_notes( _Notes )
        if _Err:
            print( f"❌ {_Err}" )
            return
        _OkCount   = sum( 1 for _R in _Results if _R["ok"] )
        _FailCount = len( _Results ) - _OkCount
        _Added     = _BatchStats["index_stats"].get( "num_added", 0 )
        _Updated   = _BatchStats["index_stats"].get( "num_updated", 0 )
        print( f"\n✅ 批次寫入：{_OkCount} 成功，{_FailCount} 失敗" )
        print( f"   索引：{_BatchStats['total_chunks']} chunks（新增={_Added}，更新={_Updated}）" )
        for _R in _Results:
            if _R["ok"]:
                print( f"  ✅  {_R['file_path']}（{_R['chars']} 字元）" )
            else:
                print( f"  ❌  {_R['file_path']} — {_R['error']}" )

    def _cmd_skills( self, iArgs: list ) -> None:
        """skills — 列出所有 Skill 知識包"""
        import os
        from config import ConfigManager
        _Config   = ConfigManager.load()
        _SkillDir = os.path.join( _Config.vault_path, "workspaces", "_global", "skills" )
        if not os.path.isdir( _SkillDir ):
            print( "Skill 目錄不存在。" )
            return
        _Files = sorted(
            _F for _F in os.listdir( _SkillDir )
            if _F.endswith( ".md" ) and _F != "index.md"
        )
        if not _Files:
            print( "沒有任何 Skill 技能包。" )
            return
        print( f"\n可用技能包（{len( _Files )} 個）：\n" )
        for _F in _Files:
            _Abs = os.path.join( _SkillDir, _F )
            _Kb  = os.path.getsize( _Abs ) / 1024
            print( f"  {_F:<40} ({_Kb:.1f}KB)" )
        print()

    def _cmd_skill( self, iArgs: list ) -> None:
        """skill <name>  — 讀取 Skill 知識包完整內容"""
        if not iArgs:
            print( "用法：skill <name>" )
            return
        import os
        from config import ConfigManager
        _Config   = ConfigManager.load()
        _SkillDir = os.path.join( _Config.vault_path, "workspaces", "_global", "skills" )
        _Name     = iArgs[0]
        if not _Name.endswith( ".md" ):
            _Name += ".md"
        _Abs  = os.path.join( _SkillDir, _Name )
        _Real = os.path.realpath( _Abs )
        if not _Real.startswith( os.path.realpath( _SkillDir ) ):
            print( "❌ 路徑安全驗證失敗。" )
            return
        if not os.path.isfile( _Abs ):
            print( f"❌ 找不到 '{_Name}'（workspaces/_global/skills/）" )
            return
        with open( _Abs, "r", encoding="utf-8" ) as _F:
            print( "\n" + _F.read() + "\n" )

    def _cmd_tasks( self, iArgs: list ) -> None:
        """tasks — 列出所有排程任務"""
        from services.auto_scheduler import AutoScheduler
        _Tasks = AutoScheduler.list_tasks()
        if not _Tasks:
            print( "沒有排程任務。" )
            return
        print( f"\n共 {len( _Tasks )} 個排程任務：\n" )
        print( f"  {'ID':<18} {'名稱':<20} 排程" )
        print( "  " + "─" * 60 )
        for _T in _Tasks:
            print( f"  {_T['id']:<18} {_T['name']:<20} {_T['schedule']}" )
            print( f"  {'':>18} {_T['description']}" )
        print()

    def _cmd_runtask( self, iArgs: list ) -> None:
        """runtask <task_id>  — 手動觸發排程任務"""
        if not iArgs:
            print( "用法：runtask <task_id>（用 tasks 查看可用 ID）" )
            return
        _TaskId = iArgs[0]
        print( f"▶️  觸發排程任務 {_TaskId}...", end="", flush=True )
        from services.auto_scheduler import AutoScheduler
        _Auto    = AutoScheduler( self.m_Config )
        _Results = _Auto.run_task( _TaskId )
        print( "\r" + " " * 40 + "\r", end="" )
        for _Label, _Detail in _Results:
            print( f"  {_Label}: {_Detail}" )

    def _cmd_exscript( self, iArgs: list ) -> None:
        """exscript <session_id> [powershell|python]  — 提取 Session 腳本"""
        if not iArgs:
            print( "用法：exscript <session_id> [powershell|python]" )
            return
        _Sid  = iArgs[0]
        _Type = iArgs[1] if len( iArgs ) > 1 else "powershell"
        if _Type not in ( "powershell", "python" ):
            print( f"⚠️  不支援的腳本類型：{_Type}（支援 powershell / python）" )
            return

        from config import ConfigManager
        _Config = ConfigManager.load()
        if not _Config.vscode_chat_dir:
            print( "❌ config.json 未設定 vscode_chat_dir" )
            return

        from services.session_extractor import SessionExtractor
        _SE     = SessionExtractor( _Config.vscode_chat_dir, _Config.vault_path )
        _Script = _SE.extract_script( _Sid, _Type )
        if not _Script:
            print( f"Session {_Sid[:8]} 中無 terminal 指令可提取。" )
            return

        print( f"\n--- {_Type} 腳本（{_Sid[:8]}）---\n" )
        print( _Script )
        print( "\n--- 結束 ---" )

        _Save = input( "\n  儲存到 Vault？（y/N）: " ).strip().lower()
        if _Save == "y":
            from pathlib import Path
            _Ext = ".ps1" if _Type == "powershell" else ".py"
            _Dir = Path( _Config.vault_path ) / "scripts"
            _Dir.mkdir( parents=True, exist_ok=True )
            _File = _Dir / f"extracted-{_Sid[:8]}{_Ext}"
            _File.write_text( _Script, encoding="utf-8" )
            print( f"✅ 已儲存：{_File}" )

    #endregion
