"""
CLI 互動介面 (v3)
直接呼叫 VaultService / SchedulerService，對應全部 18 個 MCP 工具功能。
不依賴 LLM — 純工具操作介面，啟動快速、離線可用。

指令清單：
  search <query> [--cat <category>] [--type <doc_type>] [--mode keyword|semantic]
  read <path>
  write <path>
  delete <path>
  sync
  status <org> <project>          讀取專案狀態 (get_project_status)
  todo <path> <text> [done|undone]
  daily <org> <project> [<date>]   生成專案每日進度
  review [<date>]                  生成每日總進度表 (generate_daily_review)
  weekly                           生成每週總進度表
  monthly                          生成每月總進度表
  genstatus <org> <project>        生成專案 status.md 模板 (generate_project_status)
  log <org> <project> <session>    記錄 AI 對話 (log_ai_conversation)
  aiweekly [<date>]                生成 AI 對話週報
  aimonthly [<date>]               生成 AI 對話月報
  projects                         列出所有組織與專案
  integrity                        檢查 ChromaDB 向量完整性
  clean                            清除孤立向量記錄（對應 .md 已刪除）  rename <old_path> <new_path>     移動或重命名 .md 檔案並同步向量索引  checkindex                       檢查向量索引是否因設定變更需重建
  reindex                          清除並重建 ChromaDB 向量索引
  help
  q / exit

@author gabrielchen
@version 3.0
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

    #region 私有方法 — 選單輔助
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
            "files":    "檔案操作",
            "projects": "專案管理",
            "reviews":  "進度表",
            "ai":       "AI 對話",
            "other":    "其他",
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
        "status":     "_cmd_status",
        "todo":       "_cmd_todo",
        "projects":   "_cmd_projects",
        "integrity":  "_cmd_integrity",
        "clean":      "_cmd_clean_orphans",
        "checkindex": "_cmd_checkindex",
        "reindex":    "_cmd_reindex",
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
        _Lines: list = []
        _EmptyCount = 0
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

        # 去除末尾多餘空行
        while _Lines and _Lines[-1] == "":
            _Lines.pop()

        _Content = "\n".join( _Lines )
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
    #endregion
