"""
SchedulerService 單元測試
覆蓋所有公開方法的核心邏輯：
  - generate_project_daily（含 status.md 預填充、冪等）
  - generate_project_status（冪等）
  - generate_daily_summary（覆寫、_global 連結）
  - generate_weekly_summary（同週同路徑、跨週不同路徑）
  - generate_monthly_summary（同月同路徑）
  - log_conversation（覆寫）
  - generate_ai_weekly_analysis（冪等、對話掃描）
  - generate_ai_monthly_analysis（冪等）

所有 Fixtures 定義於 conftest.py。
VaultService 透過 patch_vault fixture 替換為 filesystem stub。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
import os
import pytest


# ────────────────────────────────────────────────────────────
# Helper
# ────────────────────────────────────────────────────────────

def _read( vault_root, rel_path: str ) -> str:
    """Read a file from vault_root given its relative path."""
    _Abs = os.path.join( str( vault_root ), rel_path )
    with open( _Abs, "r", encoding="utf-8" ) as _F:
        return _F.read()


# ────────────────────────────────────────────────────────────
# generate_project_daily
# ────────────────────────────────────────────────────────────

class TestGenerateProjectDaily:

    def test_creates_file( self, sched, vault_root ):
        _Path = sched.generate_project_daily( "TESTORG", "TESTPROJ", "2026-04-04" )
        assert _Path.endswith( "2026-04-04.md" )
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )

    def test_returns_relative_path( self, sched ):
        _Path = sched.generate_project_daily( "TESTORG", "TESTPROJ", "2026-04-04" )
        assert not os.path.isabs( _Path )

    def test_idempotent( self, sched, vault_root ):
        _P1 = sched.generate_project_daily( "TESTORG", "TESTPROJ", "2026-04-04" )
        os.path.join( str( vault_root ), _P1 )
        _P2 = sched.generate_project_daily( "TESTORG", "TESTPROJ", "2026-04-04" )
        assert _P1 == _P2

    def test_contains_required_sections( self, sched, vault_root ):
        _Path = sched.generate_project_daily( "TESTORG", "TESTPROJ", "2026-04-04" )
        _Content = _read( vault_root, _Path )
        for _Section in [ "今日計畫", "今日完成", "遇到的問題", "明日計畫" ]:
            assert _Section in _Content, f"缺少區塊：{_Section}"

    def test_prefills_todos_from_status( self, sched, vault_root ):
        """status.md 存在時，今日計畫應預填待辦事項。"""
        # 直接寫入 status.md（繞過 VaultService，讓 get_project_status stub 可讀到）
        _ProjDir = vault_root / "workspaces" / "TESTORG" / "projects" / "TESTPROJ_ST"
        _ProjDir.mkdir( parents=True, exist_ok=True )
        ( _ProjDir / "status.md" ).write_text(
            "- [ ] 實作功能 A\n- [ ] 修復 Bug B\n",
            encoding="utf-8",
        )
        _Path = sched.generate_project_daily( "TESTORG", "TESTPROJ_ST", "2026-04-05" )
        _Content = _read( vault_root, _Path )
        assert "實作功能 A" in _Content
        assert "修復 Bug B" in _Content

    def test_graceful_fallback_no_status( self, sched, vault_root ):
        """status.md 不存在時，不拋出例外，改用空白模板。"""
        # patch_vault 的 get_project_status 找不到 status.md 時回傳 (None, 'not found')
        # scheduler 的 try/except 處理此情形並使用空模板
        _Path = sched.generate_project_daily( "TESTORG", "PROJ-NO-STATUS", "2026-04-04" )
        assert _Path.endswith( "2026-04-04.md" )
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )
        _Content = _read( vault_root, _Path )
        assert "今日計畫" in _Content

    def test_uses_today_by_default( self, sched ):
        from datetime import datetime
        _Path = sched.generate_project_daily( "TESTORG", "TESTPROJ" )
        _Today = datetime.now().strftime( "%Y-%m-%d" )
        assert _Today in _Path

    def test_frontmatter_correct( self, sched, vault_root ):
        _Path = sched.generate_project_daily( "TESTORG", "TESTPROJ", "2026-04-04" )
        _Content = _read( vault_root, _Path )
        assert "type: project-daily" in _Content
        assert "organization: TESTORG" in _Content
        assert "project: TESTPROJ" in _Content

    def test_status_link_in_content( self, sched, vault_root ):
        _Path = sched.generate_project_daily( "TESTORG", "TESTPROJ", "2026-04-04" )
        _Content = _read( vault_root, _Path )
        assert "status.md" in _Content


# ────────────────────────────────────────────────────────────
# generate_project_status
# ────────────────────────────────────────────────────────────

class TestGenerateProjectStatus:

    def test_creates_file( self, sched, vault_root ):
        _Path = sched.generate_project_status( "TESTORG", "TESTPROJ" )
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )

    def test_idempotent( self, sched, vault_root ):
        _P1 = sched.generate_project_status( "TESTORG", "TESTPROJ" )
        os.path.join( str( vault_root ), _P1 )
        _P2 = sched.generate_project_status( "TESTORG", "TESTPROJ" )
        assert _P1 == _P2

    def test_contains_todo_sections( self, sched, vault_root ):
        _Path = sched.generate_project_status( "TESTORG", "TESTPROJ" )
        _Content = _read( vault_root, _Path )
        assert "待辦事項" in _Content
        assert "工作脈絡" in _Content

    def test_frontmatter( self, sched, vault_root ):
        _Path = sched.generate_project_status( "TESTORG", "TESTPROJ" )
        _Content = _read( vault_root, _Path )
        assert "type: project-status" in _Content


# ────────────────────────────────────────────────────────────
# generate_daily_summary
# ────────────────────────────────────────────────────────────

class TestGenerateDailySummary:

    def test_creates_personal_file( self, sched, vault_root ):
        _Path = sched.generate_daily_summary( "2026-04-04" )
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )

    def test_overwrites_on_second_call( self, sched, vault_root ):
        """第二次呼叫（含新內容）應覆寫第一次，路徑不變。"""
        _P1 = sched.generate_daily_summary( "2026-04-04" )
        _P2 = sched.generate_daily_summary(
            "2026-04-04",
            [{"organization": "ORG", "project": "PROJ", "summary": "新摘要"}],
        )
        assert _P1 == _P2
        assert "新摘要" in _read( vault_root, _P2 )

    def test_project_rows_rendered( self, sched, vault_root ):
        _Path = sched.generate_daily_summary(
            "2026-04-04",
            [{"organization": "MYORG", "project": "MYPROJ", "summary": "搞定了"}],
        )
        _Content = _read( vault_root, _Path )
        assert "MYORG" in _Content
        assert "MYPROJ" in _Content
        assert "搞定了" in _Content

    def test_has_ai_conversation_section( self, sched, vault_root ):
        _Path = sched.generate_daily_summary( "2026-04-04" )
        _Content = _read( vault_root, _Path )
        assert "AI 對話" in _Content

    def test_frontmatter( self, sched, vault_root ):
        _Path = sched.generate_daily_summary( "2026-04-04" )
        _Content = _read( vault_root, _Path )
        assert "type: daily-summary" in _Content


# ────────────────────────────────────────────────────────────
# generate_weekly_summary
# ────────────────────────────────────────────────────────────

class TestGenerateWeeklySummary:

    def test_creates_file( self, sched, vault_root ):
        _Path = sched.generate_weekly_summary( "2026-04-04" )
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )
        assert "-W" in _Path

    def test_idempotent( self, sched ):
        _P1 = sched.generate_weekly_summary( "2026-04-04" )
        _P2 = sched.generate_weekly_summary( "2026-04-04" )
        assert _P1 == _P2

    def test_same_week_same_path( self, sched ):
        """同一週的不同日期應產生相同路徑。"""
        _P1 = sched.generate_weekly_summary( "2026-04-06" )  # 週一
        _P2 = sched.generate_weekly_summary( "2026-04-10" )  # 週五
        assert _P1 == _P2

    def test_different_weeks_different_path( self, sched ):
        _P1 = sched.generate_weekly_summary( "2026-04-04" )
        _P2 = sched.generate_weekly_summary( "2026-04-11" )
        assert _P1 != _P2

    def test_contains_required_sections( self, sched, vault_root ):
        _Path = sched.generate_weekly_summary( "2026-04-04" )
        _Content = _read( vault_root, _Path )
        assert "本週目標達成" in _Content
        assert "下週重點" in _Content

    def test_frontmatter( self, sched, vault_root ):
        _Path = sched.generate_weekly_summary( "2026-04-04" )
        _Content = _read( vault_root, _Path )
        assert "type: weekly-summary" in _Content


# ────────────────────────────────────────────────────────────
# generate_monthly_summary
# ────────────────────────────────────────────────────────────

class TestGenerateMonthlySummary:

    def test_creates_file( self, sched, vault_root ):
        _Path = sched.generate_monthly_summary( "2026-04-04" )
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )
        assert "2026-04" in _Path

    def test_idempotent( self, sched ):
        _P1 = sched.generate_monthly_summary( "2026-04-04" )
        _P2 = sched.generate_monthly_summary( "2026-04-15" )
        assert _P1 == _P2

    def test_different_months_different_path( self, sched ):
        _P1 = sched.generate_monthly_summary( "2026-04-04" )
        _P2 = sched.generate_monthly_summary( "2026-05-01" )
        assert _P1 != _P2

    def test_contains_required_sections( self, sched, vault_root ):
        _Path = sched.generate_monthly_summary( "2026-04-04" )
        _Content = _read( vault_root, _Path )
        for _S in [ "本月目標", "重大成果", "下月規劃" ]:
            assert _S in _Content


# ────────────────────────────────────────────────────────────
# log_conversation
# ────────────────────────────────────────────────────────────

class TestLogConversation:

    def test_creates_file( self, sched, vault_root ):
        _Path = sched.log_conversation( "TESTORG", "TESTPROJ", "session-1", "測試對話內容" )
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )

    def test_content_written( self, sched, vault_root ):
        _Path = sched.log_conversation( "TESTORG", "TESTPROJ", "session-1", "測試對話內容" )
        _Content = _read( vault_root, _Path )
        assert "測試對話內容" in _Content

    def test_overwrites_on_same_session( self, sched, vault_root ):
        """相同 session name 的第二次呼叫應覆寫第一次內容。"""
        sched.log_conversation( "TESTORG", "TESTPROJ", "session-x", "第一次內容" )
        _P2 = sched.log_conversation( "TESTORG", "TESTPROJ", "session-x", "第二次內容" )
        _Content = _read( vault_root, _P2 )
        assert "第二次內容" in _Content

    def test_path_contains_session_name( self, sched ):
        _Path = sched.log_conversation( "TESTORG", "TESTPROJ", "my-session", "content" )
        assert "my-session" in _Path


# ────────────────────────────────────────────────────────────
# generate_ai_weekly_analysis
# ────────────────────────────────────────────────────────────

class TestGenerateAiWeeklyAnalysis:

    def test_creates_file( self, sched, vault_root ):
        _Path = sched.generate_ai_weekly_analysis( "2026-04-04" )
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )
        assert "-W" in _Path

    def test_idempotent( self, sched ):
        _P1 = sched.generate_ai_weekly_analysis( "2026-04-04" )
        _P2 = sched.generate_ai_weekly_analysis( "2026-04-04" )
        assert _P1 == _P2

    def test_same_week_same_path( self, sched ):
        _P1 = sched.generate_ai_weekly_analysis( "2026-04-06" )
        _P2 = sched.generate_ai_weekly_analysis( "2026-04-10" )
        assert _P1 == _P2

    def test_contains_week_range( self, sched, vault_root ):
        _Path = sched.generate_ai_weekly_analysis( "2026-04-04" )
        _Content = _read( vault_root, _Path )
        assert "2026" in _Content

    def test_conversation_scan_no_error( self, sched, vault_root ):
        """無任何對話檔案時也不拋出例外。"""
        _Path = sched.generate_ai_weekly_analysis( "2026-04-04" )
        assert _Path

    def test_includes_project_if_conv_exists( self, sched, vault_root ):
        """conversations/ 有符合週範圍的檔案時，分析中應出現該專案名稱。"""
        _ConvAbs = (
            vault_root / "workspaces" / "TESTORG" / "projects" / "TESTPROJ" / "conversations"
        )
        _ConvAbs.mkdir( parents=True, exist_ok=True )
        ( _ConvAbs / "2026-04-07_test.md" ).write_text( "對話內容", encoding="utf-8" )
        _Path = sched.generate_ai_weekly_analysis( "2026-04-07" )
        assert "TESTPROJ" in _read( vault_root, _Path )


# ────────────────────────────────────────────────────────────
# generate_ai_monthly_analysis
# ────────────────────────────────────────────────────────────

class TestGenerateAiMonthlyAnalysis:

    def test_creates_file( self, sched, vault_root ):
        _Path = sched.generate_ai_monthly_analysis( "2026-04-04" )
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )
        assert "2026-04" in _Path

    def test_idempotent( self, sched ):
        _P1 = sched.generate_ai_monthly_analysis( "2026-04-04" )
        _P2 = sched.generate_ai_monthly_analysis( "2026-04-20" )
        assert _P1 == _P2

    def test_different_months_different_path( self, sched ):
        _P1 = sched.generate_ai_monthly_analysis( "2026-04-04" )
        _P2 = sched.generate_ai_monthly_analysis( "2026-05-01" )
        assert _P1 != _P2

    def test_contains_year_month( self, sched, vault_root ):
        _Path = sched.generate_ai_monthly_analysis( "2026-04-04" )
        _Content = _read( vault_root, _Path )
        assert "2026-04" in _Content
