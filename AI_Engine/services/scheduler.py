"""
排程任務服務
支援專案每日進度、個人總進度（daily/weekly/monthly）、AI 對話紀錄與分析等定時任務。

進度分層架構：
  - 專案詳細：workspaces/{org}/projects/{proj}/daily/{date}.md
  - 專案對話：workspaces/{org}/projects/{proj}/conversations/{date}_{session}.md
  - 每日總結：personal/reviews/daily/{date}.md（文本）+ _global/reviews/daily/{date}.md（連結）
  - 每週總結：personal/reviews/weekly/{year}-W{week}.md + _global 連結
  - 每月總結：personal/reviews/monthly/{month}.md + _global 連結

AI 對話分析：
  - 每週分析：personal/ai-analysis/weekly/{year}-W{week}.md
  - 每月分析：personal/ai-analysis/monthly/{year-mm}.md

@author gabrielchen
@version 3.2
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Optional

from core.logger import get_logger

_logger = get_logger( __name__ )

from config import AppConfig


class SchedulerService:
    """定時任務服務：生成回顧模板、彙整報告、分析對話。"""

    #region 成員變數
    ## <summary>應用程式設定</summary>
    m_Config: AppConfig
    ## <summary>Vault 根目錄</summary>
    m_VaultRoot: str
    #endregion

    def __init__( self, iConfig: AppConfig ):
        """
        初始化排程服務。

        Args:
            iConfig: 應用程式設定。
        """
        self.m_Config = iConfig
        self.m_VaultRoot = iConfig.vault_path

    @staticmethod
    def _validate_date( iDate: Optional[str] ) -> None:
        """
        驗證日期字串格式為 YYYY-MM-DD。

        Args:
            iDate: 日期字串（None 表示使用今天，不需驗證）。

        Raises:
            ValueError: 若格式不符。
        """
        if iDate is not None and not re.match( r'^\d{4}-\d{2}-\d{2}$', iDate ):
            raise ValueError( f"無效的日期格式：'{iDate}'。請使用 YYYY-MM-DD。" )

    #region 公開方法 — 專案每日進度
    def generate_project_daily( self, iOrg: str, iProject: str, iDate: Optional[str] = None ) -> str:
        """
        生成指定專案的每日詳細進度模板。
        冪等：已存在則回傳路徑不覆蓋。
        若 status.md 存在，會自動從待辦事項預填「今日計畫」區塊。

        Args:
            iOrg:     組織名稱（例如 'CHINESEGAMER'）。
            iProject: 專案名稱（例如 'game-server'）。
            iDate:    日期字串 YYYY-MM-DD（預設今天）。

        Returns:
            檔案的相對路徑（相對於 Vault 根目錄）。
        """
        self._validate_date( iDate )
        _Date = iDate or datetime.now().strftime( "%Y-%m-%d" )
        _DailyDir = self.m_Config.paths.project_daily_dir( iOrg, iProject )
        _RelPath = f"{_DailyDir}/{_Date}.md"
        _AbsPath = os.path.join( self.m_VaultRoot, _RelPath )

        if os.path.exists( _AbsPath ):
            return _RelPath

        # 嘗試從 status.md 讀取待辦事項
        _PendingTodos: list = []
        try:
            from services.vault import VaultService
            _StatusData, _StatusErr = VaultService.get_project_status( iOrg, iProject )
            if not _StatusErr and _StatusData:
                _PendingTodos = _StatusData.get( "pending_todos", [] )
        except Exception:
            pass  # status.md 不存在時降級為空模板

        _Content = self._render_project_daily_template( _Date, iOrg, iProject, _PendingTodos )
        self._sync_write( _RelPath, _Content )
        return _RelPath

    def generate_project_status( self, iOrg: str, iProject: str ) -> str:
        """
        生成指定專案的 status.md 模板（冪等：已存在則回傳路徑不覆蓋）。
        status.md 是 per-project 工作脈絡 + 待辦 + 決策記錄的唯一來源。

        Args:
            iOrg:     組織名稱（例如 'LIFEOFDEVELOPMENT'）。
            iProject: 專案名稱（例如 'ai-memory-vault'）。

        Returns:
            檔案的相對路徑（相對於 Vault 根目錄）。
        """
        _P = self.m_Config.paths
        _RelPath = _P.project_status_file( iOrg, iProject )
        _AbsPath = os.path.join( self.m_VaultRoot, _RelPath )

        if os.path.exists( _AbsPath ):
            return _RelPath

        _Today = datetime.now().strftime( "%Y.%m.%d" )
        _Content = self._render_project_status_template( iOrg, iProject, _Today )
        self._sync_write( _RelPath, _Content )
        return _RelPath
    #endregion

    #region 公開方法 — 總進度表
    def generate_daily_summary( self, iDate: Optional[str] = None, iProjects: list = None ) -> str:
        """
        生成每日總進度表（個人 personal/reviews/daily/ + _global 連結）。
        每次呼叫都會覆寫 personal 文本；_global 連結文件為冪等。

        Args:
            iDate:     日期字串 YYYY-MM-DD（預設今天）。
            iProjects: 各專案摘要列表，每項 dict 含 organization/project/summary 欄位（選填）。

        Returns:
            文本實體的相對路徑（personal/reviews/daily/{date}.md）。
        """
        self._validate_date( iDate )
        _Date = iDate or datetime.now().strftime( "%Y-%m-%d" )
        _P = self.m_Config.paths

        # Auto-digest：若未提供 iProjects，從今日對話自動填充
        _Conversations = self._scan_today_conversations( _Date )
        if iProjects is None and _Conversations:
            iProjects = []
            for _Key, _Files in _Conversations.items():
                _Parts    = _Key.split( "/", 1 )
                _Org      = _Parts[0] if len( _Parts ) >= 1 else ""
                _Proj     = _Parts[1] if len( _Parts ) >= 2 else ""
                _Sessions = [ _F[11:-3] for _F in _Files if len( _F ) > 14 ]
                iProjects.append( {
                    "organization": _Org,
                    "project":      _Proj,
                    "summary":      f"對話：{', '.join( _Sessions )}",
                } )

        # 文本實體：personal/reviews/daily/ — 永遠覆寫
        _PersonalRelPath = f"{_P.personal_reviews_daily}/{_Date}.md"
        _Content = self._render_daily_summary_template( _Date, iProjects, _Conversations )
        self._sync_write( _PersonalRelPath, _Content )

        # 連結文件：_global/reviews/daily/
        _GlobalRelPath = f"{_P.global_reviews_daily}/{_Date}.md"
        _GlobalAbsPath = os.path.join( self.m_VaultRoot, _GlobalRelPath )

        if not os.path.exists( _GlobalAbsPath ):
            _LinkContent = self._render_review_link( _Date, _PersonalRelPath, "每日總進度表" )
            self._sync_write( _GlobalRelPath, _LinkContent )

        return _PersonalRelPath

    def generate_weekly_summary( self, iDate: Optional[str] = None ) -> str:
        """
        生成每週總進度表（個人 personal/reviews/weekly/ + _global 連結）。
        冪等：已存在則回傳路徑不覆蓋。

        Args:
            iDate: 該週內的任一天 YYYY-MM-DD（預設今天）。

        Returns:
            文本實體的相對路徑。
        """
        self._validate_date( iDate )
        _Now = datetime.strptime( iDate, "%Y-%m-%d" ) if iDate else datetime.now()
        _Year, _Week, _ = _Now.isocalendar()
        _FileName = f"{_Year}-W{_Week:02d}.md"
        _P = self.m_Config.paths

        # 文本實體
        _PersonalRelPath = f"{_P.personal_reviews_weekly}/{_FileName}"

        # 文本實體：永遠覆寫
        _Monday = _Now - timedelta( days=_Now.weekday() )
        _WeekDays = [( _Monday + timedelta( days=i ) ).strftime( "%Y-%m-%d" ) for i in range( 7 )]
        _Content = self._render_weekly_summary_template( _Year, _Week, _WeekDays )
        self._sync_write( _PersonalRelPath, _Content )

        # 連結文件
        _GlobalRelPath = f"{_P.global_reviews_weekly}/{_FileName}"
        _GlobalAbsPath = os.path.join( self.m_VaultRoot, _GlobalRelPath )

        if not os.path.exists( _GlobalAbsPath ):
            _LinkContent = self._render_review_link(
                f"{_Year}-W{_Week:02d}", _PersonalRelPath, "每週總進度表"
            )
            self._sync_write( _GlobalRelPath, _LinkContent )

        return _PersonalRelPath

    def generate_monthly_summary( self, iDate: Optional[str] = None ) -> str:
        """
        生成每月總進度表（個人 personal/reviews/monthly/ + _global 連結）。
        冪等：已存在則回傳路徑不覆蓋。

        Args:
            iDate: 該月內的任一天 YYYY-MM-DD（預設今天）。

        Returns:
            文本實體的相對路徑。
        """
        self._validate_date( iDate )
        _Now = datetime.strptime( iDate, "%Y-%m-%d" ) if iDate else datetime.now()
        _YearMonth = _Now.strftime( "%Y-%m" )
        _FileName = f"{_YearMonth}.md"
        _P = self.m_Config.paths

        # 文本實體
        _PersonalRelPath = f"{_P.personal_reviews_monthly}/{_FileName}"

        # 文本實體：永遠覆寫
        _Content = self._render_monthly_summary_template( _YearMonth )
        self._sync_write( _PersonalRelPath, _Content )

        # 連結文件
        _GlobalRelPath = f"{_P.global_reviews_monthly}/{_FileName}"
        _GlobalAbsPath = os.path.join( self.m_VaultRoot, _GlobalRelPath )

        if not os.path.exists( _GlobalAbsPath ):
            _LinkContent = self._render_review_link(
                _YearMonth, _PersonalRelPath, "每月總進度表"
            )
            self._sync_write( _GlobalRelPath, _LinkContent )

        return _PersonalRelPath
    #endregion

    #region 公開方法 — AI 對話記錄
    def log_conversation(
        self,
        iOrg: str,
        iProject: str,
        iSessionName: str,
        iContent: str,
        iDetail: Optional[dict] = None,
    ) -> str:
        """
        記錄一次 AI 對話至指定專案的 conversations 目錄。
        若提供 iDetail，同時生成一份結構化詳細對話紀錄。

        Args:
            iOrg:         組織名稱（例如 'LIFEOFDEVELOPMENT'）。
            iProject:     專案名稱（例如 'ai-memory-vault'）。
            iSessionName: Session 名稱（例如 'vault-setup'）。
            iContent:     對話摘要內容（Markdown 格式）。
            iDetail:      （選填）結構化詳細紀錄，可包含以下欄位：
                          - topic (str):       對話主題
                          - qa_pairs (list):   關鍵問答 [{"question", "analysis", "decision", "alternatives"}]
                          - files_changed (list): 修改的檔案 [{"path", "action", "summary"}]
                          - commands (list):   執行的命令 [{"command", "purpose", "result"}]
                          - problems (list):   問題與解決 [{"problem", "cause", "solution"}]
                          - learnings (list):  學到的知識 (str 列表)
                          - decisions (list):  決策記錄 [{"decision", "options", "chosen", "reason"}]

        Returns:
            對話摘要檔案的相對路徑。若 iDetail 存在，詳細紀錄也一併寫入。
        """
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        _ConvDir = self.m_Config.paths.project_conversations_dir( iOrg, iProject )
        _RelPath = f"{_ConvDir}/{_Today}_{iSessionName}.md"

        self._sync_write( _RelPath, iContent )

        # 若提供結構化詳細紀錄，額外生成 detail 檔案
        if iDetail and isinstance( iDetail, dict ):
            _DetailRelPath = f"{_ConvDir}/{_Today}_{iSessionName}-detail.md"
            _DetailContent = self._render_conversation_detail(
                _Today, iOrg, iProject, iSessionName, iDetail
            )
            self._sync_write( _DetailRelPath, _DetailContent )

            # ── 自動 Instinct 學習管道 ──────────────────────
            self._auto_learn_instincts( iDetail, iOrg, iProject )

        return _RelPath

    def generate_ai_weekly_analysis( self, iDate: Optional[str] = None ) -> str:
        """
        生成 AI 對話每週分析模板。
        掃描所有專案的 conversations/ 目錄，彙整當週對話統計。
        冪等：已存在則回傳路徑不覆蓋。

        Args:
            iDate: 該週內的任一天 YYYY-MM-DD（預設今天）。

        Returns:
            檔案的相對路徑。
        """
        self._validate_date( iDate )
        _Now = datetime.strptime( iDate, "%Y-%m-%d" ) if iDate else datetime.now()
        _Year, _Week, _ = _Now.isocalendar()
        _FileName = f"{_Year}-W{_Week:02d}.md"
        _P = self.m_Config.paths

        _RelPath = f"{_P.ai_analysis_weekly}/{_FileName}"
        _AbsPath = os.path.join( self.m_VaultRoot, _RelPath )

        if os.path.exists( _AbsPath ):
            return _RelPath

        # 計算當週範圍
        _Monday = _Now - timedelta( days=_Now.weekday() )
        _Sunday = _Monday + timedelta( days=6 )
        _WeekStart = _Monday.strftime( "%Y-%m-%d" )
        _WeekEnd = _Sunday.strftime( "%Y-%m-%d" )

        # 掃描所有專案的 conversations
        _ProjectConvs = self._scan_all_project_conversations( _WeekStart, _WeekEnd )
        _TokenStats   = self._compute_token_stats( _ProjectConvs )
        _DetailMap    = self._parse_all_conversation_details( _ProjectConvs )
        _Metrics      = self._compute_analysis_metrics( _DetailMap, _TokenStats )

        _Content = self._render_ai_weekly_analysis_template(
            _Year, _Week, _WeekStart, _WeekEnd, _ProjectConvs, _TokenStats, _Metrics
        )
        self._sync_write( _RelPath, _Content )
        return _RelPath

    def generate_ai_monthly_analysis( self, iDate: Optional[str] = None ) -> str:
        """
        生成 AI 對話每月分析模板。
        掃描所有專案的 conversations/ 目錄 + 當月週報，彙整趨勢分析。
        冪等：已存在則回傳路徑不覆蓋。

        Args:
            iDate: 該月內的任一天 YYYY-MM-DD（預設今天）。

        Returns:
            檔案的相對路徑。
        """
        self._validate_date( iDate )
        _Now = datetime.strptime( iDate, "%Y-%m-%d" ) if iDate else datetime.now()
        _YearMonth = _Now.strftime( "%Y-%m" )
        _FileName = f"{_YearMonth}.md"
        _P = self.m_Config.paths

        _RelPath = f"{_P.ai_analysis_monthly}/{_FileName}"
        _AbsPath = os.path.join( self.m_VaultRoot, _RelPath )

        if os.path.exists( _AbsPath ):
            return _RelPath

        # 掃描當月所有專案對話
        _MonthStart = f"{_YearMonth}-01"
        _MonthEnd = f"{_YearMonth}-31"
        _ProjectConvs = self._scan_all_project_conversations( _MonthStart, _MonthEnd )

        # 掃描當月週報
        _WeeklyDir = os.path.join( self.m_VaultRoot, _P.ai_analysis_weekly )
        _WeeklyReports = []
        if os.path.exists( _WeeklyDir ):
            for _F in sorted( os.listdir( _WeeklyDir ) ):
                if _F.startswith( _YearMonth[:4] ) and _F.endswith( ".md" ):
                    _WeeklyReports.append( _F )

        _TokenStats   = self._compute_token_stats( _ProjectConvs )
        _DetailMap    = self._parse_all_conversation_details( _ProjectConvs )
        _Metrics      = self._compute_analysis_metrics( _DetailMap, _TokenStats )
        _Content = self._render_ai_monthly_analysis_template(
            _YearMonth, _ProjectConvs, _WeeklyReports, _TokenStats, _Metrics
        )
        self._sync_write( _RelPath, _Content )
        return _RelPath
    #endregion

    #region 公開方法 — 知識萃取
    def extract_knowledge(
        self,
        iOrg:     str,
        iProject: str,
        iTopic:   str,
        iSession: Optional[str] = None,
    ) -> str:
        """
        從指定專案的 conversations/ 萃取知識卡片（委派 KnowledgeExtractor）。

        Args:
            iOrg:     組織名稱。
            iProject: 專案名稱。
            iTopic:   知識主題（英文 slug）。
            iSession: 篩選特定 session 名稱（留空 = 全部）。

        Returns:
            知識卡片的相對路徑字串（失敗時為錯誤訊息字串）。
        """
        from services.knowledge_extractor import KnowledgeExtractor
        _Extractor = KnowledgeExtractor( self.m_Config )
        _Path, _Err = _Extractor.extract( iOrg, iProject, iTopic, iSession )
        if _Err:
            return _Err
        return _Path
    #endregion

    #region 私有方法 — 模板渲染（專案層級）
    def _render_project_daily_template( self, iDate: str, iOrg: str, iProject: str, iPendingTodos: list = None ) -> str:
        """渲染專案每日詳細進度模板。若待辦事項組已備，自動預填「今日計畫」區塊。"""
        _StatusRef = self.m_Config.paths.project_status_file( iOrg, iProject )

        # 「今日計畫」：從 status.md 待辦事項預填，或留空衬位
        if iPendingTodos:
            _PlanLines = "\n".join( f"- [ ] {_T}" for _T in iPendingTodos[:5] )
        else:
            _PlanLines = "- "

        return f"""---
type: project-daily
organization: {iOrg}
project: {iProject}
date: {iDate}
created: {iDate}
---

# 📝 {iProject} — 每日進度 {iDate}

> 專案狀態：[status.md]({_StatusRef})

## 今日計畫（來自 status.md）

{_PlanLines}

## 今日完成

- 

## 遇到的問題

- 

## 明日計畫

- 

## 筆記 / 學到的事

- 
"""

    def _render_project_status_template( self, iOrg: str, iProject: str, iToday: str ) -> str:
        """渲染專案狀態模板（status.md：工作脈絡 + 待辦 + 決策）。"""
        return f"""---
type: project-status
project: {iProject}
org: {iOrg}
last_updated: {iToday}
---

# 專案狀態 — {iProject}

## 工作脈絡

（尚未記錄工作脈絡）

## 待辦事項

### 進行中

- [ ] 

### 待處理

- [ ] 

### 已完成

（無）

## 重要決策

| 決策 | 原因 | 日期 |
|------|------|------|
|      |      |      |
"""
    #endregion

    #region 私有方法 — 模板渲染（總進度表）
    def _render_daily_summary_template( self, iDate: str, iProjects: list = None, iConversations: dict = None ) -> str:
        """渲染每日總進度表模板（跨所有專案的摘要）。"""
        _Header = "| 組織 | 專案 | 今日重點 |\n|------|------|---------|"
        if iProjects:
            _Rows = "\n".join(
                f"| {_P.get('organization', '')} | {_P.get('project', '')} | {_P.get('summary', '')} |"
                for _P in iProjects
            )
            _ProjectsTable = f"{_Header}\n{_Rows}"
        else:
            _ProjectsTable = f"{_Header}\n|      |      |         |"

        # 今日 AI 對話 digest
        if iConversations:
            _ConvLines = []
            for _Key, _Files in iConversations.items():
                _Parts   = _Key.split( "/", 1 )
                _Org     = _Parts[0] if len( _Parts ) >= 1 else ""
                _Proj    = _Parts[1] if len( _Parts ) >= 2 else ""
                _ConvDir = self.m_Config.paths.project_conversations_dir( _Org, _Proj )
                _Links   = ", ".join( f"[{_F}]({_ConvDir}/{_F})" for _F in _Files )
                _ConvLines.append( f"- **{_Key}**: {_Links}" )
            _ConvSection = "\n".join( _ConvLines )
        else:
            _ConvSection = "（今日尚無 AI 對話紀錄）"

        return f"""---
type: daily-summary
date: {iDate}
created: {iDate}
---

# 📅 每日總進度 — {iDate}

## 各專案重點

{_ProjectsTable}

## 今日 AI 對話

{_ConvSection}

## 今日總結

- 

## 明日優先事項

- 
"""

    def _render_weekly_summary_template( self, iYear: int, iWeek: int, iWeekDays: list ) -> str:
        """渲染每週總進度表模板。"""
        _P = self.m_Config.paths
        _DailyLinks = "\n".join(
            f"- [{_D}]({_P.personal_reviews_daily}/{_D}.md)" for _D in iWeekDays
        )
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        return f"""---
type: weekly-summary
date: {_Today}
created: {_Today}
week: {iYear}-W{iWeek:02d}
---

# 📊 每週總進度 — {iYear}-W{iWeek:02d}

## 本週 Daily 連結

{_DailyLinks}

## 本週目標達成

| 目標 | 狀態 | 備註 |
|------|------|------|
|      | ⬜   |      |

## 本週摘要

（彙整自各專案 daily 進度）

## 下週重點

- 

## 反思

- 
"""

    def _render_monthly_summary_template( self, iYearMonth: str ) -> str:
        """渲染每月總進度表模板。"""
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        return f"""---
type: monthly-summary
date: {_Today}
created: {_Today}
month: {iYearMonth}
---

# 📈 每月總進度 — {iYearMonth}

## 本月目標

| 目標 | 達成率 | 備註 |
|------|--------|------|
|      |        |      |

## Weekly Review 連結

（列出本月所有 weekly）

## 重大成果

- 

## 技術成長

- 

## 遇到的挑戰

- 

## 下月規劃

- 

## 反思 & 改進

- 
"""

    def _render_review_link( self, iLabel: str, iTargetPath: str, iTitle: str ) -> str:
        """渲染 _global/reviews/ 的連結文件（指向 personal/reviews/ 的實體）。"""
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        return f"""---
type: review-link
date: {_Today}
target: {iTargetPath}
---

# 🔗 {iTitle} — {iLabel}

→ [{iTitle}](../../{iTargetPath})
"""
    #endregion

    #region 私有方法 — 模板渲染（AI 分析）
    def _scan_all_project_conversations( self, iStartDate: str, iEndDate: str ) -> dict:
        """
        掃描所有組織/專案的 conversations/ 目錄，回傳日期範圍內的對話清單。

        Args:
            iStartDate: 起始日期 YYYY-MM-DD（含）。
            iEndDate:   結束日期 YYYY-MM-DD（含）。

        Returns:
            { "{org}/{project}": [filename, ...], ... }
        """
        _P = self.m_Config.paths
        _WsRoot = os.path.join( self.m_VaultRoot, _P.workspaces )
        _Result = {}

        if not os.path.exists( _WsRoot ):
            return _Result

        try:
            _OrgEntries = sorted( os.listdir( _WsRoot ) )
        except PermissionError as _Ex:
            print( f"[SchedulerService] Cannot read workspaces dir: {_Ex}", file=sys.stderr )
            return _Result

        for _OrgName in _OrgEntries:
            _ProjRoot = os.path.join( _WsRoot, _OrgName, _P.org_projects )
            if not os.path.isdir( _ProjRoot ):
                continue
            try:
                _ProjEntries = sorted( os.listdir( _ProjRoot ) )
            except PermissionError as _Ex:
                print( f"[SchedulerService] Cannot read projects dir ({_OrgName}): {_Ex}", file=sys.stderr )
                continue
            for _ProjName in _ProjEntries:
                _ConvDir = os.path.join( _ProjRoot, _ProjName, _P.proj_conversations )
                if not os.path.isdir( _ConvDir ):
                    continue
                try:
                    _ConvEntries = sorted( os.listdir( _ConvDir ) )
                except PermissionError as _Ex:
                    print( f"[SchedulerService] Cannot read conversations dir ({_OrgName}/{_ProjName}): {_Ex}", file=sys.stderr )
                    continue
                _Files = []
                for _F in _ConvEntries:
                    if not _F.endswith( ".md" ):
                        continue
                    # 檔名格式: {YYYY-MM-DD}_{session}.md — 取前 10 字比對日期
                    _FileDate = _F[:10]
                    if iStartDate <= _FileDate <= iEndDate:
                        _Files.append( _F )
                if _Files:
                    _Result[f"{_OrgName}/{_ProjName}"] = _Files

        return _Result

    def _scan_today_conversations( self, iDate: str ) -> dict:
        """
        掃描所有專案指定日期的 conversations/ 目錄。
        薄封裝層：將 _scan_all_project_conversations 限定為單日範圍。

        Args:
            iDate: 日期字串 YYYY-MM-DD。

        Returns:
            { "{org}/{project}": [filename, ...], ... }
        """
        return self._scan_all_project_conversations( iDate, iDate )

    def _compute_token_stats( self, iProjectConvs: dict ) -> dict:
        """
        計算各專案對話檔案的估算 token 統計。

        Args:
            iProjectConvs: { "{org}/{project}": [filename, ...], ... }

        Returns:
            { "{org}/{project}": token_count, ... } 對應估算 token 總數。
        """
        from services.token_counter import TokenCounter
        _P = self.m_Config.paths
        _Stats: dict = {}

        for _Key, _Files in iProjectConvs.items():
            _Parts = _Key.split( "/", 1 )
            _Org   = _Parts[0]
            _Proj  = _Parts[1] if len( _Parts ) > 1 else ""
            _ConvDir = os.path.join(
                self.m_VaultRoot,
                _P.project_conversations_dir( _Org, _Proj ),
            )
            _Total = 0
            for _F in _Files:
                _Total += TokenCounter.count_file( os.path.join( _ConvDir, _F ) )
            _Stats[_Key] = _Total

        return _Stats

    def _parse_all_conversation_details( self, iProjectConvs: dict ) -> dict:
        """
        解析所有 detail 檔案，萃取結構化資料。

        Args:
            iProjectConvs: { "{org}/{project}": [filename, ...], ... }

        Returns:
            {
                "{org}/{project}": [
                    {
                        "session":            str,
                        "qa_count":           int,
                        "problems":           [{ problem, cause, solution }],
                        "learnings":          [str],
                        "interaction_issues": [{ type, description }],
                        "tokens":             int,
                    },
                    ...
                ],
                ...
            }
        """
        from services.token_counter import TokenCounter
        _P      = self.m_Config.paths
        _Result = {}

        for _Key, _Files in iProjectConvs.items():
            _Parts   = _Key.split( "/", 1 )
            _Org     = _Parts[0]
            _Proj    = _Parts[1] if len( _Parts ) > 1 else ""
            _ConvDir = os.path.join( self.m_VaultRoot, _P.project_conversations_dir( _Org, _Proj ) )
            _Details = []

            for _F in _Files:
                # 只處理非 detail 的主檔，再去找同名 detail
                if _F.endswith( "-detail.md" ):
                    continue

                _Session = _F[11:].replace( ".md", "" )  # 去掉 YYYY-MM-DD_ 和 .md
                _MainTokens  = TokenCounter.count_file( os.path.join( _ConvDir, _F ) )
                _DetailFname = _F.replace( ".md", "-detail.md" )
                _DetailPath  = os.path.join( _ConvDir, _DetailFname )

                _Entry = {
                    "session":            _Session,
                    "qa_count":           0,
                    "problems":           [],
                    "learnings":          [],
                    "interaction_issues": [],
                    "tokens":             _MainTokens,
                }

                if os.path.exists( _DetailPath ):
                    _Entry["tokens"] += TokenCounter.count_file( _DetailPath )
                    self._extract_detail_data( _DetailPath, _Entry )

                _Details.append( _Entry )

            if _Details:
                _Result[_Key] = _Details

        return _Result

    def _extract_detail_data( self, iDetailPath: str, oEntry: dict ) -> None:
        """
        從 detail .md 檔中解析問答數、problems、learnings、interaction_issues。
        使用 Markdown 結構（標題 + 表格 + 列表）解析，不依賴 frontmatter。

        Args:
            iDetailPath: detail 檔案的絕對路徑。
            oEntry:      輸出 dict（直接修改）。
        """
        try:
            with open( iDetailPath, "r", encoding="utf-8" ) as _F:
                _Lines = _F.readlines()
        except OSError:
            return

        _Section  = ""
        _QaCount  = 0

        for _Line in _Lines:
            _Stripped = _Line.strip()

            # 追蹤當前 section（## 標題）
            if _Stripped.startswith( "## " ):
                _Section = _Stripped[3:].strip().lower()
                continue
            if _Stripped.startswith( "### " ):
                # ### Q1: ... → 計算問答數
                if _Stripped.startswith( "### Q" ) and ":" in _Stripped:
                    _QaCount += 1
                continue

            # 「學到的知識」列表
            if "學到" in _Section and _Stripped.startswith( "- " ):
                _Text = _Stripped[2:].strip()
                if _Text:
                    oEntry["learnings"].append( _Text )
                continue

            # 「遇到的問題」表格行（| problem | cause | solution |）
            if "問題" in _Section and _Stripped.startswith( "| " ) and not _Stripped.startswith( "| 問題" ) and not _Stripped.startswith( "|---" ):
                _Cols = [ _C.strip() for _C in _Stripped.strip( "| " ).split( "|" ) ]
                if len( _Cols ) >= 3 and _Cols[0]:
                    oEntry["problems"].append( {
                        "problem":  _Cols[0].strip(),
                        "cause":    _Cols[1].strip() if len( _Cols ) > 1 else "",
                        "solution": _Cols[2].strip() if len( _Cols ) > 2 else "",
                    } )
                continue

            # interaction_issues 表格行（如未來 detail 加入此表格）
            if "interaction" in _Section.lower() and _Stripped.startswith( "| " ) and not _Stripped.startswith( "| type" ) and not _Stripped.startswith( "|---" ):
                _Cols = [ _C.strip() for _C in _Stripped.strip( "| " ).split( "|" ) ]
                if len( _Cols ) >= 2 and _Cols[0]:
                    oEntry["interaction_issues"].append( {
                        "type":        _Cols[0].strip(),
                        "description": _Cols[1].strip() if len( _Cols ) > 1 else "",
                    } )
                continue

        oEntry["qa_count"] = _QaCount

    def _compute_analysis_metrics( self, iDetailMap: dict, iTokenStats: dict ) -> dict:
        """
        從 detail 解析結果計算分析指標。

        Args:
            iDetailMap:  _parse_all_conversation_details() 的回傳值。
            iTokenStats: _compute_token_stats() 的回傳值。

        Returns:
            {
                "total_convs":       int,
                "total_qa":          int,
                "avg_qa_per_conv":   float,
                "total_problems":    int,
                "total_learnings":   int,
                "success_rate":      float,   # 0~100
                "top_consumers":     [{ "session": str, "project": str, "tokens": int }],
                "error_patterns":    { "pattern": count },
                "all_learnings":     [str],
                "all_problems":      [{ problem, cause, solution, project }],
                "scores":            { dim: score },
                "per_project": {
                    "{org}/{project}": {
                        "conv_count":    int,
                        "success_rate":  float,
                        "tokens":        int,
                    }
                }
            }
        """
        from services.token_counter import TokenCounter

        _TotalConvs      = 0
        _TotalQa         = 0
        _ConvsWithQa     = 0   # 有 QA 記錄的對話數（用於計算有意義的平均輪數）
        _TotalProblems   = 0
        _SolvedProblems  = 0   # 有 solution 的 problems
        _ConvsNoProblems = 0
        _AllLearnings    = []
        _AllProblems     = []
        _AllConsumers    = []
        _ErrorDetails    = []  # [{ problem, cause, solution, count }]
        _PerProject      = {}

        for _Key, _Details in iDetailMap.items():
            _ProjConvs   = len( _Details )
            _ProjNoProb  = 0
            _ProjTokens  = iTokenStats.get( _Key, 0 )

            for _D in _Details:
                _TotalConvs += 1
                _QaCount = _D["qa_count"]
                _TotalQa += _QaCount
                if _QaCount > 0:
                    _ConvsWithQa += 1
                _Probs = _D["problems"]
                _TotalProblems += len( _Probs )

                if not _Probs:
                    _ConvsNoProblems += 1
                    _ProjNoProb      += 1

                _AllLearnings.extend( _D["learnings"] )
                for _P in _Probs:
                    _P["project"] = _Key
                    _AllProblems.append( _P )
                    if _P.get( "solution", "" ).strip():
                        _SolvedProblems += 1
                    _ErrorDetails.append( {
                        "problem":  _P.get( "problem", "" ),
                        "cause":    _P.get( "cause", "" ),
                        "solution": _P.get( "solution", "" ),
                    } )

                _AllConsumers.append( {
                    "session": _D["session"],
                    "project": _Key,
                    "tokens":  _D["tokens"],
                } )

            _PerProject[_Key] = {
                "conv_count":   _ProjConvs,
                "success_rate": ( _ProjNoProb / _ProjConvs * 100 ) if _ProjConvs else 0,
                "tokens":       _ProjTokens,
            }

        _SuccessRate = ( _ConvsNoProblems / _TotalConvs * 100 ) if _TotalConvs else 100
        # 平均 QA 只算有 QA 資料的對話（避免無 detail 的對話把平均拉低）
        _AvgQa = ( _TotalQa / _ConvsWithQa ) if _ConvsWithQa else 0

        # Top 3 高消耗
        _AllConsumers.sort( key=lambda x: x["tokens"], reverse=True )
        _TopConsumers = _AllConsumers[:3]

        # 自動評分
        _SolveRate = ( _SolvedProblems / _TotalProblems * 100 ) if _TotalProblems else 100
        _Scores = self._auto_score(
            _SuccessRate, _AvgQa, _TotalProblems, _TotalConvs,
            _AllLearnings, _SolveRate, _ConvsWithQa,
        )

        return {
            "total_convs":       _TotalConvs,
            "total_qa":          _TotalQa,
            "convs_with_qa":     _ConvsWithQa,
            "avg_qa_per_conv":   round( _AvgQa, 1 ),
            "total_problems":    _TotalProblems,
            "solved_problems":   _SolvedProblems,
            "solve_rate":        round( _SolveRate, 1 ),
            "total_learnings":   len( _AllLearnings ),
            "success_rate":      round( _SuccessRate, 1 ),
            "top_consumers":     _TopConsumers,
            "error_details":     _ErrorDetails,
            "all_learnings":     _AllLearnings,
            "all_problems":      _AllProblems,
            "scores":            _Scores,
            "per_project":       _PerProject,
        }

    @staticmethod
    def _auto_score(
        iSuccessRate: float, iAvgQa: float, iTotalProblems: int, iTotalConvs: int,
        iLearnings: list, iSolveRate: float = 100.0, iConvsWithQa: int = 0,
    ) -> dict:
        """
        根據指標自動產出 1-5 評分。

        Args:
            iSuccessRate: 無問題對話比率 (0-100)。
            iAvgQa:       有 QA 記錄的對話之平均 QA 輪數。
            iTotalProblems: 問題總數。
            iTotalConvs:   對話總數。
            iLearnings:    學習清單。
            iSolveRate:    有解法的問題比率 (0-100)。
            iConvsWithQa:  有 QA 記錄的對話數（0 = 無 QA 資料）。

        Returns:
            { "溝通效率": int, "輸出品質": int, "問題解決率": int, "Prompt 技巧": int }
        """
        # 溝通效率：基於 success_rate（無問題的對話佔比）
        if iSuccessRate >= 85:   _CommScore = 5
        elif iSuccessRate >= 70: _CommScore = 4
        elif iSuccessRate >= 50: _CommScore = 3
        elif iSuccessRate >= 30: _CommScore = 2
        else:                    _CommScore = 1

        # 輸出品質：基於 problems/conversation 比率（越低越好）
        _ProbRate = ( iTotalProblems / iTotalConvs ) if iTotalConvs else 0
        if _ProbRate <= 0.3:    _QualScore = 5
        elif _ProbRate <= 0.7:  _QualScore = 4
        elif _ProbRate <= 1.5:  _QualScore = 3
        elif _ProbRate <= 2.5:  _QualScore = 2
        else:                   _QualScore = 1

        # 問題解決率：基於「有解法的 problem / 總 problem」
        if iTotalProblems == 0:
            _SolveScore = 5
        elif iSolveRate >= 90:  _SolveScore = 5
        elif iSolveRate >= 70: _SolveScore = 4
        elif iSolveRate >= 50: _SolveScore = 3
        elif iSolveRate >= 30: _SolveScore = 2
        else:                  _SolveScore = 1

        # Prompt 技巧：基於平均 QA 輪數（越少 = prompt 越精準）和 learnings 數量
        # 無 QA 資料時用中間值 3
        if iConvsWithQa == 0:
            _PromptScore = 3
        else:
            if iAvgQa <= 2.0:     _PromptScore = 5
            elif iAvgQa <= 4.0:   _PromptScore = 4
            elif iAvgQa <= 6.0:   _PromptScore = 3
            elif iAvgQa <= 9.0:   _PromptScore = 2
            else:                  _PromptScore = 1
        _LearningBonus = min( 1, len( iLearnings ) // 5 )
        _PromptScore = min( 5, _PromptScore + _LearningBonus )

        return {
            "溝通效率":     _CommScore,
            "輸出品質":     _QualScore,
            "問題解決率":   _SolveScore,
            "Prompt 技巧": _PromptScore,
        }

    def _render_ai_weekly_analysis_template(
        self, iYear: int, iWeek: int, iWeekStart: str, iWeekEnd: str,
        iProjectConvs: dict, iTokenStats: dict = None, iMetrics: dict = None
    ) -> str:
        """渲染 AI 對話每週分析模板。"""
        from services.token_counter import TokenCounter
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        _P = self.m_Config.paths
        _TokenStatsMap = iTokenStats or {}
        _TotalTokens = sum( _TokenStatsMap.values() )
        _M = iMetrics or {}

        # 使用 metrics 的正確對話數（排除 detail 檔）
        _TotalConvs  = _M.get( "total_convs", sum( len( _V ) for _V in iProjectConvs.values() ) )
        _AvgQa       = _M.get( "avg_qa_per_conv", 0 )
        _ConvsWithQa = _M.get( "convs_with_qa", 0 )
        _SuccessRate = _M.get( "success_rate", 0 )
        _SolveRate   = _M.get( "solve_rate", 0 )
        _Scores      = _M.get( "scores", {} )

        # 平均輪數顯示：無 QA 資料時不顯示數字
        _AvgQaDisplay = f"{_AvgQa}" if _ConvsWithQa > 0 else "—（尚無 detail 記錄）"

        # 各專案統計表（排除 detail 檔名）
        _ProjRows = ""
        for _Key, _Files in iProjectConvs.items():
            _MainFiles = [ _F for _F in _Files if not _F.endswith( "-detail.md" ) ]
            _Org, _Proj = _Key.split( "/" )
            _ConvDir = _P.project_conversations_dir( _Org, _Proj )
            _Links = ", ".join( f"[{_F}]({_ConvDir}/{_F})" for _F in _MainFiles )
            _ProjRows += f"| {_Org} | {_Proj} | {len( _MainFiles )} | {_Links} |\n"

        if not _ProjRows:
            _ProjRows = "| （本週尚無對話紀錄） | | | |\n"

        # Token 消耗表（單欄合計，不分 input/output）
        _TokenRows = ""
        for _Key, _Toks in _TokenStatsMap.items():
            _TokenRows += f"| {_Key} | {TokenCounter.format_k( _Toks )} |\n"
        if not _TokenRows:
            _TokenRows = "| （無資料） | |\n"

        _TotalTokenFmt = TokenCounter.format_k( _TotalTokens ) if _TotalTokens else "—"

        # 高消耗對話
        _TopConsumers = _M.get( "top_consumers", [] )
        _TopConsumerLines = ""
        for _TC in _TopConsumers:
            _TopConsumerLines += f"- **{_TC['session']}**（{_TC['project']}）— {TokenCounter.format_k( _TC['tokens'] )} tokens\n"
        if not _TopConsumerLines:
            _TopConsumerLines = "- （本週無特別高消耗對話）\n"

        # 錯誤模式表（帶根本原因與改進方式）
        _ErrorDetails = _M.get( "error_details", [] )
        _ErrorRows = ""
        _Seen = set()
        for _ED in _ErrorDetails:
            _Prob = _ED["problem"][:30]
            if _Prob in _Seen:
                continue
            _Seen.add( _Prob )
            _Cause = _ED.get( "cause", "" )[:30] or "—"
            _Sol   = _ED.get( "solution", "" )[:30] or "—"
            _Cnt   = sum( 1 for _X in _ErrorDetails if _X["problem"][:30] == _Prob )
            _ErrorRows += f"| {_Prob} | {_Cnt} | {_Cause} | {_Sol} |\n"
            if len( _Seen ) >= 5:
                break
        if not _ErrorRows:
            _ErrorRows = "| （本週無明顯錯誤模式） | | | |\n"

        # 成功的對話模式
        _SuccessConvLines = ""
        if _TotalConvs > 0:
            _SuccessConvLines = f"- 本週 {_TotalConvs} 次對話中 **{_SuccessRate}%** 無需重試即完成\n"
            if _M.get( "total_problems", 0 ):
                _SuccessConvLines += f"- 共 {_M['total_problems']} 個問題，{_SolveRate}% 有明確解法\n"
        if not _SuccessConvLines:
            _SuccessConvLines = "- （無足夠資料分析）\n"

        # 評分與說明
        _ScoreDimensions = {
            "溝通效率":     "意圖傳達精準度",
            "輸出品質":     "輸出正確性與可用性",
            "問題解決率":   "問題解決效率",
            "Prompt 技巧": "指令精準度與效率",
        }
        _ScoreRows = ""
        for _Dim, _Desc in _ScoreDimensions.items():
            _Val = _Scores.get( _Dim, 0 )
            _Stars = "★" * _Val + "☆" * ( 5 - _Val )
            _ScoreRows += f"| {_Dim} | {_Stars} ({_Val}/5) | {_Desc} |\n"

        # 學到的東西
        _Learnings = _M.get( "all_learnings", [] )
        _LearningLines = ""
        for _L in _Learnings[:8]:
            _LearningLines += f"- {_L}\n"
        if not _LearningLines:
            _LearningLines = "- （本週未記錄特別收穫）\n"

        # 改進目標
        _ImprovementLines = ""
        _SeenProbs = set()
        for _ED in _ErrorDetails[:3]:
            _Prob = _ED["problem"][:30]
            if _Prob not in _SeenProbs:
                _SeenProbs.add( _Prob )
                _ImprovementLines += f"- 減少「{_Prob}」類問題\n"
        if _AvgQa > 3 and _ConvsWithQa > 0:
            _ImprovementLines += "- 嘗試更精確的 Prompt 以減少平均輪數\n"
        if not _ImprovementLines:
            _ImprovementLines = "- 維持目前品質水準\n"

        # Token 節省建議
        _TokenTips = ""
        if _TopConsumers:
            _TokenTips += "- 高消耗對話可嘗試分拆為多次小型對話\n"
        if _AvgQa > 5:
            _TokenTips += "- 提供更完整的上下文以減少來回輪數\n"
        if not _TokenTips:
            _TokenTips = "- 目前 Token 使用效率良好\n"

        return f"""---
type: ai-analysis-weekly
date: {_Today}
created: {_Today}
week: {iYear}-W{iWeek:02d}
period: {iWeekStart} ~ {iWeekEnd}
---

# 🤖 AI 對話週報 — {iYear}-W{iWeek:02d}

> 分析期間：{iWeekStart} ~ {iWeekEnd}

## 統計摘要

| 指標 | 數值 |
|------|------|
| 對話總數 | {_TotalConvs} |
| 涉及專案數 | {len( iProjectConvs )} |
| 平均每日對話數 | {_TotalConvs / 7:.1f} |
| 平均輪數（人→AI） | {_AvgQaDisplay} |
| 一次成功率 | {_SuccessRate}% |
| 估計 Token 消耗 | {_TotalTokenFmt} |

## 各專案對話明細

| 組織 | 專案 | 對話數 | 對話列表 |
|------|------|--------|---------|
{_ProjRows}
## 對話準確率分析

### 成功的對話模式

{_SuccessConvLines}
### 常見錯誤 / 需重試的情境

| 錯誤模式 | 出現次數 | 根本原因 | 改進方式 |
|---------|---------|---------|---------|
{_ErrorRows}
## Token 消耗分析

| 專案 | 預估 Token |
|------|----------|
{_TokenRows}
### 高消耗對話

{_TopConsumerLines}
### 節省 Token 的方式

{_TokenTips}
## 本週評分

| 維度 | 評分 (1-5) | 說明 |
|------|-----------|------|
{_ScoreRows}
## Prompt 技巧收穫

{_LearningLines}
## 下週改進目標

{_ImprovementLines}
"""

    def _render_ai_monthly_analysis_template(
        self, iYearMonth: str, iProjectConvs: dict, iWeeklyReports: list,
        iTokenStats: dict = None, iMetrics: dict = None
    ) -> str:
        """渲染 AI 對話每月分析模板。"""
        from services.token_counter import TokenCounter
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        _P = self.m_Config.paths
        _TokenStatsMap = iTokenStats or {}
        _TotalTokens = sum( _TokenStatsMap.values() )
        _M = iMetrics or {}
        _Scores      = _M.get( "scores", {} )
        _SuccessRate = _M.get( "success_rate", 0 )
        _PerProject  = _M.get( "per_project", {} )

        # 使用 metrics 的正確對話數（排除 detail 檔）
        _TotalConvs = _M.get( "total_convs", sum( len( _V ) for _V in iProjectConvs.values() ) )

        # 各專案月度統計（排除 detail 檔名）
        _ProjRows = ""
        for _Key, _Files in iProjectConvs.items():
            _MainCount = sum( 1 for _F in _Files if not _F.endswith( "-detail.md" ) )
            _TokFmt = TokenCounter.format_k( _TokenStatsMap.get( _Key, 0 ) )
            _ProjSR = _PerProject.get( _Key, {} ).get( "success_rate", 0 )
            _ProjRows += f"| {_Key} | {_MainCount} | {_ProjSR:.0f}% | {_TokFmt} |\n"

        if not _ProjRows:
            _ProjRows = "| （本月尚無對話紀錄） | | | |\n"

        # 週報連結 + 嘗試解析週報裡的評分（從檔名不用解析內容，直接用 _Metrics）
        _WeeklyLinks = "\n".join(
            f"- [{_F}]({_P.ai_analysis_weekly}/{_F})" for _F in iWeeklyReports
        ) if iWeeklyReports else "（本月尚無週報）"

        _TotalTokenFmt = TokenCounter.format_k( _TotalTokens ) if _TotalTokens else "—"

        # 週趨勢表 — 嘗試從週報檔案提取數據
        _WeekTrendRows = ""
        for _WF in iWeeklyReports:
            _WPath = os.path.join( self.m_VaultRoot, _P.ai_analysis_weekly, _WF )
            _WData = self._extract_weekly_summary( _WPath )
            _WeekLabel = _WF.replace( ".md", "" )
            _WeekTrendRows += (
                f"| {_WeekLabel} | {_WData['convs']} | {_WData['success_rate']} | "
                f"{_WData['tokens']} | {_WData['change']} |\n"
            )
        if not _WeekTrendRows:
            _WeekTrendRows = "| （無週報資料） | | | | |\n"

        # 評分行
        _ScoreDimensions = [ "溝通效率", "輸出品質", "問題解決率", "Prompt 技巧" ]
        _ScoreRows = ""
        for _Dim in _ScoreDimensions:
            _Val = _Scores.get( _Dim, 0 )
            _Stars = "★" * _Val + "☆" * ( 5 - _Val )
            _ScoreRows += f"| {_Dim} | {_Stars} ({_Val}/5) | — | — |\n"
        # Token 效率（基於每次對話平均 token）
        _AvgTokenPerConv = ( _TotalTokens // _TotalConvs ) if _TotalConvs else 0
        if _AvgTokenPerConv <= 500:     _TokenEffScore = 5
        elif _AvgTokenPerConv <= 1500:  _TokenEffScore = 4
        elif _AvgTokenPerConv <= 3000:  _TokenEffScore = 3
        elif _AvgTokenPerConv <= 5000:  _TokenEffScore = 2
        else:                           _TokenEffScore = 1
        _Stars = "★" * _TokenEffScore + "☆" * ( 5 - _TokenEffScore )
        _ScoreRows += f"| Token 效率 | {_Stars} ({_TokenEffScore}/5) | — | — |\n"

        # 主要收穫
        _Learnings = _M.get( "all_learnings", [] )
        _LearningLines = ""
        for _L in _Learnings[:10]:
            _LearningLines += f"- {_L}\n"
        if not _LearningLines:
            _LearningLines = "- （本月未記錄特別收穫）\n"

        # 優化建議
        _ErrorDetails = _M.get( "error_details", [] )
        _OptPrompt = ""
        _SeenOpt = set()
        for _ED in _ErrorDetails[:2]:
            _Prob = _ED["problem"][:30]
            if _Prob not in _SeenOpt:
                _SeenOpt.add( _Prob )
                _OptPrompt += f"- 針對「{_Prob}」類問題改善 Prompt 描述\n"
        if not _OptPrompt:
            _OptPrompt = "- 維持目前 Prompt 品質\n"

        _OptWorkflow = ""
        _AvgQa = _M.get( "avg_qa_per_conv", 0 )
        _ConvsWithQa = _M.get( "convs_with_qa", 0 )
        if _AvgQa > 5 and _ConvsWithQa > 0:
            _OptWorkflow += "- 嘗試拆分大型任務為多個小對話\n"
        if _TotalConvs > 30:
            _OptWorkflow += "- 考慮彙整常用操作為自動化腳本\n"
        if not _OptWorkflow:
            _OptWorkflow = "- 目前工作流程效率良好\n"

        # 改進計畫
        _ImprovementLines = ""
        _SeenImp = set()
        for _ED in _ErrorDetails[:3]:
            _Prob = _ED["problem"][:30]
            if _Prob not in _SeenImp:
                _SeenImp.add( _Prob )
                _ImprovementLines += f"- 減少「{_Prob}」類問題\n"
        if _AvgQa > 3 and _ConvsWithQa > 0:
            _ImprovementLines += "- 持續優化 Prompt 精準度\n"
        if not _ImprovementLines:
            _ImprovementLines = "- 維持目前品質水準\n"

        # 反思
        _ReflectLines = ""
        if _SuccessRate >= 80:
            _ReflectLines += f"- 本月一次成功率 {_SuccessRate:.0f}%，整體表現良好\n"
        else:
            _ReflectLines += f"- 本月一次成功率 {_SuccessRate:.0f}%，需關注常見失敗模式\n"
        if _Learnings:
            _ReflectLines += f"- 累積 {len( _Learnings )} 項學習筆記，知識沉澱持續進行\n"

        return f"""---
type: ai-analysis-monthly
date: {_Today}
created: {_Today}
month: {iYearMonth}
---

# 🤖 AI 對話月報 — {iYearMonth}

## 月度統計

| 指標 | 數值 |
|------|------|
| 對話總數 | {_TotalConvs} |
| 涉及專案數 | {len( iProjectConvs )} |
| 平均每週對話數 | {_TotalConvs / 4:.1f} |
| 月度一次成功率 | {_SuccessRate:.0f}% |
| 月度 Token 總消耗 | {_TotalTokenFmt} |

## 各專案月度對話統計

| 組織/專案 | 對話數 | 一次成功率 | 預估 Token |
|----------|--------|----------|-----------|
{_ProjRows}
## 週報彙整

{_WeeklyLinks}

## 趨勢分析

### 對話效率趨勢

| 週次 | 對話數 | 成功率 | Token 消耗 | 變化 |
|------|--------|--------|-----------|------|
{_WeekTrendRows}
### 效率變化

- 本月平均 QA 輪數：{_AvgQa}
- 本月一次成功率：{_SuccessRate:.0f}%

## 優化建議

### Prompt 優化

{_OptPrompt}
### 工作流程優化

{_OptWorkflow}
### 工具使用優化

- 善用 detail 結構化記錄提升追蹤品質

## 月度評分

| 維度 | 評分 (1-5) | 上月 | 變化 |
|------|-----------|------|------|
{_ScoreRows}
## 主要收穫

{_LearningLines}
## 下月改進計畫

{_ImprovementLines}
## 反思

{_ReflectLines}
"""

    def _extract_weekly_summary( self, iWeeklyPath: str ) -> dict:
        """
        從已生成的週報 .md 提取「對話總數」「一次成功率」「Token 消耗」。

        Returns:
            { "convs": str, "success_rate": str, "tokens": str, "change": str }
        """
        _Default = { "convs": "—", "success_rate": "—", "tokens": "—", "change": "—" }
        try:
            with open( iWeeklyPath, "r", encoding="utf-8" ) as _F:
                _Lines = _F.readlines()
        except OSError:
            return _Default

        _Convs       = "—"
        _SuccessRate = "—"
        _Tokens      = "—"

        for _Line in _Lines:
            _Stripped = _Line.strip()
            if "| 對話總數" in _Stripped:
                _Parts = [ _C.strip() for _C in _Stripped.split( "|" ) ]
                if len( _Parts ) >= 3:
                    _Convs = _Parts[2]
            elif "| 一次成功率" in _Stripped:
                _Parts = [ _C.strip() for _C in _Stripped.split( "|" ) ]
                if len( _Parts ) >= 3:
                    _SuccessRate = _Parts[2]
            elif "| 估計 Token" in _Stripped or "| Token" in _Stripped:
                _Parts = [ _C.strip() for _C in _Stripped.split( "|" ) ]
                if len( _Parts ) >= 3:
                    _Tokens = _Parts[2]

        return { "convs": _Convs, "success_rate": _SuccessRate, "tokens": _Tokens, "change": "—" }
    #endregion

    #region 私有方法 — 對話詳細紀錄渲染
    @staticmethod
    def _render_conversation_detail(
        iDate: str, iOrg: str, iProject: str, iSession: str, iDetail: dict
    ) -> str:
        """渲染結構化對話詳細紀錄。"""
        _Topic = iDetail.get( "topic", iSession )

        _Lines = [
            "---",
            "type: conversation-detail",
            f"date: {iDate}",
            f"session: {iSession}",
            f"project: {iProject}",
            f"org: {iOrg}",
            "tags: [conversation, detail]",
            "---",
            "",
            f"# {iDate} {iSession} — 詳細對話紀錄",
            "",
            "## 對話概要",
            f"- **主題**：{_Topic}",
            "",
        ]

        # 關鍵問答
        _QaPairs = iDetail.get( "qa_pairs", [] )
        if _QaPairs:
            _Lines.append( "## 關鍵問答紀錄" )
            _Lines.append( "" )
            for _I, _Qa in enumerate( _QaPairs, 1 ):
                _Lines.append( f"### Q{_I}: {_Qa.get( 'question', '' )}" )
                if _Qa.get( "analysis" ):
                    _Lines.append( f"- **AI 分析**：{_Qa['analysis']}" )
                if _Qa.get( "decision" ):
                    _Lines.append( f"- **決策**：{_Qa['decision']}" )
                if _Qa.get( "alternatives" ):
                    _Lines.append( f"- **替代方案**：{_Qa['alternatives']}" )
                _Lines.append( "" )

        # 修改的檔案
        _Files = iDetail.get( "files_changed", [] )
        if _Files:
            _Lines.append( "## 修改的檔案清單" )
            _Lines.append( "" )
            _Lines.append( "| 檔案 | 操作 | 摘要 |" )
            _Lines.append( "|------|------|------|" )
            for _F in _Files:
                _Lines.append(
                    f"| `{_F.get( 'path', '' )}` | {_F.get( 'action', '' )} | {_F.get( 'summary', '' )} |"
                )
            _Lines.append( "" )

        # 執行的命令
        _Cmds = iDetail.get( "commands", [] )
        if _Cmds:
            _Lines.append( "## 執行的命令" )
            _Lines.append( "" )
            _Lines.append( "| 命令 | 目的 | 結果 |" )
            _Lines.append( "|------|------|------|" )
            for _C in _Cmds:
                _Lines.append(
                    f"| `{_C.get( 'command', '' )}` | {_C.get( 'purpose', '' )} | {_C.get( 'result', '' )} |"
                )
            _Lines.append( "" )

        # 問題與解決
        _Problems = iDetail.get( "problems", [] )
        if _Problems:
            _Lines.append( "## 遇到的問題與解決" )
            _Lines.append( "" )
            _Lines.append( "| 問題 | 原因 | 解決方式 |" )
            _Lines.append( "|------|------|---------|" )
            for _Prob in _Problems:
                _Lines.append(
                    f"| {_Prob.get( 'problem', '' )} | {_Prob.get( 'cause', '' )} | {_Prob.get( 'solution', '' )} |"
                )
            _Lines.append( "" )

        # 學到的知識
        _Learnings = iDetail.get( "learnings", [] )
        if _Learnings:
            _Lines.append( "## 學到的知識" )
            _Lines.append( "" )
            for _L in _Learnings:
                _Lines.append( f"- {_L}" )
            _Lines.append( "" )

        # 決策記錄
        _Decisions = iDetail.get( "decisions", [] )
        if _Decisions:
            _Lines.append( "## 決策記錄" )
            _Lines.append( "" )
            _Lines.append( "| 決策 | 選項 | 最終選擇 | 理由 |" )
            _Lines.append( "|------|------|---------|------|" )
            for _D in _Decisions:
                _Lines.append(
                    f"| {_D.get( 'decision', '' )} | {_D.get( 'options', '' )} | {_D.get( 'chosen', '' )} | {_D.get( 'reason', '' )} |"
                )
            _Lines.append( "" )

        return "\n".join( _Lines )
    #endregion

    #region 私有方法 — 自動學習管道
    def _auto_learn_instincts( self, iDetail: dict, iOrg: str, iProject: str ) -> None:
        """
        從 log_ai_conversation 的 detail 自動萃取直覺卡片。
        解析 problems（問題→解法→直覺）和 learnings（學到的知識→直覺）。
        靜默失敗：單張卡片建立失敗不影響整體對話記錄流程。

        Args:
            iDetail:  結構化詳細紀錄 dict。
            iOrg:     組織名稱。
            iProject: 專案名稱。
        """
        try:
            from services.instinct import InstinctService
            _Svc = InstinctService( self.m_Config )
        except Exception as _Err:
            _logger.warning( f"[AutoLearn] InstinctService 初始化失敗，跳過自動學習：{_Err}" )
            return

        _Source = f"auto-learn:{iOrg}/{iProject}"
        _Created = 0

        # ── 從 problems 萃取 ─────────────────────────
        for _P in iDetail.get( "problems", [] ):
            if not isinstance( _P, dict ):
                continue
            _Problem  = _P.get( "problem", "" ).strip()
            _Solution = _P.get( "solution", "" ).strip()
            if not _Problem or not _Solution:
                continue
            _Id = re.sub( r"[^a-z0-9]+", "-", _Problem[:60].lower() ).strip( "-" )
            if not _Id:
                continue
            try:
                _Svc.create(
                    iId=_Id,
                    iTrigger=_Problem,
                    iDomain=iProject,
                    iTitle=f"問題：{_Problem[:50]}",
                    iAction=_Solution,
                    iEvidence=_P.get( "cause", "" ),
                    iSource=_Source,
                )
                _Created += 1
            except FileExistsError:
                pass  # 同 ID 已存在，靜默跳過
            except Exception as _Err:
                _logger.warning( f"[AutoLearn] 建立 problem instinct '{_Id}' 失敗：{_Err}" )

        # ── 從 learnings 萃取 ────────────────────────
        for _L in iDetail.get( "learnings", [] ):
            if not isinstance( _L, str ) or len( _L.strip() ) < 10:
                continue
            _Text = _L.strip()
            _Id = re.sub( r"[^a-z0-9]+", "-", _Text[:60].lower() ).strip( "-" )
            if not _Id:
                continue
            try:
                _Svc.create(
                    iId=_Id,
                    iTrigger=_Text,
                    iDomain=iProject,
                    iTitle=f"學習：{_Text[:50]}",
                    iAction=_Text,
                    iSource=_Source,
                )
                _Created += 1
            except FileExistsError:
                pass
            except Exception as _Err:
                _logger.warning( f"[AutoLearn] 建立 learning instinct '{_Id}' 失敗：{_Err}" )

        if _Created > 0:
            _logger.info( f"[AutoLearn] 自動建立 {_Created} 張直覺卡片（{iOrg}/{iProject}）" )
    #endregion

    #region 私有方法 — 檔案操作
    @staticmethod
    def _sync_write( iRelPath: str, iContent: str ) -> None:
        """
        寫入檔案並同步至 ChromaDB（透過 VaultService）。

        Args:
            iRelPath: 相對於 Vault 根目錄的路徑。
            iContent: 檔案內容。
        """
        from services.vault import VaultService
        _Stats, _Error = VaultService.write_note( iRelPath, iContent )
        if _Error:
            print( f"[SchedulerService] Write error ({iRelPath}): {_Error}", file=sys.stderr )
            raise RuntimeError( f"Vault write failed ({iRelPath}): {_Error}" )
    #endregion
