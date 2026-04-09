"""
Vault 索引遷移偵測與重建機制

偵測以下設定變更並在需要時觸發完整重建：
  - embedding.model        嵌入模型（維度/語意空間不同 → 向量不相容）
  - embedding.chunk_size   chunk 裁切大小（切塊結果不同 → 索引不一致）
  - embedding.chunk_overlap chunk 重疊大小（同上）
  - database.collection_name ChromaDB 集合名稱

Meta 檔案存放位置：DATA_DIR/vault_meta.json
（frozen 模式：%APPDATA%/AI-Memory-Vault/，dev：AI_Engine/）

使用方式：
    from core.migration import MigrationManager

    # 啟動時偵測
    needs, changes = MigrationManager.check( config )
    if needs:
        MigrationManager.reset_index( config )
        vault_service.sync()          # 重建索引

    # CLI --reindex：強制全部重建
    MigrationManager.reset_index( config )

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.4
@date 2026.04.06
"""
import json
import logging
import shutil
from pathlib import Path
from typing import List, Tuple

from config import AppConfig, DATA_DIR

_logger = logging.getLogger( __name__ )

## <summary>格式版本號，schema 破壞性變更時遞增</summary>
_SCHEMA_VERSION: int = 1
## <summary>meta 檔案路徑（DATA_DIR 下，frozen 時走 AppData）</summary>
_META_FILE: Path = DATA_DIR / "vault_meta.json"


def _build_signature( iConfig: AppConfig ) -> dict:
    """根據目前設定建立比對用的 signature dict。"""
    return {
        "schema_version":  _SCHEMA_VERSION,
        "embedding_model": iConfig.embedding.model,
        "chunk_size":      iConfig.embedding.chunk_size,
        "chunk_overlap":   iConfig.embedding.chunk_overlap,
        "collection_name": iConfig.database.collection_name,
    }


def _read_meta() -> dict:
    """
    讀取已儲存的 meta 檔案。

    Returns:
        解析後的 dict；若不存在或格式損壞，回傳空 dict。
    """
    if not _META_FILE.is_file():
        return {}
    try:
        return json.loads( _META_FILE.read_text( encoding="utf-8" ) )
    except (json.JSONDecodeError, OSError):
        _logger.warning( "vault_meta.json 讀取失敗，視為首次初始化。" )
        return {}


def _write_meta( iConfig: AppConfig ) -> None:
    """將目前設定的 signature 寫入 META_FILE。"""
    _META_FILE.parent.mkdir( parents=True, exist_ok=True )
    _META_FILE.write_text(
        json.dumps( _build_signature( iConfig ), indent=2, ensure_ascii=False ),
        encoding="utf-8",
    )


class MigrationManager:
    """向量索引遷移管理器（靜態方法）。"""

    # ─────────────────────────────────────────────────────────
    # 公開 API
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def check( iConfig: AppConfig ) -> Tuple[bool, List[Tuple[str, object, object]]]:
        """
        比較目前設定與上次 meta，判斷是否需要重建索引。

        首次呼叫（meta 不存在）→ 寫入 meta，視為不需要重建。

        Args:
            iConfig: 應用程式設定。

        Returns:
            (needs_reindex: bool, changes: List[(key, old_val, new_val)])
        """
        _Meta = _read_meta()

        if not _Meta:
            # 第一次初始化：建立 meta，不需要重建
            _write_meta( iConfig )
            _logger.debug( "vault_meta.json 已建立（首次初始化）。" )
            return False, []

        _Sig    = _build_signature( iConfig )
        _Changed: list = []

        for _Key, _NewVal in _Sig.items():
            if _Key == "schema_version":
                continue
            _OldVal = _Meta.get( _Key )
            if _OldVal != _NewVal:
                _Changed.append( (_Key, _OldVal, _NewVal) )

        if _Changed:
            _logger.warning(
                "偵測到索引相關設定已變更（需重建）：%s",
                { k: (o, n) for k, o, n in _Changed },
            )

        return bool( _Changed ), _Changed

    @staticmethod
    def reset_index( iConfig: AppConfig ) -> Tuple[bool, str]:
        """
        清除 ChromaDB 目錄 + RecordManager SQLite + 更新 meta。
        清除後須由呼叫方觸發 VaultService.sync() 重建索引。

        Args:
            iConfig: 應用程式設定（用於定位資料庫路徑）。

        Returns:
            (success: bool, message: str)
        """
        _ChromaPath = Path( iConfig.database.get_chroma_path() )
        # RecordManager URL 格式：sqlite:///絕對路徑
        _DbUrl = iConfig.database.get_record_db_url()
        _DbPath = Path( _DbUrl.replace( "sqlite:///", "", 1 ) )

        try:
            # 1. 清除 ChromaDB 目錄
            if _ChromaPath.exists():
                shutil.rmtree( _ChromaPath )
                _logger.info( "ChromaDB 目錄已清除：%s", _ChromaPath )

            # 2. 清除 RecordManager SQLite
            if _DbPath.is_file():
                _DbPath.unlink()
                _logger.info( "RecordManager DB 已清除：%s", _DbPath )

            # 3. 清除 singleton cache（避免舊實例持有已刪除目錄的 handle）
            import core.vectorstore as _VS
            _VS.get_vectorstore.cache_clear()
            _VS.get_record_manager.cache_clear()

            # 4. 更新 meta → 記錄新設定，下次啟動不再偵測為「需要重建」
            _write_meta( iConfig )
            _logger.info( "vault_meta.json 已更新。" )

            return True, "索引已清除，請執行同步以重建（sync_vault）。"

        except OSError as _E:
            _logger.error( "reset_index 失敗：%s", _E )
            return False, f"清除失敗：{_E}"

    @staticmethod
    def describe_changes( iChanges: List[Tuple[str, object, object]] ) -> str:
        """
        將 check() 回傳的 changes 轉換為使用者可讀的說明文字。

        Args:
            iChanges: (key, old_val, new_val) 的清單。

        Returns:
            多行說明字串。
        """
        _Labels = {
            "embedding_model": "嵌入模型",
            "chunk_size":      "Chunk 大小",
            "chunk_overlap":   "Chunk 重疊",
            "collection_name": "ChromaDB 集合名稱",
        }
        _Lines = []
        for _Key, _Old, _New in iChanges:
            _Label = _Labels.get( _Key, _Key )
            _Lines.append( f"  {_Label}：{_Old!r} → {_New!r}" )
        return "\n".join( _Lines )
