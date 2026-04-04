"""
自動排程服務（APScheduler 觸發層）
封裝 SchedulerService，提供每週/每月/每日自動觸發。

排程規則：
  Weekly:  每週一 08:00 → generate_weekly_summary()
  Monthly: 每月 1 日 08:00 → generate_monthly_summary()
  Daily:   每日 22:00 → generate_daily_summary()

使用方式：
  from services.auto_scheduler import AutoScheduler
  sched = AutoScheduler( config )
  sched.start()       # 啟動背景排程（非阻塞）
  sched.block()       # 阻塞直到 Ctrl+C（供 main.py --scheduler 使用）
  sched.stop()        # 停止排程

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
import sys
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import AppConfig
from services.scheduler import SchedulerService
from services.vault import VaultService


class AutoScheduler:
    """APScheduler 觸發層：定期驅動 SchedulerService 的摘要方法。"""

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
        self.m_Config    = iConfig
        self.m_Scheduler = BackgroundScheduler()
        self.m_Service   = SchedulerService( iConfig )

    # ─────────────────────────────────────────────
    #region 公開方法
    # ─────────────────────────────────────────────

    def start( self ) -> None:
        """
        啟動背景排程（非阻塞）。
        同時初始化 VaultService，並向排程器注冊三個 cron 任務。
        """
        VaultService.initialize( self.m_Config )

        # Weekly：每週一 08:00
        self.m_Scheduler.add_job(
            self._run_weekly,
            CronTrigger( day_of_week="mon", hour=8, minute=0 ),
            id="weekly_summary",
            replace_existing=True,
        )

        # Monthly：每月 1 日 08:00
        self.m_Scheduler.add_job(
            self._run_monthly,
            CronTrigger( day=1, hour=8, minute=0 ),
            id="monthly_summary",
            replace_existing=True,
        )

        # Daily：每日 22:00
        self.m_Scheduler.add_job(
            self._run_daily,
            CronTrigger( hour=22, minute=0 ),
            id="daily_summary",
            replace_existing=True,
        )

        self.m_Scheduler.start()
        print( "[AutoScheduler] 已啟動（weekly/monthly/daily 任務已排入）" )

    def stop( self ) -> None:
        """停止背景排程器。"""
        if self.m_Scheduler.running:
            self.m_Scheduler.shutdown( wait=False )
            print( "[AutoScheduler] 已停止" )

    def block( self ) -> None:
        """
        阻塞主執行緒直到收到 KeyboardInterrupt。
        供 main.py --scheduler 的守護進程模式使用。
        """
        print( "[AutoScheduler] 背景模式執行中，按 Ctrl+C 停止..." )
        try:
            while True:
                import time
                time.sleep( 60 )
        except ( KeyboardInterrupt, SystemExit ):
            self.stop()

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
        print( f"[AutoScheduler] _run_weekly  → {_Date}", flush=True )
        try:
            _Path = self.m_Service.generate_weekly_summary( _Date )
            print( f"[AutoScheduler] weekly OK → {_Path}", flush=True )
        except Exception as _Err:
            print( f"[AutoScheduler] weekly ERROR: {_Err}", file=sys.stderr, flush=True )

    def _run_monthly( self ) -> None:
        """每月 1 日 08:00 自動生成每月摘要。"""
        _Date = datetime.now().strftime( "%Y-%m-%d" )
        print( f"[AutoScheduler] _run_monthly → {_Date}", flush=True )
        try:
            _Path = self.m_Service.generate_monthly_summary( _Date )
            print( f"[AutoScheduler] monthly OK → {_Path}", flush=True )
        except Exception as _Err:
            print( f"[AutoScheduler] monthly ERROR: {_Err}", file=sys.stderr, flush=True )

    def _run_daily( self ) -> None:
        """每日 22:00 自動生成每日摘要。"""
        _Date = datetime.now().strftime( "%Y-%m-%d" )
        print( f"[AutoScheduler] _run_daily   → {_Date}", flush=True )
        try:
            _Path = self.m_Service.generate_daily_summary( _Date )
            print( f"[AutoScheduler] daily OK → {_Path}", flush=True )
        except Exception as _Err:
            print( f"[AutoScheduler] daily ERROR: {_Err}", file=sys.stderr, flush=True )

    #endregion
