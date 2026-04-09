"""
MigrationManager 單元測試

覆蓋核心邏輯：
  - check()            首次初始化、未變更、各欄位單獨觸發、多欄位同時觸發
  - reset_index()      清除 ChromaDB 目錄、清除 DB 檔案、更新 meta、不存在時不拋出
  - describe_changes() 欄位標籤翻譯、多欄位格式

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.4
@date 2026.04.06
"""
import json
import os
import pytest


# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────

@pytest.fixture
def meta_dir( tmp_path, monkeypatch ):
    """
    將 migration._META_FILE 重定向至 tmp_path，避免汙染真實 DATA_DIR。
    同時確保 chroma_db / record.sql 路徑也在 tmp_path 下。
    """
    import core.migration as _Mod
    _MetaFile = tmp_path / "vault_meta.json"
    monkeypatch.setattr( _Mod, "_META_FILE", _MetaFile )
    return tmp_path


@pytest.fixture
def migconf( config, tmp_path ):
    """
    設定 AppConfig 的資料庫路徑指向 tmp_path（讓 reset_index 可安全測試）。
    """
    config.database.chroma_dir   = str( tmp_path / "chroma_db" )
    config.database.record_db    = str( tmp_path / "record.sql" )
    return config


# ────────────────────────────────────────────────────────────
# check()
# ────────────────────────────────────────────────────────────

class TestCheck:

    def test_first_run_creates_meta( self, migconf, meta_dir ):
        """首次呼叫（meta 不存在）→ 建立 meta，回傳 (False, [])。"""
        from core.migration import MigrationManager, _META_FILE
        _Needs, _Changes = MigrationManager.check( migconf )
        assert _Needs is False
        assert _Changes == []
        assert _META_FILE.is_file()

    def test_first_run_meta_content( self, migconf, meta_dir ):
        """建立的 meta 包含所有必要欄位。"""
        from core.migration import MigrationManager, _META_FILE
        MigrationManager.check( migconf )
        _Data = json.loads( _META_FILE.read_text( encoding="utf-8" ) )
        for _Key in ( "schema_version", "embedding_model", "chunk_size",
                      "chunk_overlap", "collection_name" ):
            assert _Key in _Data

    def test_no_change_returns_false( self, migconf, meta_dir ):
        """設定未變更時回傳 (False, [])。"""
        from core.migration import MigrationManager
        MigrationManager.check( migconf )          # 建立 meta
        _Needs, _Changes = MigrationManager.check( migconf )
        assert _Needs is False
        assert _Changes == []

    def test_embedding_model_change( self, migconf, meta_dir ):
        """embedding_model 變更時偵測到差異。"""
        from core.migration import MigrationManager
        MigrationManager.check( migconf )
        migconf.embedding.model = "new-model-xyz"
        _Needs, _Changes = MigrationManager.check( migconf )
        assert _Needs is True
        _Keys = [ k for k, _, _ in _Changes ]
        assert "embedding_model" in _Keys

    def test_chunk_size_change( self, migconf, meta_dir ):
        """chunk_size 變更時偵測到差異。"""
        from core.migration import MigrationManager
        MigrationManager.check( migconf )
        migconf.embedding.chunk_size = 9999
        _Needs, _Changes = MigrationManager.check( migconf )
        assert _Needs is True
        _Keys = [ k for k, _, _ in _Changes ]
        assert "chunk_size" in _Keys

    def test_chunk_overlap_change( self, migconf, meta_dir ):
        """chunk_overlap 變更時偵測到差異。"""
        from core.migration import MigrationManager
        MigrationManager.check( migconf )
        migconf.embedding.chunk_overlap = 9999
        _Needs, _Changes = MigrationManager.check( migconf )
        assert _Needs is True

    def test_collection_name_change( self, migconf, meta_dir ):
        """collection_name 變更時偵測到差異。"""
        from core.migration import MigrationManager
        MigrationManager.check( migconf )
        migconf.database.collection_name = "my_new_collection"
        _Needs, _Changes = MigrationManager.check( migconf )
        assert _Needs is True

    def test_multiple_changes( self, migconf, meta_dir ):
        """多欄位同時變更時，changes 清單包含所有差異欄位。"""
        from core.migration import MigrationManager
        MigrationManager.check( migconf )
        migconf.embedding.model = "model-a"
        migconf.embedding.chunk_size = 1000
        _Needs, _Changes = MigrationManager.check( migconf )
        assert _Needs is True
        _Keys = [ k for k, _, _ in _Changes ]
        assert "embedding_model" in _Keys
        assert "chunk_size" in _Keys

    def test_changes_tuple_format( self, migconf, meta_dir ):
        """changes 清單中每項為 (key, old_val, new_val) 格式。"""
        from core.migration import MigrationManager
        MigrationManager.check( migconf )
        _OldModel = migconf.embedding.model
        migconf.embedding.model = "brand-new-model"
        _, _Changes = MigrationManager.check( migconf )
        _Entry = next( (c for c in _Changes if c[0] == "embedding_model"), None )
        assert _Entry is not None
        _Key, _Old, _New = _Entry
        assert _Old == _OldModel
        assert _New == "brand-new-model"

    def test_corrupted_meta_treated_as_first_run( self, migconf, meta_dir ):
        """meta 檔案損壞時，視為首次初始化，回傳 (False, [])。"""
        from core.migration import MigrationManager, _META_FILE
        _META_FILE.write_text( "NOT_JSON{{{{", encoding="utf-8" )
        _Needs, _Changes = MigrationManager.check( migconf )
        assert _Needs is False
        assert _Changes == []


# ────────────────────────────────────────────────────────────
# reset_index()
# ────────────────────────────────────────────────────────────

class TestResetIndex:

    def _make_chroma( self, tmp_path ) -> "Path":
        """建立假的 chroma_db 目錄（含一個假檔案）。"""
        _Dir = tmp_path / "chroma_db"
        _Dir.mkdir()
        ( _Dir / "chroma.sqlite3" ).write_bytes( b"\x00" * 64 )
        return _Dir

    def _make_record_db( self, tmp_path ) -> "Path":
        """建立假的 record_manager_cache.sql 檔案。"""
        _File = tmp_path / "record.sql"
        _File.write_bytes( b"\x00" * 32 )
        return _File

    def test_removes_chroma_dir( self, migconf, meta_dir, tmp_path ):
        """reset_index 應刪除 ChromaDB 目錄。"""
        from core.migration import MigrationManager
        _Dir = self._make_chroma( tmp_path )
        migconf.database.chroma_dir = str( _Dir )
        MigrationManager.reset_index( migconf )
        assert not _Dir.exists()

    def test_removes_record_db( self, migconf, meta_dir, tmp_path ):
        """reset_index 應刪除 RecordManager SQLite 檔。"""
        from core.migration import MigrationManager
        _DbFile = self._make_record_db( tmp_path )
        migconf.database.record_db = str( _DbFile )
        MigrationManager.reset_index( migconf )
        assert not _DbFile.exists()

    def test_updates_meta( self, migconf, meta_dir, tmp_path ):
        """reset_index 後，meta 應更新為目前設定。"""
        from core.migration import MigrationManager, _META_FILE
        MigrationManager.check( migconf )
        migconf.embedding.model = "updated-model"
        MigrationManager.reset_index( migconf )
        _Data = json.loads( _META_FILE.read_text( encoding="utf-8" ) )
        assert _Data["embedding_model"] == "updated-model"

    def test_ok_when_chroma_not_exist( self, migconf, meta_dir ):
        """ChromaDB 目錄不存在時不拋出例外，回傳 (True, msg)。"""
        from core.migration import MigrationManager
        _Ok, _Msg = MigrationManager.reset_index( migconf )
        assert _Ok is True

    def test_ok_when_record_db_not_exist( self, migconf, meta_dir ):
        """record DB 不存在時不拋出例外，回傳 (True, msg)。"""
        from core.migration import MigrationManager
        _Ok, _Msg = MigrationManager.reset_index( migconf )
        assert _Ok is True

    def test_returns_true_on_success( self, migconf, meta_dir ):
        """成功時回傳 (True, 非空字串)。"""
        from core.migration import MigrationManager
        _Ok, _Msg = MigrationManager.reset_index( migconf )
        assert _Ok is True
        assert _Msg

    def test_subsequent_check_no_migration( self, migconf, meta_dir ):
        """reset_index 後，check() 應回傳 (False, [])（meta 已更新）。"""
        from core.migration import MigrationManager
        MigrationManager.check( migconf )
        migconf.embedding.model = "changed-model"
        MigrationManager.reset_index( migconf )
        _Needs, _Changes = MigrationManager.check( migconf )
        assert _Needs is False
        assert _Changes == []


# ────────────────────────────────────────────────────────────
# describe_changes()
# ────────────────────────────────────────────────────────────

class TestDescribeChanges:

    def test_contains_embedding_model_label( self ):
        """embedding_model 鍵應翻譯為中文標籤。"""
        from core.migration import MigrationManager
        _Changes = [ ("embedding_model", "old", "new") ]
        _Text = MigrationManager.describe_changes( _Changes )
        assert "嵌入模型" in _Text

    def test_contains_chunk_size_label( self ):
        """chunk_size 鍵應翻譯為中文標籤。"""
        from core.migration import MigrationManager
        _Changes = [ ("chunk_size", 500, 1000) ]
        _Text = MigrationManager.describe_changes( _Changes )
        assert "Chunk 大小" in _Text

    def test_contains_collection_name_label( self ):
        """collection_name 鍵應翻譯為中文。"""
        from core.migration import MigrationManager
        _Changes = [ ("collection_name", "old_col", "new_col") ]
        _Text = MigrationManager.describe_changes( _Changes )
        assert "ChromaDB" in _Text

    def test_shows_old_and_new_values( self ):
        """輸出文字應包含舊值與新值。"""
        from core.migration import MigrationManager
        _Changes = [ ("embedding_model", "old-model", "new-model") ]
        _Text = MigrationManager.describe_changes( _Changes )
        assert "old-model" in _Text
        assert "new-model" in _Text

    def test_multiple_changes_multiline( self ):
        """多個變更應以多行呈現。"""
        from core.migration import MigrationManager
        _Changes = [
            ("embedding_model", "a", "b"),
            ("chunk_size", 500, 1000),
        ]
        _Text = MigrationManager.describe_changes( _Changes )
        assert _Text.count( "\n" ) >= 1

    def test_empty_changes( self ):
        """空清單回傳空字串。"""
        from core.migration import MigrationManager
        _Text = MigrationManager.describe_changes( [] )
        assert _Text == ""
