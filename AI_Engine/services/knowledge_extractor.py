"""
知識萃取服務
掃描指定專案的 conversations/ 目錄，生成 knowledge/ 知識卡片草稿。

行為說明：
  - 不依賴 LLM（無即時推理呼叫），從對話檔案結構萃取骨架
  - 掃描 conversations/*.md，擷取一級/二級標題與重點條列
  - 輸出到 knowledge/{date}-{topic}.md
  - 冪等：若同 topic 卡片已存在，以「更新來源」模式追加新對話連結而非覆蓋

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.2
@date 2026.04.05
"""
import os
import re
from datetime import datetime
from typing import Optional

from config import AppConfig
from services.vault import VaultService


class KnowledgeExtractor:
    """從 conversations/ 萃取知識卡片草稿的服務。"""

    #region 成員變數
    ## <summary>應用程式設定</summary>
    m_Config: AppConfig
    ## <summary>Vault 根目錄</summary>
    m_VaultRoot: str
    #endregion

    def __init__( self, iConfig: AppConfig ):
        """
        初始化知識萃取服務。

        Args:
            iConfig: 應用程式設定。
        """
        self.m_Config = iConfig
        self.m_VaultRoot = iConfig.vault_path

    #region 公開方法
    def extract(
        self,
        iOrg:     str,
        iProject: str,
        iTopic:   str,
        iSession: Optional[str] = None,
    ) -> tuple:
        """
        從指定專案的 conversations/ 萃取知識卡片，寫入 knowledge/{date}-{topic}.md。
        冪等：已存在時追加新來源清單，不覆蓋既有卡片內容。

        Args:
            iOrg:     組織名稱（例如 'LIFEOFDEVELOPMENT'）。
            iProject: 專案名稱（例如 'ai-memory-vault'）。
            iTopic:   知識主題（英文 slug，例如 'chromadb-sync'）。
            iSession: 篩選特定 session 名稱（留空 = 掃描所有）。

        Returns:
            (rel_path, error_message) — 成功時 error_message 為 None。
        """
        # ── 驗證輸入 ──────────────────────────────────────
        if not iOrg or not iProject or not iTopic:
            return None, "Error: org, project, topic 均為必填。"

        _TopicSlug = re.sub( r"[^\w\-]", "-", iTopic.lower() )
        if not _TopicSlug:
            return None, "Error: topic 轉換後為空，請使用英數字或連字號。"

        # ── 掃描 conversations/ ───────────────────────────
        _Sources = self._scan_conversations( iOrg, iProject, iSession )
        if not _Sources:
            return None, (
                f"Error: 找不到對話記錄 — "
                f"workspaces/{iOrg}/projects/{iProject}/conversations/"
                + ( f" (session={iSession})" if iSession else "" )
            )

        # ── 決定輸出路徑 ───────────────────────────────────
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        _FileName = f"{_Today}-{_TopicSlug}.md"
        _RelPath = f"{self.m_Config.paths.knowledge}/{_FileName}"
        _AbsPath = os.path.join( self.m_VaultRoot, _RelPath )

        # ── 冪等處理：已存在 → 追加來源 ─────────────────────
        if os.path.isfile( _AbsPath ):
            _, _Err = self._append_sources( _RelPath, _Sources )
            if _Err:
                return None, _Err
            return _RelPath, None

        # ── 全新卡片 ───────────────────────────────────────
        _KeyPoints = self._extract_key_points( _Sources )
        _Content = self._render_knowledge_card(
            _TopicSlug, iTopic, iOrg, iProject, _Today, _Sources, _KeyPoints
        )
        _Stats, _WriteErr = VaultService.write_note( _RelPath, _Content )
        if _WriteErr:
            return None, _WriteErr

        return _RelPath, None
    #endregion

    #region 私有方法 — 掃描
    def _scan_conversations( self, iOrg: str, iProject: str, iSession: Optional[str] ) -> list:
        """
        掃描 conversations/ 目錄，回傳符合條件的檔案資訊清單。

        Args:
            iOrg:     組織名稱。
            iProject: 專案名稱。
            iSession: 若給定則只回傳檔名含此字串的檔案。

        Returns:
            list of dict — { "rel_path", "file_name", "date", "session" }
        """
        _ConvDir = self.m_Config.paths.project_conversations_dir( iOrg, iProject )
        _ConvAbsDir = os.path.join( self.m_VaultRoot, _ConvDir )

        if not os.path.isdir( _ConvAbsDir ):
            return []

        _Results = []
        for _FileName in sorted( os.listdir( _ConvAbsDir ) ):
            if not _FileName.endswith( ".md" ):
                continue
            if iSession and iSession not in _FileName:
                continue

            # 解析檔名格式：YYYY-MM-DD_{session}.md
            _Date    = _FileName[:10] if len( _FileName ) > 10 else ""
            _Session = _FileName[11:-3] if len( _FileName ) > 14 else _FileName[:-3]

            _Results.append( {
                "rel_path":  f"{_ConvDir}/{_FileName}",
                "file_name": _FileName,
                "date":      _Date,
                "session":   _Session,
            } )

        return _Results

    def _extract_key_points( self, iSources: list ) -> list:
        """
        從對話檔案擷取一級/二級標題與重點條列，作為知識卡片草稿。
        最多取前 15 行重點，避免卡片過長。

        Args:
            iSources: _scan_conversations 回傳的檔案資訊清單。

        Returns:
            list of str — 去重後的重點字串清單。
        """
        _Points   = []
        _Seen     = set()
        _MaxTotal = 15

        for _Src in iSources:
            if len( _Points ) >= _MaxTotal:
                break

            _AbsPath = os.path.join( self.m_VaultRoot, _Src["rel_path"] )
            if not os.path.isfile( _AbsPath ):
                continue

            try:
                with open( _AbsPath, "r", encoding="utf-8" ) as _F:
                    _Lines = _F.readlines()
            except OSError:
                continue

            for _Line in _Lines:
                if len( _Points ) >= _MaxTotal:
                    break

                _Stripped = _Line.strip()

                # 擷取：## 標題、- 條列（排除 frontmatter 行）
                _IsHeading = _Stripped.startswith( "## " ) or _Stripped.startswith( "# " )
                _IsBullet  = _Stripped.startswith( "- " ) and len( _Stripped ) > 5

                if _IsHeading or _IsBullet:
                    # 過濾 frontmatter、空行、框架文字
                    _Clean = _Stripped.lstrip( "#" ).strip()
                    if _Clean and _Clean not in _Seen and not _Clean.startswith( "---" ):
                        _Points.append( _Clean )
                        _Seen.add( _Clean )

        return _Points
    #endregion

    #region 私有方法 — 寫入
    def _append_sources( self, iRelPath: str, iNewSources: list ) -> tuple:
        """
        在已存在的知識卡片末尾追加新的來源連結（去重）。

        Args:
            iRelPath:    卡片路徑（相對於 Vault 根目錄）。
            iNewSources: 新來源清單。

        Returns:
            (None, error_message) 或 (None, None)。
        """
        _Content, _Err = VaultService.read_note( iRelPath )
        if _Err:
            return None, _Err

        _NewLines = []
        for _Src in iNewSources:
            _Link = f"- [{_Src['date']} {_Src['session']}]({_Src['rel_path']})"
            if _Link not in _Content:
                _NewLines.append( _Link )

        if not _NewLines:
            return None, None  # 沒有新來源，無需更新

        _Appended = _Content.rstrip() + "\n" + "\n".join( _NewLines ) + "\n"
        _, _WriteErr = VaultService.write_note( iRelPath, _Appended )
        return None, _WriteErr
    #endregion

    #region 私有方法 — 模板渲染
    def _render_knowledge_card(
        self,
        iSlug:      str,
        iTopic:     str,
        iOrg:       str,
        iProject:   str,
        iDate:      str,
        iSources:   list,
        iKeyPoints: list,
    ) -> str:
        """
        渲染知識卡片 Markdown 模板。

        Args:
            iSlug:      topic slug（lowercase-kebab）。
            iTopic:     原始 topic 字串（顯示用）。
            iOrg:       組織名稱。
            iProject:   專案名稱。
            iDate:      建立日期 YYYY-MM-DD。
            iSources:   來源對話清單。
            iKeyPoints: 從對話萃取的重點列表。

        Returns:
            完整 Markdown 字串。
        """
        _SourceLines = "\n".join(
            f"- [{_S['date']} {_S['session']}]({_S['rel_path']})"
            for _S in iSources
        )

        if iKeyPoints:
            _DraftLines = "\n".join( f"- {_P}" for _P in iKeyPoints )
            _DraftSection = f"（以下為自動萃取草稿，請人工審閱修訂）\n\n{_DraftLines}"
        else:
            _DraftSection = "（請從來源對話填入重點）"

        return f"""---
type: knowledge
topic: {iSlug}
source_org: {iOrg}
source_project: {iProject}
created: {iDate}
tags: []
---

# {iTopic}

## 核心概念

{_DraftSection}

## 問題表現

（描述問題的症狀或觸發條件）

## 解法

（記錄有效的解決方案）

## 注意事項

（陷阱、邊界條件、不適用場景）

## 來源對話

{_SourceLines}
"""
    #endregion
