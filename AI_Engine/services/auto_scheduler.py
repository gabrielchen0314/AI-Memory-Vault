"""
自動排程服務（APScheduler 觸發層）
封裝 SchedulerService，提供每週/每月/每日自動觸發。

排程規則：
  Daily:       每日 22:00      → generate_daily_summary()
  Weekly:      每週一 08:00    → generate_weekly_summary()
  Weekly AI:   每週一 09:00    → generate_ai_weekly_analysis()
  Monthly:     每月 1 日 08:00 → generate_monthly_summary()
  Monthly AI:  每月 1 日 09:00 → generate_ai_monthly_analysis()
  Full Sync:   每週日 02:00    → VaultService.sync()（清除孤立向量）

使用方式：
  from services.auto_scheduler import AutoScheduler
  sched = AutoScheduler( config )
  sched.start()       # 啟動背景排程（非阻塞）
  sched.block()       # 阻塞直到 Ctrl+C（供 main.py --scheduler 使用）
  sched.stop()        # 停止排程

@author gabrielchen
@version 1.1
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import AppConfig

_logger = logging.getLogger( __name__ )


class AutoScheduler:
    """APScheduler 觸發層：定期驅動 SchedulerService 的摘要方法。"""

    # ─────────────────────────────────────────────
    # Task Registry — 所有可用排程任務定義
    # ─────────────────────────────────────────────
    TASK_REGISTRY: dict = {
        "daily-summary": {
            "name":        "每日摘要",
            "description": "整理今日對話與活動，產生 personal/reviews/daily/",
            "schedule":    "每天",
        },
        "weekly-summary": {
            "name":        "每週摘要",
            "description": "彙整過去 7 天進度，產生 personal/reviews/weekly/",
            "schedule":    "每週一",
        },
        "weekly-ai": {
            "name":        "AI 週報分析",
            "description": "對話準確率、Token 統計，產生 personal/ai-analysis/weekly/",
            "schedule":    "每週一",
        },
        "monthly-summary": {
            "name":        "每月摘要",
            "description": "彙整過去 30 天進度，產生 personal/reviews/monthly/",
            "schedule":    "每月 1 日",
        },
        "monthly-ai": {
            "name":        "AI 月報分析",
            "description": "趨勢、優化、評分，產生 personal/ai-analysis/monthly/",
            "schedule":    "每月 1 日",
        },
        "vector-sync": {
            "name":        "向量同步",
            "description": "清除孤立向量，補漏本地直接修改的檔案",
            "schedule":    "每週日",
        },
        "morning-brief": {
            "name":        "早安簡報",
            "description": "顯示今日待辦事項 + 排程任務一覽",
            "schedule":    "每天早上",
        },
        "auto-all": {
            "name":        "全自動（智慧選擇）",
            "description": "依星期/日期自動決定：每天=摘要、週一+週報、1日+月報、週日+同步",
            "schedule":    "每天",
        },
        "monthly-retrospective": {
            "name":        "月度復盤",
            "description": "生成月度復盤報告（Instinct 統計、問題分析、協作效率），產生 personal/reviews/monthly/",
            "schedule":    "每月 1 日",
        },
        "db-backup": {
            "name":        "資料庫備份",
            "description": "壓縮 ChromaDB 向量索引為 zip 備份，保留最近 7 份",
            "schedule":    "每天 03:00",
        },
        "extract-sessions": {
            "name":        "VS Code 對話提取",
            "description": "從 chatSessions/*.jsonl 提取 Q&A 對話到 Vault conversations/（零 LLM Token）",
            "schedule":    "依需求",
        },
    }

    #region 成員變數
    ## <summary>應用程式設定</summary>
    m_Config: AppConfig
    ## <summary>APScheduler 背景排程器</summary>
    m_Scheduler: BackgroundScheduler
    ## <summary>業務邏輯服務</summary>
    m_Service: SchedulerService
    #endregion

    def __init__( self, iConfig: AppConfig ):
        """
        初始化自動排程服務。

        Args:
            iConfig: 應用程式設定。
        """
        from services.scheduler import SchedulerService

        self.m_Config    = iConfig
        self.m_Scheduler = BackgroundScheduler()
        self.m_Service   = SchedulerService( iConfig )

    # ─────────────────────────────────────────────
    #region 公開方法
    # ─────────────────────────────────────────────

    def start( self ) -> None:
        """
        啟動背景排程（非阻塞）。
        向排程器注冊六個 cron 任務：daily 摘要、weekly 摘要、weekly AI 分析、
        monthly 摘要、monthly AI 分析、每週全量 DB sync。
        """
        from services.vault import VaultService
        VaultService.initialize( self.m_Config )

        # Daily：每日 22:00
        self.m_Scheduler.add_job(
            self._run_daily,
            CronTrigger( hour=22, minute=0 ),
            id="daily_summary",
            replace_existing=True,
        )

        # Weekly：每週一 08:00
        self.m_Scheduler.add_job(
            self._run_weekly,
            CronTrigger( day_of_week="mon", hour=8, minute=0 ),
            id="weekly_summary",
            replace_existing=True,
        )

        # Weekly AI：每週一 09:00（接在 weekly_summary 之後）
        self.m_Scheduler.add_job(
            self._run_ai_weekly,
            CronTrigger( day_of_week="mon", hour=9, minute=0 ),
            id="ai_weekly_analysis",
            replace_existing=True,
        )

        # Monthly：每月 1 日 08:00
        self.m_Scheduler.add_job(
            self._run_monthly,
            CronTrigger( day=1, hour=8, minute=0 ),
            id="monthly_summary",
            replace_existing=True,
        )

        # Monthly AI：每月 1 日 09:00（接在 monthly_summary 之後）
        self.m_Scheduler.add_job(
            self._run_ai_monthly,
            CronTrigger( day=1, hour=9, minute=0 ),
            id="ai_monthly_analysis",
            replace_existing=True,
        )

        # Full Sync：每週日 02:00（清除孤立向量，補漏本地直接修改的檔案）
        self.m_Scheduler.add_job(
            self._run_full_sync,
            CronTrigger( day_of_week="sun", hour=2, minute=0 ),
            id="weekly_full_sync",
            replace_existing=True,
        )

        # DB Backup：每天 03:00（壓縮 ChromaDB → backups/）
        self.m_Scheduler.add_job(
            self._run_db_backup,
            CronTrigger( hour=3, minute=0 ),
            id="daily_db_backup",
            replace_existing=True,
        )

        self.m_Scheduler.start()
        _logger.info( "[AutoScheduler] 已啟動（daily/weekly/weekly-AI/monthly/monthly-AI/full-sync/db-backup 任務已排入）" )

    def stop( self ) -> None:
        """停止背景排程器。"""
        if self.m_Scheduler.running:
            self.m_Scheduler.shutdown( wait=False )
            _logger.info( "[AutoScheduler] 已停止" )

    def block( self ) -> None:
        """
        阻塞主執行緒直到收到 KeyboardInterrupt。
        供 main.py --scheduler 的守護進程模式使用。
        """
        _logger.info( "[AutoScheduler] 背景模式執行中，按 Ctrl+C 停止..." )
        try:
            while True:
                import time
                time.sleep( 60 )
        except ( KeyboardInterrupt, SystemExit ):
            self.stop()

    def run_once( self, daily_only: bool = False ) -> list:
        """
        依今日日期執行一次所有適用的排程任務，回傳完成項目清單。
        供 --once 模式（Windows 工作排程器觸發）使用。

        觸發規則（daily_only=False）：
          Daily    → 每天
          Weekly   → 每週一
          Monthly  → 每月 1 日
          Full Sync → 每週日

        Args:
            daily_only: True = 僅執行每日摘要（--daily-only 模式）
        """
        from services.vault import VaultService
        VaultService.initialize( self.m_Config )

        _Today   = datetime.now()
        _Date    = _Today.strftime( "%Y-%m-%d" )
        _Results = []

        # ── Daily（每天）────────────────────────────────────────
        try:
            _Path = self.m_Service.generate_daily_summary( _Date )
            _Results.append( ( "✅ 每日摘要", f"已產生：{_Path}" ) )
            _logger.info( f"[run_once] daily OK → {_Path}" )
        except Exception as _Err:
            _Results.append( ( "❌ 每日摘要", str( _Err ) ) )
            _logger.error( f"[run_once] daily ERROR: {_Err}" )

        if daily_only:
            return _Results

        # ── Weekly（每週一）─────────────────────────────────────
        if _Today.weekday() == 0:
            try:
                _Path = self.m_Service.generate_weekly_summary( _Date )
                _Results.append( ( "✅ 每週摘要", f"已產生：{_Path}" ) )
                _logger.info( f"[run_once] weekly OK → {_Path}" )
            except Exception as _Err:
                _Results.append( ( "❌ 每週摘要", str( _Err ) ) )
                _logger.error( f"[run_once] weekly ERROR: {_Err}" )

            try:
                _Path = self.m_Service.generate_ai_weekly_analysis( _Date )
                _Results.append( ( "✅ AI 週報分析", f"已產生：{_Path}" ) )
                _logger.info( f"[run_once] ai_weekly OK → {_Path}" )
            except Exception as _Err:
                _Results.append( ( "❌ AI 週報分析", str( _Err ) ) )
                _logger.error( f"[run_once] ai_weekly ERROR: {_Err}" )

        # ── Monthly（每月 1 日）──────────────────────────────────
        if _Today.day == 1:
            try:
                _Path = self.m_Service.generate_monthly_summary( _Date )
                _Results.append( ( "✅ 每月摘要", f"已產生：{_Path}" ) )
                _logger.info( f"[run_once] monthly OK → {_Path}" )
            except Exception as _Err:
                _Results.append( ( "❌ 每月摘要", str( _Err ) ) )
                _logger.error( f"[run_once] monthly ERROR: {_Err}" )

            try:
                _Path = self.m_Service.generate_ai_monthly_analysis( _Date )
                _Results.append( ( "✅ AI 月報分析", f"已產生：{_Path}" ) )
                _logger.info( f"[run_once] ai_monthly OK → {_Path}" )
            except Exception as _Err:
                _Results.append( ( "❌ AI 月報分析", str( _Err ) ) )
                _logger.error( f"[run_once] ai_monthly ERROR: {_Err}" )

            try:
                from services.instinct import InstinctService
                _InstSvc = InstinctService( self.m_Config )
                _Path = _InstSvc.generate_retrospective()
                _Results.append( ( "✅ 月度復盤", f"已產生：{_Path}" ) )
                _logger.info( f"[run_once] retrospective OK → {_Path}" )
            except Exception as _Err:
                _Results.append( ( "❌ 月度復盤", str( _Err ) ) )
                _logger.error( f"[run_once] retrospective ERROR: {_Err}" )

        # ── DB Backup（每天）──────────────────────────────────
        try:
            _Detail = self._exec_db_backup()
            _Results.append( ( "✅ 資料庫備份", f"已完成：{_Detail}" ) )
            _logger.info( f"[run_once] db_backup OK → {_Detail}" )
        except Exception as _Err:
            _Results.append( ( "❌ 資料庫備份", str( _Err ) ) )
            _logger.error( f"[run_once] db_backup ERROR: {_Err}" )

        # ── Full Sync（每週日）──────────────────────────────────
        if _Today.weekday() == 6:
            try:
                _Result  = VaultService.sync()
                _Deleted = _Result.get( "index_stats", {} ).get( "num_deleted", 0 )
                _Results.append( ( "✅ 向量同步", f"已完成：清除孤立向量 {_Deleted} 筆" ) )
                _logger.info( f"[run_once] full_sync OK → deleted={_Deleted}" )
            except Exception as _Err:
                _Results.append( ( "❌ 向量同步", str( _Err ) ) )
                _logger.error( f"[run_once] full_sync ERROR: {_Err}" )

        return _Results

    def run_task( self, iTaskId: str ) -> list:
        """
        依 task_id 執行單一排程任務。

        Args:
            iTaskId: TASK_REGISTRY 中的 key（如 'daily-summary'）。

        Returns:
            [ (label, detail), ... ] 結果清單。
        """
        if iTaskId == "auto-all":
            return self.run_once()

        if iTaskId not in self.TASK_REGISTRY:
            return [ ( "❌ 未知任務", f"task_id='{iTaskId}' 不在 TASK_REGISTRY 中" ) ]

        from services.vault import VaultService
        VaultService.initialize( self.m_Config )

        _Date    = datetime.now().strftime( "%Y-%m-%d" )
        _Results = []
        _Name    = self.TASK_REGISTRY[iTaskId]["name"]

        _Handlers = {
            "daily-summary":          lambda: self.m_Service.generate_daily_summary( _Date ),
            "weekly-summary":         lambda: self.m_Service.generate_weekly_summary( _Date ),
            "weekly-ai":              lambda: self.m_Service.generate_ai_weekly_analysis( _Date ),
            "monthly-summary":        lambda: self.m_Service.generate_monthly_summary( _Date ),
            "monthly-ai":             lambda: self.m_Service.generate_ai_monthly_analysis( _Date ),
            "vector-sync":            lambda: self._exec_vector_sync(),
            "morning-brief":          lambda: self._exec_morning_brief( _Date ),
            "monthly-retrospective":  lambda: self._exec_retrospective(),
            "db-backup":              lambda: self._exec_db_backup(),
            "extract-sessions":       lambda: self._exec_extract_sessions(),
        }

        _Handler = _Handlers.get( iTaskId )
        if _Handler is None:
            return [ ( f"❌ {_Name}", "尚未實作" ) ]

        try:
            _Detail = _Handler()
            _Results.append( ( f"✅ {_Name}", f"已完成：{_Detail}" ) )
            _logger.info( f"[run_task] {iTaskId} OK → {_Detail}" )
        except Exception as _Err:
            _Results.append( ( f"❌ {_Name}", str( _Err ) ) )
            _logger.error( f"[run_task] {iTaskId} ERROR: {_Err}" )

        return _Results

    @classmethod
    def list_tasks( cls ) -> list:
        """
        回傳所有可用任務的 ID + 名稱 + 說明，供 --list-tasks 或 UI 列表使用。

        Returns:
            [ { "id": str, "name": str, "description": str, "schedule": str }, ... ]
        """
        return [
            { "id": _Id, **_Info }
            for _Id, _Info in cls.TASK_REGISTRY.items()
        ]

    def job_count( self ) -> int:
        """回傳目前已排入的任務數量（供測試驗證用）。"""
        return len( self.m_Scheduler.get_jobs() )

    #endregion

    # ─────────────────────────────────────────────
    #region 私有方法 — 任務執行
    # ─────────────────────────────────────────────

    def _run_weekly( self ) -> None:
        """每週一 08:00 自動生成每週摘要。"""
        _Date = datetime.now().strftime( "%Y-%m-%d" )
        _logger.info( f"[AutoScheduler] _run_weekly  → {_Date}" )
        try:
            _Path = self.m_Service.generate_weekly_summary( _Date )
            _logger.info( f"[AutoScheduler] weekly OK → {_Path}" )
        except Exception as _Err:
            _logger.error( f"[AutoScheduler] weekly ERROR: {_Err}" )

    def _run_monthly( self ) -> None:
        """每月 1 日 08:00 自動生成每月摘要。"""
        _Date = datetime.now().strftime( "%Y-%m-%d" )
        _logger.info( f"[AutoScheduler] _run_monthly → {_Date}" )
        try:
            _Path = self.m_Service.generate_monthly_summary( _Date )
            _logger.info( f"[AutoScheduler] monthly OK → {_Path}" )
        except Exception as _Err:
            _logger.error( f"[AutoScheduler] monthly ERROR: {_Err}" )

    def _run_daily( self ) -> None:
        """每日 22:00 自動生成每日摘要。"""
        _Date = datetime.now().strftime( "%Y-%m-%d" )
        _logger.info( f"[AutoScheduler] _run_daily   → {_Date}" )
        try:
            _Path = self.m_Service.generate_daily_summary( _Date )
            _logger.info( f"[AutoScheduler] daily OK → {_Path}" )
        except Exception as _Err:
            _logger.error( f"[AutoScheduler] daily ERROR: {_Err}" )

    def _run_ai_weekly( self ) -> None:
        """每週一 09:00 自動生成 AI 對話週報分析。"""
        _Date = datetime.now().strftime( "%Y-%m-%d" )
        _logger.info( f"[AutoScheduler] _run_ai_weekly  → {_Date}" )
        try:
            _Path = self.m_Service.generate_ai_weekly_analysis( _Date )
            _logger.info( f"[AutoScheduler] ai_weekly OK → {_Path}" )
        except Exception as _Err:
            _logger.error( f"[AutoScheduler] ai_weekly ERROR: {_Err}" )

    def _run_ai_monthly( self ) -> None:
        """每月 1 日 09:00 自動生成 AI 對話月報分析。"""
        _Date = datetime.now().strftime( "%Y-%m-%d" )
        _logger.info( f"[AutoScheduler] _run_ai_monthly → {_Date}" )
        try:
            _Path = self.m_Service.generate_ai_monthly_analysis( _Date )
            _logger.info( f"[AutoScheduler] ai_monthly OK → {_Path}" )
        except Exception as _Err:
            _logger.error( f"[AutoScheduler] ai_monthly ERROR: {_Err}" )

    def _run_full_sync( self ) -> None:
        """每週日 02:00 執行全量 DB sync，清除孤立向量。"""
        from services.vault import VaultService
        _logger.info( "[AutoScheduler] _run_full_sync → start" )
        try:
            _Result = VaultService.sync()
            _Deleted = _Result.get( "index_stats", {} ).get( "num_deleted", 0 )
            _logger.info( f"[AutoScheduler] full_sync OK → deleted={_Deleted}" )
        except Exception as _Err:
            _logger.error( f"[AutoScheduler] full_sync ERROR: {_Err}" )

    def _exec_vector_sync( self ) -> str:
        """run_task 用：執行向量同步，回傳結果摘要。"""
        from services.vault import VaultService
        _Result  = VaultService.sync()
        _Deleted = _Result.get( "index_stats", {} ).get( "num_deleted", 0 )
        return f"清除孤立向量 {_Deleted} 筆"

    def _run_db_backup( self ) -> None:
        """每天 03:00 自動備份 ChromaDB。"""
        _logger.info( "[AutoScheduler] _run_db_backup → start" )
        try:
            _Detail = self._exec_db_backup()
            _logger.info( f"[AutoScheduler] db_backup OK → {_Detail}" )
        except Exception as _Err:
            _logger.error( f"[AutoScheduler] db_backup ERROR: {_Err}" )

    def _exec_db_backup( self ) -> str:
        """run_task 用：執行 ChromaDB 備份 + 清理舊備份，回傳結果摘要。"""
        from services.backup import BackupService
        _Svc = BackupService( self.m_Config )
        _Path, _Err = _Svc.backup_chromadb()
        if _Err:
            raise RuntimeError( _Err )
        _Cleaned = _Svc.cleanup()
        return f"備份至 {_Path}，清除 {_Cleaned} 份舊備份"

    def _exec_morning_brief( self, iDate: str ) -> str:
        """
        run_task 用：產生早安簡報（今日待辦 + 排程任務狀態）。
        掃描所有專案的 status.md 提取進行中的待辦，
        加上今天已有的 conversations/ 活動。
        """
        import os

        _VaultPath = self.m_Config.vault_path
        _Lines     = []

        # 1. 掃描所有專案的 status.md → 找 [ ] 待辦
        _WsDir = os.path.join( _VaultPath, "workspaces" )
        if os.path.isdir( _WsDir ):
            for _Org in sorted( os.listdir( _WsDir ) ):
                _ProjsDir = os.path.join( _WsDir, _Org, "projects" )
                if not os.path.isdir( _ProjsDir ):
                    continue
                for _Proj in sorted( os.listdir( _ProjsDir ) ):
                    _StatusPath = os.path.join( _ProjsDir, _Proj, "status.md" )
                    if not os.path.isfile( _StatusPath ):
                        continue
                    _Todos = []
                    with open( _StatusPath, "r", encoding="utf-8" ) as _F:
                        for _Line in _F:
                            _Stripped = _Line.strip()
                            if _Stripped.startswith( "- [ ]" ):
                                _Todos.append( _Stripped[5:].strip() )
                    if _Todos:
                        _Lines.append( f"## {_Org}/{_Proj}" )
                        for _T in _Todos:
                            _Lines.append( f"- [ ] {_T}" )
                        _Lines.append( "" )

        # 2. 今日有無對話紀錄
        _ConvCount = 0
        if os.path.isdir( _WsDir ):
            for _Root, _Dirs, _Files in os.walk( _WsDir ):
                if "conversations" in _Root:
                    _ConvCount += sum( 1 for _F in _Files if _F.startswith( iDate ) )

        if not _Lines and _ConvCount == 0:
            return "今日無待辦、無對話紀錄"

        _Header = f"# 早安簡報 {iDate}\n\n"
        if _ConvCount:
            _Header += f"> 今日已有 {_ConvCount} 筆對話紀錄\n\n"

        _Content = _Header + "\n".join( _Lines )

        # 寫入 personal/reviews/daily/{date}-brief.md
        _RelPath = f"personal/reviews/daily/{iDate}-brief.md"
        _AbsPath = os.path.join( _VaultPath, _RelPath )
        os.makedirs( os.path.dirname( _AbsPath ), exist_ok=True )
        with open( _AbsPath, "w", encoding="utf-8" ) as _F:
            _F.write( _Content )

        return _RelPath

    def _exec_retrospective( self ) -> str:
        """run_task 用：生成上月月度復盤報告。"""
        from services.instinct import InstinctService
        _Svc = InstinctService( self.m_Config )
        return _Svc.generate_retrospective()

    def _exec_extract_sessions( self ) -> str:
        """
        run_task 用：從 VS Code chatSessions/*.jsonl 提取 Q&A 對話到 Vault conversations/。
        不消耗任何 LLM Token。
        """
        from services.session_extractor import SessionExtractor

        _ChatDir   = self.m_Config.vscode_chat_dir
        _VaultPath = self.m_Config.vault_path

        if not _ChatDir:
            return "vscode_chat_dir 未設定，請於 config.json 或 setup 中設定 VS Code chatSessions 路徑"

        # 取得預設組織與專案（使用第一個組織 + 存在 status.md 的第一個專案）
        import os
        _Org     = ""
        _Project = ""
        _Orgs    = self.m_Config.user.organizations
        if _Orgs:
            _Org = _Orgs[0]
            _ProjsDir = os.path.join( _VaultPath, "workspaces", _Org, "projects" )
            if os.path.isdir( _ProjsDir ):
                for _P in sorted( os.listdir( _ProjsDir ) ):
                    if os.path.isfile( os.path.join( _ProjsDir, _P, "status.md" ) ):
                        _Project = _P
                        break

        if not _Org or not _Project:
            return "找不到有效的組織/專案，請確認 config.json 的 user.organizations 設定"

        _Extractor = SessionExtractor( _ChatDir, _VaultPath )
        _Count     = _Extractor.extract_new( _Org, _Project )

        if _Count == 0:
            return "沒有新增的對話，watermark 已是最新"
        return f"已提取 {_Count} 個 session 的新 Q&A 對話至 conversations/"

    #endregion
