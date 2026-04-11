"""
直覺記憶服務 — 管理 AI 直覺卡片（Instinct Cards）的建立、搜尋、更新、信心管理。

直覺卡片是 AI 從工作經驗中學到的行為規則，包含觸發條件、正確做法、證據和信心度，
用於避免重複犯錯並加速問題解決。

自主學習管道：
  工作中犯錯 / 學到新知
    → log_ai_conversation（detail.problems / detail.learnings）
    → AI 判斷是否需要建立 instinct
    → create_instinct（信心初始 0.6）
    → 下次類似情境 → search_instincts → 主動提醒
    → 月底 → generate_retrospective → 分析模式

儲存位置：personal/instincts/
  _config.json    配置（信心閾值、衰減率）
  {id}.md         個別直覺卡片

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.6
@date 2026.04.09
"""
import json
import os
import re
from datetime import datetime
from typing import Optional

from config import AppConfig
from core.logger import get_logger

_logger = get_logger( __name__ )

# ── 預設配置 ─────────────────────────────────────────────
_DEFAULT_CONFIG = {
    "version": "1.0",
    "instincts": {
        "min_confidence": 0.3,
        "auto_apply_threshold": 0.7,
        "initial_confidence": 0.6,
        "max_confidence": 1.0,
    },
    "evolution": {
        "cluster_threshold": 3,
        "min_average_confidence": 0.6,
    },
}


class InstinctService:
    """直覺記憶管理服務。"""

    #region 成員變數
    ## <summary>應用程式設定</summary>
    m_Config: AppConfig
    ## <summary>Vault 根目錄</summary>
    m_VaultRoot: str
    ## <summary>Instinct 儲存目錄（絕對路徑）</summary>
    m_InstinctDir: str
    #endregion

    def __init__( self, iConfig: AppConfig ):
        """
        初始化直覺記憶服務。

        Args:
            iConfig: 應用程式設定。
        """
        self.m_Config      = iConfig
        self.m_VaultRoot   = iConfig.vault_path
        self.m_InstinctDir = os.path.join( self.m_VaultRoot, iConfig.paths.personal_instincts )
        self._cached_config: Optional[dict] = None
        os.makedirs( self.m_InstinctDir, exist_ok=True )

    # ─────────────────────────────────────────────
    #region 設定檔管理
    # ─────────────────────────────────────────────

    def _load_config( self ) -> dict:
        """載入 instinct 設定，不存在則建立預設。使用快取避免重複讀取。"""
        if self._cached_config is not None:
            return self._cached_config
        _Path = os.path.join( self.m_InstinctDir, "_config.json" )
        if os.path.exists( _Path ):
            with open( _Path, "r", encoding="utf-8" ) as _F:
                self._cached_config = json.load( _F )
                return self._cached_config
        self._save_config( _DEFAULT_CONFIG )
        self._cached_config = _DEFAULT_CONFIG.copy()
        return self._cached_config

    def _save_config( self, iConfig: dict ) -> None:
        """儲存 instinct 設定並更新快取。"""
        _Path = os.path.join( self.m_InstinctDir, "_config.json" )
        with open( _Path, "w", encoding="utf-8" ) as _F:
            json.dump( iConfig, _F, indent=2, ensure_ascii=False )
        self._cached_config = iConfig

    #endregion

    # ─────────────────────────────────────────────
    #region Sequence 管理
    # ─────────────────────────────────────────────

    def _next_sequence( self ) -> int:
        """取得下一個序號並自動遞增。"""
        _Path = os.path.join( self.m_InstinctDir, "_sequence.json" )
        _Seq  = 0
        if os.path.exists( _Path ):
            with open( _Path, "r", encoding="utf-8" ) as _F:
                _Seq = json.load( _F ).get( "value", 0 )
        _Seq += 1
        with open( _Path, "w", encoding="utf-8" ) as _F:
            json.dump( { "value": _Seq }, _F )
        return _Seq

    def _get_sequence( self ) -> int:
        """取得目前序號（不遞增）。"""
        _Path = os.path.join( self.m_InstinctDir, "_sequence.json" )
        if os.path.exists( _Path ):
            with open( _Path, "r", encoding="utf-8" ) as _F:
                return json.load( _F ).get( "value", 0 )
        return 0

    #endregion

    # ─────────────────────────────────────────────
    #region Frontmatter 解析
    # ─────────────────────────────────────────────

    @staticmethod
    def _parse_frontmatter( iContent: str ) -> dict:
        """
        解析 YAML frontmatter（委派至 core.frontmatter 共用模組）。

        Args:
            iContent: 完整檔案內容（含 --- 標記）。
        """
        from core.frontmatter import parse
        _Meta, _ = parse( iContent )
        return _Meta

    @staticmethod
    def _render_frontmatter( iMeta: dict ) -> str:
        """
        渲染 YAML frontmatter（委派至 core.frontmatter 共用模組）。

        Args:
            iMeta: metadata 字典。
        """
        from core.frontmatter import render
        return render( iMeta )

    #endregion

    # ─────────────────────────────────────────────
    #region CRUD 操作
    # ─────────────────────────────────────────────

    def create(
        self,
        iId: str,
        iTrigger: str,
        iDomain: str,
        iTitle: str,
        iAction: str,
        iCorrectPattern: str = "",
        iEvidence: str = "",
        iReflection: str = "",
        iConfidence: float = 0.0,
        iSource: str = "session-observation",
    ) -> str:
        """
        建立新的直覺卡片。

        Args:
            iId:             卡片 ID（slug 格式，如 debug-one-change-at-a-time）。
            iTrigger:        觸發條件描述。
            iDomain:         領域（debugging, workflow, csharp, unity, lua 等）。
            iTitle:          卡片標題。
            iAction:         遇到觸發條件時該怎麼做。
            iCorrectPattern: 正確模式的程式碼範例（選填）。
            iEvidence:       證據描述（選填）。
            iReflection:     錯誤反思（選填）。
            iConfidence:     初始信心度（0 = 使用預設 0.6）。
            iSource:         來源（預設 session-observation）。

        Returns:
            Vault 相對路徑。

        Raises:
            FileExistsError: 同 ID 卡片已存在。
        """
        _Config = self._load_config()
        if iConfidence <= 0:
            iConfidence = _Config["instincts"]["initial_confidence"]

        _Seq     = self._next_sequence()
        _RelPath = f"personal/instincts/{iId}.md"
        _AbsPath = os.path.join( self.m_VaultRoot, _RelPath )

        if os.path.exists( _AbsPath ):
            raise FileExistsError( f"直覺卡片已存在：{iId}" )

        # ── 組裝卡片內容 ──
        _Meta = {
            "id":         iId,
            "trigger":    iTrigger,
            "confidence": iConfidence,
            "domain":     iDomain,
            "source":     iSource,
            "created":    datetime.now().strftime( "%Y-%m-%d" ),
            "sequence":   _Seq,
        }

        _Sections = [ self._render_frontmatter( _Meta ), "", f"# {iTitle}", "", "## 動作", iAction ]

        if iCorrectPattern:
            _Sections.extend( [ "", "## 正確模式", iCorrectPattern ] )
        if iEvidence:
            _Sections.extend( [ "", "## 證據", iEvidence ] )
        if iReflection:
            _Sections.extend( [ "", "## ⚠️ 錯誤反思", iReflection ] )

        _Content = "\n".join( _Sections ) + "\n"

        # ── 寫入 Vault（自動索引） ──
        from services.vault import VaultService
        VaultService.write_note( _RelPath, _Content )

        _logger.info( "[Instinct] created: %s (seq=%d, confidence=%.2f)", iId, _Seq, iConfidence )
        return _RelPath

    def update(
        self,
        iId: str,
        iConfidenceDelta: float = 0.0,
        iNewEvidence: str = "",
    ) -> dict:
        """
        更新直覺卡片的信心度和/或新增證據。

        Args:
            iId:              卡片 ID。
            iConfidenceDelta: 信心度增減值（如 +0.1 或 -0.05）。
            iNewEvidence:     新增的證據描述（選填）。

        Returns:
            更新後的 metadata dict。

        Raises:
            FileNotFoundError: 卡片不存在。
        """
        _RelPath = f"personal/instincts/{iId}.md"
        _AbsPath = os.path.join( self.m_VaultRoot, _RelPath )

        if not os.path.exists( _AbsPath ):
            raise FileNotFoundError( f"直覺卡片不存在：{iId}" )

        with open( _AbsPath, "r", encoding="utf-8" ) as _F:
            _Content = _F.read()

        _Meta   = self._parse_frontmatter( _Content )
        _Config = self._load_config()

        # ── 更新信心度 ──
        if iConfidenceDelta != 0:
            _Old = float( _Meta.get( "confidence", 0.6 ) )
            _New = max(
                _Config["instincts"]["min_confidence"],
                min( _Config["instincts"]["max_confidence"], _Old + iConfidenceDelta ),
            )
            _Meta["confidence"] = round( _New, 2 )

        # ── 重建內容 ──
        _FmEnd = _Content.find( "---", 3 )
        _Body  = _Content[_FmEnd + 3:].lstrip( "\n" )

        if iNewEvidence:
            if "## 證據" in _Body:
                _Body = _Body.replace( "## 證據\n", f"## 證據\n{iNewEvidence}\n", 1 )
            else:
                _Body += f"\n## 證據\n{iNewEvidence}\n"

        _NewContent = self._render_frontmatter( _Meta ) + "\n\n" + _Body

        from services.vault import VaultService
        VaultService.write_note( _RelPath, _NewContent )

        _logger.info( "[Instinct] updated: %s → confidence=%.2f", iId, _Meta.get( "confidence", 0 ) )
        return _Meta

    def list_all( self, iDomain: str = "" ) -> list:
        """
        列出所有直覺卡片的摘要資訊。

        Args:
            iDomain: 篩選特定 domain（空字串 = 全部）。

        Returns:
            [{ id, trigger, confidence, domain, created, sequence }, ...]
        """
        _Results = []
        if not os.path.isdir( self.m_InstinctDir ):
            return _Results

        for _Fname in sorted( os.listdir( self.m_InstinctDir ) ):
            if not _Fname.endswith( ".md" ):
                continue
            _AbsPath = os.path.join( self.m_InstinctDir, _Fname )
            try:
                with open( _AbsPath, "r", encoding="utf-8" ) as _F:
                    _Content = _F.read()
                _Meta = self._parse_frontmatter( _Content )
                if not _Meta.get( "id" ):
                    continue
                if iDomain and _Meta.get( "domain" ) != iDomain:
                    continue
                _Results.append( _Meta )
            except Exception as _Err:
                _logger.warning( "[Instinct] parse error %s: %s", _Fname, _Err )

        return _Results

    def search( self, iQuery: str, iDomain: str = "", iMinConfidence: float = 0.0 ) -> list:
        """
        搜尋直覺卡片（Vault 向量搜尋 + 後過濾）。

        Args:
            iQuery:         搜尋關鍵字或描述。
            iDomain:        篩選 domain（選填）。
            iMinConfidence: 最低信心度門檻（選填）。

        Returns:
            [{ id, trigger, confidence, domain, snippet, score }, ...]
        """
        from services.vault import VaultService

        _Hits    = VaultService.search( iQuery, iTopK=20 )
        _Results = []

        for _Hit in _Hits:
            _Source = _Hit.get( "source", "" )
            if "personal/instincts/" not in _Source:
                continue

            _AbsPath = os.path.join( self.m_VaultRoot, _Source )
            if not os.path.exists( _AbsPath ):
                continue

            with open( _AbsPath, "r", encoding="utf-8" ) as _F:
                _Content = _F.read()
            _Meta = self._parse_frontmatter( _Content )

            if iDomain and _Meta.get( "domain" ) != iDomain:
                continue
            if float( _Meta.get( "confidence", 0 ) ) < iMinConfidence:
                continue

            _Meta["snippet"] = _Hit.get( "content", "" )[:200]
            _Results.append( _Meta )

        return _Results

    #endregion

    # ─────────────────────────────────────────────
    #region 月度復盤
    # ─────────────────────────────────────────────

    def generate_retrospective( self, iMonth: str = "" ) -> str:
        """
        生成月度復盤報告模板。
        自動收集當月統計數據（工作天數、對話數、Instinct 成長、活躍專案），
        分析性欄位留空由 AI 在覆盤時填寫。

        Args:
            iMonth: 月份 YYYY-MM（預設上個月）。

        Returns:
            Vault 相對路徑。
        """
        if not iMonth:
            _Today = datetime.now()
            if _Today.month == 1:
                iMonth = f"{_Today.year - 1}-12"
            else:
                iMonth = f"{_Today.year}-{_Today.month - 1:02d}"

        _Year, _MonthNum = iMonth.split( "-" )
        _MonthNum = int( _MonthNum )

        # ── 收集統計資料 ──
        _Stats = self._collect_month_stats( iMonth )

        # ── 生成報告 ──
        _RelPath = f"personal/reviews/monthly/{iMonth}-retrospective.md"
        _Content = self._render_retrospective( iMonth, _Year, _MonthNum, _Stats )

        from services.vault import VaultService
        VaultService.write_note( _RelPath, _Content )

        _logger.info( "[Instinct] retrospective generated: %s", _RelPath )
        return _RelPath

    def _collect_month_stats( self, iMonth: str ) -> dict:
        """收集指定月份的統計資料。"""
        _AllInstincts   = self.list_all()
        _MonthInstincts = [ _I for _I in _AllInstincts if str( _I.get( "created", "" ) ).startswith( iMonth ) ]

        # Domain 分布
        _DomainCounts = {}
        for _Inst in _AllInstincts:
            _D = _Inst.get( "domain", "unknown" )
            _DomainCounts[_D] = _DomainCounts.get( _D, 0 ) + 1

        # 每日回顧計數
        _DailyDir   = os.path.join( self.m_VaultRoot, "personal/reviews/daily" )
        _DailyCount = 0
        if os.path.isdir( _DailyDir ):
            _DailyCount = sum(
                1 for _F in os.listdir( _DailyDir )
                if _F.startswith( iMonth ) and _F.endswith( ".md" )
            )

        # 對話紀錄 + 活躍專案
        _ConvCount      = 0
        _ActiveProjects = []
        _WsDir          = os.path.join( self.m_VaultRoot, "workspaces" )
        if os.path.isdir( _WsDir ):
            for _Org in os.listdir( _WsDir ):
                if _Org.startswith( "_" ):
                    continue
                _ProjDir = os.path.join( _WsDir, _Org, "projects" )
                if not os.path.isdir( _ProjDir ):
                    continue
                for _Proj in os.listdir( _ProjDir ):
                    _ConvDir = os.path.join( _ProjDir, _Proj, "conversations" )
                    if not os.path.isdir( _ConvDir ):
                        continue
                    _MonthConvs = [
                        _F for _F in os.listdir( _ConvDir )
                        if _F.startswith( iMonth ) and _F.endswith( ".md" )
                    ]
                    if _MonthConvs:
                        _ConvCount += len( _MonthConvs )
                        _ActiveProjects.append( f"{_Org}/{_Proj}" )

        return {
            "all_instincts":    _AllInstincts,
            "month_instincts":  _MonthInstincts,
            "domain_counts":    _DomainCounts,
            "daily_count":      _DailyCount,
            "conv_count":       _ConvCount,
            "active_projects":  _ActiveProjects,
        }

    def _render_retrospective( self, iMonth: str, iYear: str, iMonthNum: int, iStats: dict ) -> str:
        """渲染月度復盤報告 Markdown。"""
        _All   = iStats["all_instincts"]
        _New   = iStats["month_instincts"]
        _DC    = iStats["domain_counts"]
        _AP    = iStats["active_projects"]
        _Today = datetime.now().strftime( "%Y-%m-%d" )

        # Domain 表
        _DomainRows = "\n".join( f"| {_D} | {_C} |" for _D, _C in sorted( _DC.items() ) ) if _DC else "| — | 0 |"

        # Instinct Top 10 表
        _Sorted = sorted( _All, key=lambda x: float( x.get( "confidence", 0 ) ), reverse=True )
        _InstRows = "\n".join(
            f"| {_I.get( 'id', '' )} | {_I.get( 'confidence', '' )} | {_I.get( 'domain', '' )} | {_I.get( 'created', '' )} |"
            for _I in _Sorted[:10]
        ) if _All else "| — | — | — | — |"

        # 本月新增
        _NewRows = "\n".join(
            f"- **{_I.get( 'id' )}**（{_I.get( 'domain' )}，信心 {_I.get( 'confidence' )}）"
            for _I in _New
        ) if _New else "- 無"

        # 活躍專案
        _ProjRows = "\n".join(
            f"| {_P} | 🟡 待填寫 | 待填寫 |" for _P in _AP
        ) if _AP else "| — | — | — |"

        _MonthCN = f"{iYear} 年 {iMonthNum} 月"

        return f"""---
type: retrospective
month: "{iMonth}"
created: "{_Today}"
---

# {_MonthCN} — 復盤報告 📊

## 📋 更新記錄
| 更新時間 | 涵蓋範圍 | 本次新增說明 |
|---------|---------|-------------|
| {_Today} | {iMonthNum:02d}/01 ~ {iMonthNum:02d}/末 | 首次建立 |

---

## 零、跨月對照分析

### 📊 歷史復盤比較
<!-- 與前月復盤對比，補充差異分析 -->

### 🔁 重複犯錯追蹤
<!-- 列出本月重現的已知問題 -->

### 📈 改善成效驗證
<!-- 驗證上月行動項是否產生效果 -->

---

## 一、本月工作總覽

### 📈 數據統計

| 項目 | 數量 |
|------|------|
| 工作日數（有回顧的天數） | {iStats['daily_count']} |
| 對話紀錄 | {iStats['conv_count']} |
| 活躍專案 | {len( _AP )} |
| Instinct 總數 | {len( _All )} |
| 本月新增 Instinct | {len( _New )} |

### 🗓️ 活躍專案

| 專案 | 狀態 | 主要工作 |
|------|------|---------|
{_ProjRows}

---

## 二、問題回顧與根因分析

### 🔴 嚴重問題
<!-- 高影響問題：描述情境、後果、根因、改善方向 -->

### 🟡 中等問題
<!-- 中影響問題 -->

### 🟢 輕微問題
<!-- 低影響問題 -->

### 📊 根因分類統計

| 根因類型 | 問題數 |
|---------|-------|
| 待分析 | 0 |

---

## 三、指令清晰度分析（開發者側）⭐

### ⚠️ 本月溝通障礙

| 類型 | 情境 | AI 行為 | 建議表達方式 |
|------|------|---------|-------------|
| 待補充 | | | |

### ✅ 值得繼續保持的溝通習慣
<!-- 列出本月有效的溝通模式 -->

---

## 四、AI 理解偏差分析

### 概念層混淆
<!-- AI 混淆概念的情況 -->

### 流程遺漏
<!-- AI 遺漏重要步驟的情況 -->

### 策略偏差
<!-- AI 選擇了錯誤策略的情況 -->

---

## 五、協作效率分析

### 📊 協作效率指數（估算）

| 指標 | 估算值 |
|------|--------|
| 整體零迭代比率 | 待統計 |
| 平均修正輪次 | 待統計 |

### 📋 技術債累積追蹤

| 技術債項目 | 發現日期 | 風險等級 | 處理計畫 |
|-----------|---------|---------|---------|
| 待補充 | | | |

---

## 六、直覺系統復盤

### 📊 Instinct 成長軌跡

| 時間點 | Instinct 數 |
|--------|------------|
| 月初 | {len( _All ) - len( _New )} |
| 月末 | {len( _All )} |
| **淨成長** | {len( _New )} |

### 📈 Domain 分布

| Domain | 數量 |
|--------|------|
{_DomainRows}

### 🏆 高信心 Instinct Top 10

| Instinct ID | 信心 | Domain | 建立日 |
|------------|------|--------|--------|
{_InstRows}

### 本月新增 Instinct

{_NewRows}

---

## 七、成就與亮點 🎉

### 技術成就
<!-- 本月技術突破 -->

### AI 協作成就
<!-- AI 分析正確、效率提升的案例 -->

### 開發者成長觀察
<!-- 工作習慣改善 -->

---

## 八、下階段展望

### 延續項目

| 項目 | 狀態 | 說明 |
|------|------|------|
| 待補充 | | |

### 系統改進行動項

| 行動項 | 優先度 | 說明 |
|--------|--------|------|
| 待補充 | | |
"""

    #endregion
