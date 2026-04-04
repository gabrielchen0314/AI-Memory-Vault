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
import sys
from datetime import datetime, timedelta
from typing import Optional

from config import AppConfig
from services.vault import VaultService


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
        _Date = iDate or datetime.now().strftime( "%Y-%m-%d" )
        _DailyDir = self.m_Config.paths.project_daily_dir( iOrg, iProject )
        _RelPath = f"{_DailyDir}/{_Date}.md"
        _AbsPath = os.path.join( self.m_VaultRoot, _RelPath )

        if os.path.exists( _AbsPath ):
            return _RelPath

        # 嘗試從 status.md 讀取待辦事項
        _PendingTodos: list = []
        try:
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
    def log_conversation( self, iOrg: str, iProject: str, iSessionName: str, iContent: str ) -> str:
        """
        記錄一次 AI 對話至指定專案的 conversations 目錄。

        Args:
            iOrg:         組織名稱（例如 'LIFEOFDEVELOPMENT'）。
            iProject:     專案名稱（例如 'ai-memory-vault'）。
            iSessionName: Session 名稱（例如 'vault-setup'）。
            iContent:     對話原始內容。

        Returns:
            檔案的相對路徑。
        """
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        _ConvDir = self.m_Config.paths.project_conversations_dir( iOrg, iProject )
        _RelPath = f"{_ConvDir}/{_Today}_{iSessionName}.md"

        self._sync_write( _RelPath, iContent )
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
        _TokenStats = self._compute_token_stats( _ProjectConvs )

        _Content = self._render_ai_weekly_analysis_template(
            _Year, _Week, _WeekStart, _WeekEnd, _ProjectConvs, _TokenStats
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

        _TokenStats = self._compute_token_stats( _ProjectConvs )
        _Content = self._render_ai_monthly_analysis_template(
            _YearMonth, _ProjectConvs, _WeeklyReports, _TokenStats
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

    def _render_ai_weekly_analysis_template(
        self, iYear: int, iWeek: int, iWeekStart: str, iWeekEnd: str,
        iProjectConvs: dict, iTokenStats: dict = None
    ) -> str:
        """渲染 AI 對話每週分析模板。"""
        from services.token_counter import TokenCounter
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        _TotalConvs = sum( len( _V ) for _V in iProjectConvs.values() )
        _P = self.m_Config.paths
        _TokenStatsMap = iTokenStats or {}
        _TotalTokens = sum( _TokenStatsMap.values() )

        # 各專案統計表
        _ProjRows = ""
        for _Key, _Files in iProjectConvs.items():
            _Org, _Proj = _Key.split( "/" )
            _ConvDir = _P.project_conversations_dir( _Org, _Proj )
            _Links = ", ".join( f"[{_F}]({_ConvDir}/{_F})" for _F in _Files )
            _ProjRows += f"| {_Org} | {_Proj} | {len( _Files )} | {_Links} |\n"

        if not _ProjRows:
            _ProjRows = "| （本週尚無對話紀錄） | | | |\n"

        # Token 消耗表（依專案）
        _TokenRows = ""
        for _Key, _Toks in _TokenStatsMap.items():
            _TokenRows += f"| {_Key} | {TokenCounter.format_k( _Toks )} | — | {TokenCounter.format_k( _Toks )} |\n"
        if not _TokenRows:
            _TokenRows = "| （無資料） | | | |\n"

        _TotalTokenFmt = TokenCounter.format_k( _TotalTokens ) if _TotalTokens else "—"

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
| 平均輪數（人→AI） | TODO |
| 一次成功率 | TODO% |
| 估計 Token 消耗 | {_TotalTokenFmt} |

## 各專案對話明細

| 組織 | 專案 | 對話數 | 對話列表 |
|------|------|--------|---------|
{_ProjRows}
## 對話準確率分析

### 成功的對話模式

- 

### 常見錯誤 / 需重試的情境

| 錯誤模式 | 出現次數 | 根本原因 | 改進方式 |
|---------|---------|---------|---------|
| 指令模糊 | | 缺乏具體需求描述 | 提供檔案路徑與期望結果 |
| 缺少上下文 | | 未附相關程式碼 | 先提供背景再提需求 |
| 一次要求過多 | | 需求範圍過大 | 拆分為獨立步驟 |

## Token 消耗分析

| 專案 | 預估 Input Tokens | 預估 Output Tokens | 合計 |
|------|------------------|-------------------|------|
{_TokenRows}
### 高消耗對話

- 

### 節省 Token 的方式

- 

## 本週評分

| 維度 | 評分 (1-5) | 說明 |
|------|-----------|------|
| 溝通效率 | ⬜ | |
| 輸出品質 | ⬜ | |
| 問題解決率 | ⬜ | |
| Prompt 技巧 | ⬜ | |

## Prompt 技巧收穫

- 

## 下週改進目標

- 
"""

    def _render_ai_monthly_analysis_template(
        self, iYearMonth: str, iProjectConvs: dict, iWeeklyReports: list,
        iTokenStats: dict = None
    ) -> str:
        """渲染 AI 對話每月分析模板。"""
        from services.token_counter import TokenCounter
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        _TotalConvs = sum( len( _V ) for _V in iProjectConvs.values() )
        _P = self.m_Config.paths
        _TokenStatsMap = iTokenStats or {}
        _TotalTokens = sum( _TokenStatsMap.values() )

        # 各專案月度統計
        _ProjRows = ""
        for _Key, _Files in iProjectConvs.items():
            _TokFmt = TokenCounter.format_k( _TokenStatsMap.get( _Key, 0 ) )
            _ProjRows += f"| {_Key} | {len( _Files )} | TODO | {_TokFmt} |\n"

        if not _ProjRows:
            _ProjRows = "| （本月尚無對話紀錄） | | | |\n"

        # 週報連結
        _WeeklyLinks = "\n".join(
            f"- [{_F}]({_P.ai_analysis_weekly}/{_F})" for _F in iWeeklyReports
        ) if iWeeklyReports else "（本月尚無週報）"

        _TotalTokenFmt = TokenCounter.format_k( _TotalTokens ) if _TotalTokens else "—"

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
| 月度一次成功率 | TODO% |
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
| W1 | | | | |
| W2 | | | | |
| W3 | | | | |
| W4 | | | | |

### 效率變化

- 

## 優化建議

### Prompt 優化

- 

### 工作流程優化

- 

### 工具使用優化

- 

## 月度評分

| 維度 | 評分 (1-5) | 上月 | 變化 |
|------|-----------|------|------|
| 溝通效率 | ⬜ | ⬜ | |
| 輸出品質 | ⬜ | ⬜ | |
| 問題解決率 | ⬜ | ⬜ | |
| Prompt 技巧 | ⬜ | ⬜ | |
| Token 效率 | ⬜ | ⬜ | |

## 主要收穫

- 

## 下月改進計畫

- 

## 反思

- 
"""
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
        _Stats, _Error = VaultService.write_note( iRelPath, iContent )
        if _Error:
            print( f"[SchedulerService] Write error ({iRelPath}): {_Error}", file=sys.stderr )
            raise RuntimeError( f"Vault write failed ({iRelPath}): {_Error}" )
    #endregion
