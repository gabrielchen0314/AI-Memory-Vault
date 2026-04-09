"""
MCP 工具模組 — 直覺記憶工具
create_instinct / update_instinct / search_instincts / list_instincts / generate_retrospective

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.6
@date 2026.04.09
"""
from __future__ import annotations
from typing import Optional
from mcp_app.utils import suppress_stdout


def register( mcp, get_instinct ):
    """將直覺記憶工具註冊到 MCP Server。get_instinct() 回傳 InstinctService 單例。"""

    @mcp.tool()
    @suppress_stdout
    def create_instinct(
        id: str,
        trigger: str,
        domain: str,
        title: str,
        action: str,
        correct_pattern: str = "",
        evidence: str = "",
        reflection: str = "",
        confidence: float = 0.0,
        source: str = "session-observation",
    ) -> str:
        """
        建立新的直覺卡片（Instinct Card）。
        當 AI 在工作中犯錯或學到重要經驗時，建立直覺卡片以避免重複犯錯。
        id: 卡片 ID，slug 格式（例如 debug-one-change-at-a-time）。
        trigger: 觸發條件描述 — 什麼情境下應該想起這條規則。
        domain: 領域分類（debugging, workflow, csharp, unity, lua, python, architecture 等）。
        title: 卡片標題（簡短描述這條規則）。
        action: 遇到觸發條件時該怎麼做（具體行動指引）。
        correct_pattern: 正確模式的程式碼範例（選填，支援 Markdown 格式）。
        evidence: 證據描述 — 什麼時候發生過、後果是什麼（選填）。
        reflection: 錯誤反思 — 錯在哪、為什麼錯、正確做法、避免再犯（選填）。
        confidence: 初始信心度 0.0~1.0（0 = 使用預設 0.6）。
        source: 來源（預設 session-observation）。
        """
        _Path = get_instinct().create(
            iId=id, iTrigger=trigger, iDomain=domain, iTitle=title,
            iAction=action, iCorrectPattern=correct_pattern,
            iEvidence=evidence, iReflection=reflection,
            iConfidence=confidence, iSource=source,
        )
        return f"直覺卡片已建立：{_Path}"

    @mcp.tool()
    @suppress_stdout
    def update_instinct(
        id: str,
        confidence_delta: float = 0.0,
        new_evidence: str = "",
    ) -> str:
        """
        更新直覺卡片的信心度和/或新增證據。
        信心度會在 min_confidence(0.3) ~ max_confidence(1.0) 範圍內調整。
        id: 卡片 ID（例如 debug-one-change-at-a-time）。
        confidence_delta: 信心度增減值（如 +0.1 表示驗證成功提升，-0.05 表示衰減）。
        new_evidence: 新增的證據描述（Markdown 格式，選填）。
        """
        _Meta = get_instinct().update(
            iId=id, iConfidenceDelta=confidence_delta, iNewEvidence=new_evidence,
        )
        return f"直覺卡片已更新：{id}（信心度 → {_Meta.get( 'confidence', '?' )}）"

    @mcp.tool()
    @suppress_stdout
    def search_instincts(
        query: str,
        domain: str = "",
        min_confidence: float = 0.0,
    ) -> str:
        """
        搜尋直覺卡片。使用向量語意搜尋，可按 domain 和信心度過濾。
        工作前應搜尋相關直覺，避免重複犯錯。
        query: 搜尋關鍵字或情境描述。
        domain: 篩選特定 domain（選填）。
        min_confidence: 最低信心度門檻（選填，預設 0 = 全部）。
        """
        _Results = get_instinct().search(
            iQuery=query, iDomain=domain, iMinConfidence=min_confidence,
        )
        if not _Results:
            return "找不到符合條件的直覺卡片。"

        _Lines = [ f"找到 {len( _Results )} 張直覺卡片：\n" ]
        for _R in _Results:
            _Lines.append(
                f"- **{_R.get( 'id', '?' )}**（{_R.get( 'domain', '?' )}，"
                f"信心 {_R.get( 'confidence', '?' )}）\n"
                f"  觸發：{_R.get( 'trigger', '' )[:100]}\n"
                f"  摘要：{_R.get( 'snippet', '' )[:150]}"
            )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def list_instincts( domain: str = "" ) -> str:
        """
        列出所有直覺卡片的狀態概覽，按信心度排序。
        domain: 篩選特定 domain（選填，空字串 = 全部）。
        """
        _Results = get_instinct().list_all( iDomain=domain )
        if not _Results:
            return "目前沒有直覺卡片。"

        _Sorted = sorted( _Results, key=lambda x: float( x.get( "confidence", 0 ) ), reverse=True )
        _Config = get_instinct()._load_config()
        _Threshold = _Config["instincts"]["auto_apply_threshold"]

        _Lines = [ f"共 {len( _Sorted )} 張直覺卡片（自動套用閾值：{_Threshold}）：\n" ]
        _Lines.append( "| ID | 信心 | Domain | 建立日 | 狀態 |" )
        _Lines.append( "|-----|------|--------|--------|------|" )

        for _R in _Sorted:
            _Conf   = float( _R.get( "confidence", 0 ) )
            _Status = "🟢 自動" if _Conf >= _Threshold else "🟡 參考"
            _Lines.append(
                f"| {_R.get( 'id', '' )} | {_Conf} | {_R.get( 'domain', '' )} | {_R.get( 'created', '' )} | {_Status} |"
            )
        return "\n".join( _Lines )

    @mcp.tool()
    @suppress_stdout
    def generate_retrospective( month: str = "" ) -> str:
        """
        生成月度復盤報告模板。自動收集統計數據（工作天數、對話數、Instinct 成長、活躍專案），
        分析性欄位留空由開發者或 AI 覆盤時填寫。
        month: 月份 YYYY-MM（預設上個月）。
        """
        _Path = get_instinct().generate_retrospective( iMonth=month or "" )
        return f"月度復盤報告已生成：{_Path}"
