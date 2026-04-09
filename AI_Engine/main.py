"""
AI Memory Vault v3 — 入口程式
支援 CLI / API / MCP 三種模式，首次執行自動觸發 Setup Wizard。

用法：
    python main.py                          → 啟動 Setup Wizard（首次）或 CLI 模式
    python main.py --mode cli               → CLI 互動模式
    python main.py --mode api               → FastAPI 伺服器
    python main.py --mode mcp               → MCP stdio 伺服器
    python main.py --scheduler              → 啟動 APScheduler 守護模式（週/月/日自動生成）
    python main.py --reindex                → 清除向量索引並重建（嵌入模型/chunk設定變更後使用）
    python main.py --setup                  → 強制重新執行完整 Setup Wizard
    python main.py --setup-section vault    → 僅設定 Vault 路徑
    python main.py --setup-section user     → 僅設定使用者資訊
    python main.py --setup-section org      → 組織管理（新增/移除）
    python main.py --setup-section llm      → 僅設定 LLM

@author gabrielchen
@version 3.5
@since AI-Memory-Vault 3.0
@date 2026.04.10
"""
import argparse
import sys
import os
from pathlib import Path

# ── 凍結模式：強制 stdout/stderr 使用 UTF-8，避免 Windows codepage 導致 crash ──
if getattr( sys, 'frozen', False ):
    try:
        sys.stdout.reconfigure( encoding='utf-8', errors='replace' )
        sys.stderr.reconfigure( encoding='utf-8', errors='replace' )
    except Exception:
        pass

# 確保 AI_Engine 目錄在 sys.path 中
# PyInstaller frozen 模式：__file__ 指向 bundle 內部，改用 sys.executable 所在目錄
if getattr( sys, 'frozen', False ):
    _ENGINE_DIR = os.path.dirname( sys.executable )
else:
    _ENGINE_DIR = os.path.dirname( os.path.abspath( __file__ ) )
if _ENGINE_DIR not in sys.path:
    sys.path.insert( 0, _ENGINE_DIR )
os.chdir( _ENGINE_DIR )


from cli.setup_commands import SETUP_SECTIONS


# ── 依賴檢查（僅使用 stdlib，在任何 import 之前執行）──────────

def _find_missing_packages() -> list:
    """
    快速掃描關鍵套件是否可用（stdlib importlib，無需 pip）。

    Returns:
        缺少的 pip 套件名稱清單；若全部已安裝則回傳空清單。
    """
    import importlib.util as _ilu

    ## <summary>關鍵套件對照表：(module_name, pip_package_name)</summary>
    _CANARIES = [
        ( "langchain",             "langchain" ),
        ( "chromadb",              "chromadb" ),
        ( "sentence_transformers", "sentence-transformers" ),
        ( "mcp",                   "mcp[cli]" ),
        ( "apscheduler",           "apscheduler" ),
        ( "questionary",           "questionary" ),
    ]
    return [
        _PkgName
        for _ModName, _PkgName in _CANARIES
        if _ilu.find_spec( _ModName ) is None
    ]


def _ask_install_gui( iMissing: list ) -> bool:
    """
    以 tkinter 彈窗詢問使用者是否安裝缺少的套件。

    Args:
        iMissing: 缺少的 pip 套件名稱清單。

    Returns:
        True = 同意安裝；False = 拒絕；None = tkinter 不可用（需降級）。
    """
    try:
        import tkinter as _tk
        from tkinter import messagebox as _mb

        _Names = "\n".join( f"  • {_P}" for _P in iMissing )
        _Msg = (
            f"偵測到以下套件尚未安裝：\n\n{_Names}\n\n"
            "是否立即安裝（pip install -r requirements.txt）？"
        )
        _Root = _tk.Tk()
        _Root.withdraw()                  # 隱藏主視窗
        _Root.attributes( "-topmost", True )  # 彈窗置頂
        _Result = _mb.askyesno( "AI Memory Vault — 缺少套件", _Msg )
        _Root.destroy()
        return _Result

    except Exception:
        return None  # tkinter 不可用 → 呼叫端降級為終端機提示


def _check_and_install_deps() -> None:
    """
    啟動前依賴自動檢查與安裝引導。
    僅在套件真正缺少時才觸發，正常啟動零額外耗費。

    執行模式策略：
        CLI / Scheduler：先嘗試 tkinter 彈窗，失敗時降級為 terminal input()。
        MCP：不可使用 GUI 或 stdin（VS Code 自動啟動），改為靜默安裝到 stderr。
    """
    import subprocess

    _Missing = _find_missing_packages()
    if not _Missing:
        return  # 全部已安裝，直接跳過

    _ReqFile = os.path.join( _ENGINE_DIR, "requirements.txt" )
    _IsMcp   = "--mode" in sys.argv and "mcp" in sys.argv

    # ── MCP 模式：靜默安裝 ────────────────────────────────
    if _IsMcp:
        print( "[ai-memory-vault] ⚙️  缺少依賴套件，正在安裝中…", file=sys.stderr )
        _Ret = subprocess.run(
            [ sys.executable, "-m", "pip", "install", "-r", _ReqFile, "-q" ],
            stderr=sys.stderr,
        )
        if _Ret.returncode != 0:
            print( "[ai-memory-vault] ❌ 依賴安裝失敗，請手動執行：", file=sys.stderr )
            print( f"  pip install -r {_ReqFile}", file=sys.stderr )
            sys.exit( 1 )
        return

    # ── CLI / Scheduler 模式：詢問使用者 ─────────────────
    _Confirmed = _ask_install_gui( _Missing )

    if _Confirmed is None:
        # tkinter 不可用 → 終端機降級
        print( "\n⚠️  偵測到缺少以下套件：" )
        for _P in _Missing:
            print( f"  • {_P}" )
        _Ans = input( "\n是否立即安裝（pip install -r requirements.txt）？[Y/n]: " ).strip().lower()
        _Confirmed = ( _Ans != "n" )

    if not _Confirmed:
        print( "已取消。請手動安裝後再啟動：" )
        print( f"  pip install -r requirements.txt" )
        sys.exit( 0 )

    # ── 執行安裝 ──────────────────────────────────────────
    print( "\n📦 正在安裝依賴套件（pip install -r requirements.txt）…\n" )
    _Ret = subprocess.run(
        [ sys.executable, "-m", "pip", "install", "-r", _ReqFile ],
    )
    if _Ret.returncode != 0:
        print( "\n❌ 安裝失敗，請手動執行：" )
        print( f"  pip install -r {_ReqFile}" )
        sys.exit( 1 )
    print( "\n✅ 安裝完成，繼續啟動…\n" )


def _detect_frozen_mode() -> None:
    """
    PyInstaller 打包後，根據執行檔名稱自動設定執行模式。
    僅在 sys.frozen 且尚未傳入任何引數時生效，避免覆蓋明確的命令列參數。

      vault-mcp.exe       → --mode mcp
      vault-scheduler.exe → --scheduler
      vault-cli.exe       → 沿用 argparse 預設（CLI 模式）
    """
    if not getattr( sys, 'frozen', False ):
        return
    if len( sys.argv ) > 1:
        return  # 已有明確參數，不覆蓋
    _Exe = os.path.basename( sys.executable ).lower()
    if 'mcp' in _Exe:
        sys.argv.extend( [ '--mode', 'mcp' ] )
    elif 'scheduler' in _Exe:
        # 預設執行一次（Windows 工作排程器用）；明確傳 --scheduler 才進守護模式
        sys.argv.append( '--once' )
    # vault-cli.exe：不加參數，argparse 預設即 CLI 模式


def main():
    """主入口：依賴檢查 → 解析參數 → 檢查初始化 → 分發執行模式。"""
    _detect_frozen_mode()
    # frozen 模式下套件已內嵌，跳過依賴安裝檢查
    if not getattr( sys, 'frozen', False ):
        _check_and_install_deps()

    _Parser = argparse.ArgumentParser( description="AI Memory Vault v3 — 記憶庫引擎" )
    _Parser.add_argument(
        "--mode",
        choices=[ "cli", "api", "mcp" ],
        default="cli",
        help="啟動模式：cli（互動終端）/ api（FastAPI 伺服器）/ mcp（MCP stdio 伺服器）",
    )
    _Parser.add_argument(
        "--setup",
        action="store_true",
        help="強制重新執行完整 Setup Wizard",
    )
    _Parser.add_argument(
        "--setup-section",
        choices=SETUP_SECTIONS,
        help="設定特定區段：vault / user / org / llm",
    )
    _Parser.add_argument(
        "--reconfigure",
        action="store_true",
        help="重新設定所有區段（保留資料庫，逐項引導）",
    )
    _Parser.add_argument(
        "--scheduler",
        action="store_true",
        help="啟動 APScheduler 守護模式（weekly/monthly/daily 自動生成摘要）",
    )
    _Parser.add_argument(
        "--menu",
        action="store_true",
        help="CLI 選單模式（方向鍵圓式選單，預設 CLI 指令列）",
    )
    _Parser.add_argument(
        "--reindex",
        action="store_true",
        help="清除向量索引並完整重建（嵌入模型或 chunk 設定變更後使用）",
    )
    _Parser.add_argument(
        "--once",
        action="store_true",
        help="執行一次所有適用於今日的排程任務後結束（Windows 工作排程器用）",
    )
    _Parser.add_argument(
        "--headless",
        action="store_true",
        help="非互動模式（Windows Task Scheduler 後台執行，跳過 Enter 等待）",
    )
    _Parser.add_argument(
        "--daily-only",
        action="store_true",
        help="僅執行每日摘要，忽略週報/月報/同步（搭配 --once 使用）",
    )
    _Parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="執行指定的排程任務（如 daily-summary, morning-brief），搭配 --headless 使用",
    )
    _Parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="列出所有可用排程任務（JSON 格式，供選單 UI 解析）",
    )
    _Args = _Parser.parse_args()

    from config import ConfigManager

    # ── 首次執行或強制 Setup ──────────────────────────────
    if _Args.setup or not ConfigManager.is_initialized():
        from cli.setup_commands import run_setup_wizard
        run_setup_wizard()
        if _Args.setup:
            return

    # ── 強制重建索引 ─────────────────────────
    if _Args.reindex:
        _run_reindex()
        return

    # ── 重新完整設定（保留資料庫，逐項引導） ────────────
    if _Args.reconfigure:
        from cli.setup_commands import run_full_reconfigure
        run_full_reconfigure()
        return

    # ── 單一區段設定 ──────────────────────────
    if _Args.setup_section:
        from cli.setup_commands import dispatch_section
        dispatch_section( _Args.setup_section )
        return

    # ── 列出可用排程任務 ─────────────────────────────────
    if _Args.list_tasks:
        _list_available_tasks()
        return

    # ── 執行指定排程任務 ─────────────────────────────────
    if _Args.task:
        _start_scheduler_task( _Args.task, _Args.headless )
        return

    # ── 一次性排程（Windows 工作排程器觸發） ─────
    if _Args.once:
        _start_scheduler_once( _Args.daily_only, _Args.headless )
        return

    # ── 排程守護模式 ──────────────────────────────────────
    if _Args.scheduler:
        _start_scheduler()
        return

    # ── 正常啟動 ──────────────────────────────────────────
    _Config = ConfigManager.load()

    # MCP stdio 模式：bootstrap 期間同時封鎖 Python 層（sys.stdout）
    # 和 fd 層（fd 1），防止 C 擴展汙染 JSON-RPC 通道。
    # bootstrap 結束後兩層都必須還原，FastMCP 用 sys.stdout 寫回應。
    if _Args.mode == "mcp":
        _RealStdout = sys.stdout
        sys.stdout = sys.stderr
        _SavedFd1 = os.dup( 1 )
        os.dup2( 2, 1 )

    _bootstrap( _Config )

    if _Args.mode == "api":
        _start_api( _Config )
    elif _Args.mode == "mcp":
        # 還原 fd 1 + sys.stdout → FastMCP stdio transport 需要兩層都正常
        os.dup2( _SavedFd1, 1 )
        os.close( _SavedFd1 )
        sys.stdout = _RealStdout
        _start_mcp()
    else:
        _start_cli( _Config, getattr( _Args, "menu", False ) )


def _bootstrap( iConfig ):
    """
    初始化所有核心模組（Embeddings → VectorStore → VaultService）。
    同時執行 migration check：偵測 embedding model / chunk 設定是否變更。

    Args:
        iConfig: 應用程式設定。
    """
    from core import embeddings as _EmbModule
    from core import vectorstore as _VsModule
    from core.migration import MigrationManager
    from services.vault import VaultService

    # ── 遷移偵測 ──────────────────────────────────────────
    _NeedsReindex, _Changes = MigrationManager.check( iConfig )
    if _NeedsReindex:
        _Desc = MigrationManager.describe_changes( _Changes )
        print( "\n⚠️  偵測到索引相關設定已變更：" )
        print( _Desc )
        print( "   請執行 --reindex 重建索引以確保搜尋結果正確。\n" )

    _EmbModule.initialize( iConfig.embedding.model )
    _VsModule.initialize(
        iChromaDir=iConfig.database.get_chroma_path(),
        iRecordDbUrl=iConfig.database.get_record_db_url(),
        iCollectionName=iConfig.database.collection_name,
    )
    VaultService.initialize( iConfig )


def _list_available_tasks():
    """列出所有可用排程任務（JSON 格式輸出，供 vault-menu.ps1 解析）。"""
    import json
    from services.auto_scheduler import AutoScheduler
    _Tasks = AutoScheduler.list_tasks()
    print( json.dumps( _Tasks, ensure_ascii=False, indent=2 ) )


def _start_scheduler_task( iTaskId: str, iHeadless: bool = False ):
    """執行指定的排程任務，輸出結果後依 iHeadless 決定是否等待。"""
    import logging
    import os
    from datetime import datetime as _DT
    from config import ConfigManager
    from services.auto_scheduler import AutoScheduler

    # ── 設定 file logging ──────────────────────────────────────
    _DataDir = os.path.join( os.environ.get( "APPDATA", "" ), "AI-Memory-Vault" )
    os.makedirs( _DataDir, exist_ok=True )
    _LogPath = os.path.join( _DataDir, "scheduler.log" )

    _Handler = logging.FileHandler( _LogPath, encoding="utf-8" )
    _Handler.setFormatter( logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ) )
    logging.root.addHandler( _Handler )
    logging.root.setLevel( logging.INFO )

    _WeekDays  = [ "一", "二", "三", "四", "五", "六", "日" ]
    _StartTime = _DT.now()
    _TaskInfo  = AutoScheduler.TASK_REGISTRY.get( iTaskId, {} )
    _TaskName  = _TaskInfo.get( "name", iTaskId )
    _TaskDesc  = _TaskInfo.get( "description", "" )

    print( "" )
    print( "=" * 52 )
    print( "  AI Memory Vault - 排程任務執行報告" )
    print( "=" * 52 )
    print( f"  任務名稱：{_TaskName}" )
    if _TaskDesc:
        print( f"  任務說明：{_TaskDesc}" )
    print( f"  執行日期：{_StartTime.strftime( '%Y-%m-%d' )}（星期{_WeekDays[_StartTime.weekday()]}）" )
    print( f"  開始時間：{_StartTime.strftime( '%H:%M:%S' )}" )
    print( "" )

    _Config  = ConfigManager.load()
    _Sched   = AutoScheduler( _Config )
    _Results = _Sched.run_task( iTaskId )

    _EndTime      = _DT.now()
    _Elapsed      = ( _EndTime - _StartTime ).total_seconds()
    _SuccessCount = sum( 1 for _R in _Results if _R[0].startswith( "✅" ) )
    _FailCount    = sum( 1 for _R in _Results if _R[0].startswith( "❌" ) )

    print( "  ── 執行結果 ──────────────────────────────────" )
    print( "" )
    if _Results:
        for _Label, _Detail in _Results:
            print( f"  {_Label}" )
            print( f"    → {_Detail}" )
            print( "" )
    else:
        print( "  [i] 無結果" )
        print( "" )

    print( "  ── 執行統計 ──────────────────────────────────" )
    print( f"  完成時間：{_EndTime.strftime( '%H:%M:%S' )}" )
    print( f"  總耗時　：{_Elapsed:.1f} 秒" )
    _Summary = f"{_SuccessCount} 項成功"
    if _FailCount:
        _Summary += f" / {_FailCount} 項失敗"
    print( f"  執行結果：{_Summary}" )
    print( "" )
    print( "=" * 52 )
    print( "" )
    if not iHeadless:
        print( "按 Enter 鍵關閉視窗..." )
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass


def _start_scheduler_once( iDailyOnly: bool = False, iHeadless: bool = False ):
    """執行一次所有適用於今日的排程任務，輸出結果後等待按鍵結束。（Windows 工作排程器用）"""
    import logging
    import os
    from datetime import datetime as _DT
    from config import ConfigManager
    from services.auto_scheduler import AutoScheduler

    # ── 設定 file logging ──────────────────────────────────────
    _DataDir = os.path.join( os.environ.get( "APPDATA", "" ), "AI-Memory-Vault" )
    os.makedirs( _DataDir, exist_ok=True )
    _LogPath = os.path.join( _DataDir, "scheduler.log" )

    _Handler = logging.FileHandler( _LogPath, encoding="utf-8" )
    _Handler.setFormatter( logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ) )
    logging.root.addHandler( _Handler )
    logging.root.setLevel( logging.INFO )

    _WeekDays  = [ "一", "二", "三", "四", "五", "六", "日" ]
    _StartTime = _DT.now()
    _WeekDay   = _WeekDays[_StartTime.weekday()]

    # ── 預判今日會執行哪些任務 ────────────────────────────────
    _PlannedTasks = [ "每日摘要" ]
    if not iDailyOnly:
        if _StartTime.weekday() == 0:
            _PlannedTasks.extend( [ "每週摘要", "AI 週報分析" ] )
        if _StartTime.day == 1:
            _PlannedTasks.extend( [ "每月摘要", "AI 月報分析" ] )
        if _StartTime.weekday() == 6:
            _PlannedTasks.append( "向量同步" )

    print( "" )
    print( "=" * 52 )
    print( "  AI Memory Vault - 排程執行報告" )
    print( "=" * 52 )
    print( f"  執行日期：{_StartTime.strftime( '%Y-%m-%d' )}（星期{_WeekDay}）" )
    print( f"  開始時間：{_StartTime.strftime( '%H:%M:%S' )}" )
    print( f"  預計任務：{'、'.join( _PlannedTasks )}" )
    print( "" )

    _Config  = ConfigManager.load()
    _Sched   = AutoScheduler( _Config )
    _Results = _Sched.run_once( daily_only=iDailyOnly )

    _EndTime      = _DT.now()
    _Elapsed      = ( _EndTime - _StartTime ).total_seconds()
    _SuccessCount = sum( 1 for _R in _Results if _R[0].startswith( "✅" ) )
    _FailCount    = sum( 1 for _R in _Results if _R[0].startswith( "❌" ) )

    print( "  ── 執行結果 ──────────────────────────────────" )
    print( "" )
    if _Results:
        for _Label, _Detail in _Results:
            print( f"  {_Label}" )
            print( f"    → {_Detail}" )
            print( "" )
    else:
        print( "  [i] 今日無適用任務" )
        print( "" )

    print( "  ── 執行統計 ──────────────────────────────────" )
    print( f"  完成時間：{_EndTime.strftime( '%H:%M:%S' )}" )
    print( f"  總耗時　：{_Elapsed:.1f} 秒" )
    _Summary = f"{_SuccessCount} 項成功"
    if _FailCount:
        _Summary += f" / {_FailCount} 項失敗"
    print( f"  執行結果：{_Summary}" )
    print( "" )
    print( "=" * 52 )
    print( "" )
    if not iHeadless:
        print( "按 Enter 鍵關閉視窗..." )
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass


def _start_scheduler():
    """啟動 APScheduler 守護模式（非互動，阻塞直到 Ctrl+C）。"""
    import logging
    import os
    from config import ConfigManager
    from services.auto_scheduler import AutoScheduler

    # ── 設定 file logging ──────────────────────────────────────
    _DataDir = os.path.join( os.environ.get( "APPDATA", "" ), "AI-Memory-Vault" )
    os.makedirs( _DataDir, exist_ok=True )
    _LogPath = os.path.join( _DataDir, "scheduler.log" )

    _Handler = logging.FileHandler( _LogPath, encoding="utf-8" )
    _Handler.setFormatter( logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ) )
    logging.root.addHandler( _Handler )
    logging.root.setLevel( logging.INFO )

    print( f"[Scheduler] Log 路徑：{_LogPath}" )

    _Config = ConfigManager.load()
    _Sched  = AutoScheduler( _Config )
    _Sched.start()
    _Sched.block()


def _run_reindex():
    """
    清除現有向量索引並從零重建。
    用於 embedding model / chunk 設定變更後同步索引。
    """
    from config import ConfigManager
    from core.migration import MigrationManager
    from core import embeddings as _EmbModule, vectorstore as _VsModule
    from services.vault import VaultService

    _Config = ConfigManager.load()

    print( "" )
    print( "=" * 60 )
    print( "  🗑️  向量索引重建" )
    print( "=" * 60 )
    print( "  此操作將清除現有的 ChromaDB 向量索引，" )
    print( "  並從 Vault 目錄完整重建。" )
    print( "  Vault 筆記本身不受影響。" )
    print( "" )

    _Confirm = input( "確定要重建索引？(y/Enter = 確定，n = 取消): " ).strip().lower()
    if _Confirm == "n":
        print( "  已取消。" )
        return

    print( "\n  🗑️  清除索引中..." )
    _Ok, _Msg = MigrationManager.reset_index( _Config )
    if not _Ok:
        print( f"  ❌ {_Msg}" )
        return

    print( f"  ✅ {_Msg}" )
    print( "\n  🔄 初始化服務中..." )

    _EmbModule.initialize( _Config.embedding.model )
    _VsModule.initialize(
        iChromaDir=_Config.database.get_chroma_path(),
        iRecordDbUrl=_Config.database.get_record_db_url(),
        iCollectionName=_Config.database.collection_name,
    )
    VaultService.initialize( _Config )

    print( "  🔄 重建索引中（掃描所有 .md 檔案）..." )
    _Stats = VaultService.sync()
    _Idx = _Stats.get( "index_stats", {} )

    print( "" )
    print( f"  ✅ 重建完成！" )
    print( f"     新增：{_Idx.get('num_added', 0)} chunks" )
    print( f"     總數：{_Stats.get('total_chunks', 0)} chunks" )
    print( "" )


def _start_cli( iConfig, iMenu: bool = False ):
    """啟動 CLI 互動模式。"""
    from cli.repl import VaultRepl
    _Repl = VaultRepl( iConfig )
    if iMenu:
        _Repl.run_menu()
    else:
        _Repl.run()


def _start_api( iConfig ):
    """啟動 FastAPI 伺服器。"""
    print( "🔧 API 模式尚未實作（V3 Phase 2）" )


def _start_mcp():
    """啟動 MCP stdio 伺服器。"""
    from mcp_app.server import run_mcp_server
    run_mcp_server()


if __name__ == "__main__":
    try:
        main()
    except Exception as _E:
        import traceback as _tb
        _crash = _tb.format_exc()
        # 寫入日誌（UTF-8，確保能記錄中文）
        try:
            _log = Path.home() / "vault-crash.log"
            _log.write_text( _crash, encoding="utf-8" )
        except Exception:
            pass
        # 嘗試在終端顯示
        try:
            sys.stderr.write( "\n=== CRASH ===\n" )
            sys.stderr.write( _crash )
            sys.stderr.flush()
        except Exception:
            pass
        try:
            input( "\nCrash log: ~/vault-crash.log  Press Enter to exit..." )
        except Exception:
            pass
        sys.exit( 1 )
