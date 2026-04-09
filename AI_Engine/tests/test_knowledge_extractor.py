"""
KnowledgeExtractor 單元測試

覆蓋所有公開/私有方法的核心邏輯：
  - extract()            正常建立、冪等追加、session 過濾、輸入驗證
  - _scan_conversations()  目錄掃描、副檔名過濾、session 過濾、結果格式
  - _extract_key_points()  標題/條列萃取、去重、上限 15 筆
  - _append_sources()      追加去重、讀檔失敗回傳錯誤
  - _render_knowledge_card() frontmatter、區塊結構、來源連結、重點清單

所有 Fixtures 定義於 conftest.py（vault_root / config）。
VaultService 透過 patch_extractor_vault fixture 在本檔替換為 filesystem stub。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.2
@date 2026.04.05
"""
import os
import pytest


# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

def _read( vault_root, rel_path: str ) -> str:
    """Read a file from vault_root given its relative path."""
    _Abs = os.path.join( str( vault_root ), rel_path )
    with open( _Abs, "r", encoding="utf-8" ) as _F:
        return _F.read()


def _write_conv( vault_root, org: str, project: str, filename: str, content: str ):
    """
    建立一個對話檔案至 vault_root/workspaces/{org}/projects/{project}/conversations/{filename}。
    """
    _Dir = vault_root / "workspaces" / org / "projects" / project / "conversations"
    _Dir.mkdir( parents=True, exist_ok=True )
    ( _Dir / filename ).write_text( content, encoding="utf-8" )


# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────

@pytest.fixture
def patch_extractor_vault( monkeypatch, vault_root ):
    """
    Stub VaultService in services.knowledge_extractor：
    - write_note → 直接寫檔至 vault_root（不依賴 ChromaDB）
    - read_note  → 直接從 vault_root 讀取
    """
    import services.knowledge_extractor as _ExtMod
    _Root = str( vault_root )

    class _FakeVault:

        @classmethod
        def write_note( cls, iFilePath: str, iContent: str, iMode: str = "overwrite" ):
            _Abs = os.path.join( _Root, iFilePath )
            os.makedirs( os.path.dirname( _Abs ), exist_ok=True )
            with open( _Abs, "w", encoding="utf-8" ) as _F:
                _F.write( iContent )
            return { "chars": len( iContent ), "total_chunks": 1, "index_stats": {} }, None

        @classmethod
        def read_note( cls, iFilePath: str ):
            _Abs = os.path.join( _Root, iFilePath )
            if not os.path.isfile( _Abs ):
                return None, f"File not found: {iFilePath}"
            with open( _Abs, "r", encoding="utf-8" ) as _F:
                return _F.read(), None

    monkeypatch.setattr( _ExtMod, "VaultService", _FakeVault )
    yield _FakeVault


@pytest.fixture
def extractor( config, patch_extractor_vault, vault_root ):
    """KnowledgeExtractor 實例（VaultService 已 stub）。"""
    ( vault_root / "knowledge" ).mkdir( exist_ok=True )
    from services.knowledge_extractor import KnowledgeExtractor
    return KnowledgeExtractor( config )


# ────────────────────────────────────────────────────────────
# extract()
# ────────────────────────────────────────────────────────────

class TestExtract:

    def test_creates_knowledge_card( self, extractor, vault_root ):
        """正常流程：對話存在時建立知識卡片。"""
        _write_conv( vault_root, "TESTORG", "TESTPROJ", "2026-04-04_s1.md", "# Title\n\n- Point A\n" )

        _Path, _Err = extractor.extract( "TESTORG", "TESTPROJ", "my-topic" )

        assert _Err is None
        assert _Path is not None
        assert os.path.isfile( os.path.join( str( vault_root ), _Path ) )

    def test_returns_relative_path( self, extractor, vault_root ):
        """回傳路徑必須是相對路徑。"""
        _write_conv( vault_root, "TESTORG", "TESTPROJ", "2026-04-04_s1.md", "# T\n" )

        _Path, _ = extractor.extract( "TESTORG", "TESTPROJ", "rel-path-test" )

        assert not os.path.isabs( _Path )

    def test_path_in_knowledge_dir( self, extractor, vault_root ):
        """卡片必須寫入 knowledge/ 目錄。"""
        _write_conv( vault_root, "TESTORG", "TESTPROJ", "2026-04-04_s1.md", "# T\n" )

        _Path, _ = extractor.extract( "TESTORG", "TESTPROJ", "dir-check" )

        assert _Path.startswith( "knowledge/" )

    def test_topic_slug_in_path( self, extractor, vault_root ):
        """topic 轉換為 slug 並出現在檔名中。"""
        _write_conv( vault_root, "TESTORG", "TESTPROJ", "2026-04-04_s1.md", "# T\n" )

        _Path, _ = extractor.extract( "TESTORG", "TESTPROJ", "My Topic Name" )

        assert "my-topic-name" in _Path

    def test_card_has_required_frontmatter( self, extractor, vault_root ):
        """卡片 frontmatter 包含必要欄位。"""
        _write_conv( vault_root, "TESTORG", "TESTPROJ", "2026-04-04_s1.md", "# T\n" )

        _Path, _ = extractor.extract( "TESTORG", "TESTPROJ", "frontmatter-test" )
        _Content = _read( vault_root, _Path )

        assert "type: knowledge" in _Content
        assert "source_org: TESTORG" in _Content
        assert "source_project: TESTPROJ" in _Content

    def test_card_has_required_sections( self, extractor, vault_root ):
        """卡片包含所有必要 Markdown 區塊。"""
        _write_conv( vault_root, "TESTORG", "TESTPROJ", "2026-04-04_s1.md", "# T\n" )

        _Path, _ = extractor.extract( "TESTORG", "TESTPROJ", "sections-test" )
        _Content = _read( vault_root, _Path )

        for _Section in [ "## 核心概念", "## 問題表現", "## 解法", "## 注意事項", "## 來源對話" ]:
            assert _Section in _Content, f"缺少區塊：{_Section}"

    def test_idempotent_appends_sources( self, extractor, vault_root ):
        """同一 topic 呼叫兩次：第二次追加新來源，不覆蓋卡片內容，回傳同路徑。"""
        _write_conv( vault_root, "TESTORG", "TESTPROJ", "2026-04-04_first.md", "# F\n" )

        _Path1, _ = extractor.extract( "TESTORG", "TESTPROJ", "idempotent-test" )

        _write_conv( vault_root, "TESTORG", "TESTPROJ", "2026-04-05_second.md", "# S\n" )
        _Path2, _ = extractor.extract( "TESTORG", "TESTPROJ", "idempotent-test" )

        assert _Path1 == _Path2
        _Content = _read( vault_root, _Path1 )
        assert "2026-04-05_second.md" in _Content

    def test_idempotent_no_duplicate_sources( self, extractor, vault_root ):
        """相同來源不應重複追加（呼叫 3 次只出現 1 次）。"""
        _write_conv( vault_root, "TESTORG", "TESTPROJ", "2026-04-04_only.md", "# O\n" )

        _Path, _ = extractor.extract( "TESTORG", "TESTPROJ", "no-dup" )
        extractor.extract( "TESTORG", "TESTPROJ", "no-dup" )
        extractor.extract( "TESTORG", "TESTPROJ", "no-dup" )

        _Content = _read( vault_root, _Path )
        assert _Content.count( "2026-04-04_only.md" ) == 1

    def test_session_filter_includes_match( self, extractor, vault_root ):
        """iSession 指定時，符合的對話應出現在來源。"""
        _write_conv( vault_root, "TESTORG", "SFPROJ", "2026-04-04_target.md", "## Hit\n" )
        _write_conv( vault_root, "TESTORG", "SFPROJ", "2026-04-04_other.md", "## Miss\n" )

        _Path, _Err = extractor.extract( "TESTORG", "SFPROJ", "session-filter", "target" )

        assert _Err is None
        _Content = _read( vault_root, _Path )
        assert "target" in _Content

    def test_session_filter_excludes_non_match( self, extractor, vault_root ):
        """iSession 指定時，不符合的對話不應在來源連結中。"""
        _write_conv( vault_root, "TESTORG", "SFPROJ2", "2026-04-04_target.md", "## Hit\n" )
        _write_conv( vault_root, "TESTORG", "SFPROJ2", "2026-04-04_other.md", "## Miss\n" )

        _Path, _ = extractor.extract( "TESTORG", "SFPROJ2", "session-excl", "target" )
        _Content = _read( vault_root, _Path )
        assert "other" not in _Content

    def test_validation_missing_org( self, extractor ):
        """org 為空時回傳 Error。"""
        _, _Err = extractor.extract( "", "TESTPROJ", "topic" )
        assert _Err is not None
        assert "Error" in _Err

    def test_validation_missing_project( self, extractor ):
        """project 為空時回傳 Error。"""
        _, _Err = extractor.extract( "TESTORG", "", "topic" )
        assert _Err is not None

    def test_validation_missing_topic( self, extractor ):
        """topic 為空時回傳 Error。"""
        _, _Err = extractor.extract( "TESTORG", "TESTPROJ", "" )
        assert _Err is not None

    def test_no_conversations_returns_error( self, extractor ):
        """conversations/ 目錄不存在時回傳 Error，不拋出例外。"""
        _, _Err = extractor.extract( "TESTORG", "NO_CONV_PROJ", "topic" )
        assert _Err is not None
        assert "Error" in _Err


# ────────────────────────────────────────────────────────────
# _scan_conversations()
# ────────────────────────────────────────────────────────────

class TestScanConversations:

    def test_empty_when_dir_not_exist( self, extractor ):
        """conversations/ 不存在時回傳空清單，不拋出例外。"""
        _Results = extractor._scan_conversations( "TESTORG", "GHOST_PROJ", None )
        assert _Results == []

    def test_finds_md_files( self, extractor, vault_root ):
        """正常掃描：找到所有 .md 檔案。"""
        _write_conv( vault_root, "TESTORG", "SCAN_PROJ", "2026-04-04_alpha.md", "# A\n" )
        _write_conv( vault_root, "TESTORG", "SCAN_PROJ", "2026-04-05_beta.md",  "# B\n" )

        _Results = extractor._scan_conversations( "TESTORG", "SCAN_PROJ", None )

        assert len( _Results ) == 2

    def test_ignores_non_md_files( self, extractor, vault_root ):
        """非 .md 檔案不應被納入。"""
        _Dir = vault_root / "workspaces" / "TESTORG" / "projects" / "NONMD_PROJ" / "conversations"
        _Dir.mkdir( parents=True, exist_ok=True )
        ( _Dir / "image.png" ).write_bytes( b"\x00" )
        ( _Dir / "note.md" ).write_text( "# Note\n", encoding="utf-8" )

        _Results = extractor._scan_conversations( "TESTORG", "NONMD_PROJ", None )

        assert len( _Results ) == 1
        assert _Results[0]["file_name"] == "note.md"

    def test_session_filter( self, extractor, vault_root ):
        """session 過濾：只回傳檔名含 session 字串的項目。"""
        _write_conv( vault_root, "TESTORG", "SF_PROJ", "2026-04-04_phase1.md", "# P1\n" )
        _write_conv( vault_root, "TESTORG", "SF_PROJ", "2026-04-04_phase2.md", "# P2\n" )

        _Results = extractor._scan_conversations( "TESTORG", "SF_PROJ", "phase1" )

        assert len( _Results ) == 1
        assert "phase1" in _Results[0]["file_name"]

    def test_result_has_required_keys( self, extractor, vault_root ):
        """每個結果項目必須包含 rel_path / file_name / date / session。"""
        _write_conv( vault_root, "TESTORG", "KEY_PROJ", "2026-04-04_session-a.md", "# A\n" )

        _Results = extractor._scan_conversations( "TESTORG", "KEY_PROJ", None )

        assert len( _Results ) == 1
        for _Key in [ "rel_path", "file_name", "date", "session" ]:
            assert _Key in _Results[0]

    def test_parses_date_and_session( self, extractor, vault_root ):
        """date 欄位應為 YYYY-MM-DD，session 欄為檔名去日期後的部分。"""
        _write_conv( vault_root, "TESTORG", "PARSE_PROJ", "2026-04-04_my-session.md", "# A\n" )

        _Results = extractor._scan_conversations( "TESTORG", "PARSE_PROJ", None )

        assert _Results[0]["date"] == "2026-04-04"
        assert _Results[0]["session"] == "my-session"

    def test_sorted_alphabetically( self, extractor, vault_root ):
        """結果應按檔名排序（字母序）。"""
        _write_conv( vault_root, "TESTORG", "SORT_PROJ", "2026-04-05_z.md", "# Z\n" )
        _write_conv( vault_root, "TESTORG", "SORT_PROJ", "2026-04-04_a.md", "# A\n" )

        _Results = extractor._scan_conversations( "TESTORG", "SORT_PROJ", None )

        assert _Results[0]["file_name"] < _Results[1]["file_name"]


# ────────────────────────────────────────────────────────────
# _extract_key_points()
# ────────────────────────────────────────────────────────────

class TestExtractKeyPoints:

    def _make_sources( self, vault_root, files: dict ) -> list:
        """
        Helper：建立測試用對話檔，回傳 sources 清單。
        files: { "relative/path.md": "content" }
        """
        _Sources = []
        for _RelPath, _Content in files.items():
            _Abs = vault_root / _RelPath.replace( "/", os.sep )
            _Abs.parent.mkdir( parents=True, exist_ok=True )
            _Abs.write_text( _Content, encoding="utf-8" )
            _Sources.append( {
                "rel_path":  _RelPath,
                "file_name": _Abs.name,
                "date":      "",
                "session":   "",
            } )
        return _Sources

    def test_extracts_headings( self, extractor, vault_root ):
        """## 二級標題應被萃取。"""
        _Sources = self._make_sources( vault_root, {
            "tmp_kp/h.md": "## 重要標題\n## 第二標題\n"
        } )
        _Points = extractor._extract_key_points( _Sources )
        assert "重要標題" in _Points
        assert "第二標題" in _Points

    def test_extracts_bullets( self, extractor, vault_root ):
        """- 條列重點應被萃取（長度需 > 5 字元，含 "- " 前綴；萃取後保留前綴）。"""
        _Sources = self._make_sources( vault_root, {
            "tmp_kp/b.md": "- 重點條列一\n- 重點條列二\n"
        } )
        _Points = extractor._extract_key_points( _Sources )
        # 條列萃取後 lstrip("#").strip() 仍保留 "- " 前綴
        assert any( "重點條列一" in _P for _P in _Points )
        assert any( "重點條列二" in _P for _P in _Points )

    def test_deduplicates( self, extractor, vault_root ):
        """相同文字只保留一次。"""
        _Sources = self._make_sources( vault_root, {
            "tmp_kp/d.md": "## Same\n## Same\n- Same\n"
        } )
        _Points = extractor._extract_key_points( _Sources )
        assert _Points.count( "Same" ) == 1

    def test_max_15_items( self, extractor, vault_root ):
        """萃取結果不超過 15 筆。"""
        _Lines = "\n".join( f"- Point {i}" for i in range( 30 ) )
        _Sources = self._make_sources( vault_root, { "tmp_kp/m.md": _Lines } )
        _Points = extractor._extract_key_points( _Sources )
        assert len( _Points ) <= 15

    def test_graceful_for_missing_file( self, extractor ):
        """來源檔案不存在時不拋出例外，回傳空清單。"""
        _Sources = [ {
            "rel_path":  "ghost/missing.md",
            "file_name": "missing.md",
            "date":      "",
            "session":   "",
        } ]
        _Points = extractor._extract_key_points( _Sources )
        assert isinstance( _Points, list )

    def test_empty_for_no_sources( self, extractor ):
        """空清單輸入回傳空清單。"""
        _Points = extractor._extract_key_points( [] )
        assert _Points == []


# ────────────────────────────────────────────────────────────
# _append_sources()
# ────────────────────────────────────────────────────────────

class TestAppendSources:

    def test_appends_new_source( self, extractor, vault_root ):
        """新來源連結應被追加至卡片末尾。"""
        _Abs = vault_root / "knowledge" / "test-append.md"
        _Abs.write_text( "# Card\n\n## 來源對話\n", encoding="utf-8" )

        _Sources = [ {
            "rel_path":  "workspaces/ORG/projects/PROJ/conversations/2026-04-05_s.md",
            "file_name": "2026-04-05_s.md",
            "date":      "2026-04-05",
            "session":   "s",
        } ]
        _, _Err = extractor._append_sources( "knowledge/test-append.md", _Sources )

        assert _Err is None
        _Content = _read( vault_root, "knowledge/test-append.md" )
        assert "2026-04-05" in _Content

    def test_skips_duplicate_source( self, extractor, vault_root ):
        """已存在的連結不重複追加（出現次數 = 1）。"""
        _SrcLink = "- [2026-04-05 s](workspaces/ORG/projects/PROJ/conversations/2026-04-05_s.md)"
        _Abs = vault_root / "knowledge" / "test-nodup.md"
        _Abs.write_text( f"# Card\n\n{_SrcLink}\n", encoding="utf-8" )

        _Sources = [ {
            "rel_path":  "workspaces/ORG/projects/PROJ/conversations/2026-04-05_s.md",
            "file_name": "2026-04-05_s.md",
            "date":      "2026-04-05",
            "session":   "s",
        } ]
        extractor._append_sources( "knowledge/test-nodup.md", _Sources )

        _Content = _read( vault_root, "knowledge/test-nodup.md" )
        assert _Content.count( "2026-04-05_s.md" ) == 1

    def test_error_when_file_not_found( self, extractor ):
        """卡片不存在時回傳錯誤，不拋出例外。"""
        _, _Err = extractor._append_sources( "knowledge/ghost.md", [] )
        assert _Err is not None


# ────────────────────────────────────────────────────────────
# _render_knowledge_card()
# ────────────────────────────────────────────────────────────

class TestRenderKnowledgeCard:

    def test_contains_all_sections( self, extractor ):
        """渲染結果包含所有必要 Markdown 區塊。"""
        _Content = extractor._render_knowledge_card(
            "test-slug", "Test Topic", "TESTORG", "TESTPROJ",
            "2026-04-04", [], []
        )
        for _Section in [ "## 核心概念", "## 問題表現", "## 解法", "## 注意事項", "## 來源對話" ]:
            assert _Section in _Content, f"缺少區塊：{_Section}"

    def test_slug_in_frontmatter( self, extractor ):
        """topic slug 出現在 frontmatter。"""
        _Content = extractor._render_knowledge_card(
            "my-slug", "My Topic", "ORG", "PROJ", "2026-04-04", [], []
        )
        assert "topic: my-slug" in _Content

    def test_org_project_in_frontmatter( self, extractor ):
        """source_org / source_project 出現在 frontmatter。"""
        _Content = extractor._render_knowledge_card(
            "slug", "topic", "MYORG", "MYPROJ", "2026-04-04", [], []
        )
        assert "source_org: MYORG" in _Content
        assert "source_project: MYPROJ" in _Content

    def test_sources_rendered_in_section( self, extractor ):
        """來源對話清單正確渲染為 Markdown 連結。"""
        _Sources = [ {
            "rel_path":  "p/c.md",
            "file_name": "c.md",
            "date":      "2026-04-04",
            "session":   "s1",
        } ]
        _Content = extractor._render_knowledge_card(
            "slug", "topic", "ORG", "PROJ", "2026-04-04", _Sources, []
        )
        assert "2026-04-04 s1" in _Content
        assert "p/c.md" in _Content

    def test_keypoints_in_draft( self, extractor ):
        """重點清單渲染至核心概念區塊。"""
        _Points = [ "點 A", "點 B" ]
        _Content = extractor._render_knowledge_card(
            "slug", "topic", "ORG", "PROJ", "2026-04-04", [], _Points
        )
        assert "點 A" in _Content
        assert "點 B" in _Content

    def test_empty_keypoints_placeholder( self, extractor ):
        """重點清單為空時顯示填入提示文字。"""
        _Content = extractor._render_knowledge_card(
            "slug", "topic", "ORG", "PROJ", "2026-04-04", [], []
        )
        assert "請從來源對話填入重點" in _Content
