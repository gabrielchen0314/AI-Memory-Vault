"""
ChromaDB 備份服務
定期壓縮 ChromaDB 目錄至備份存放區，保留最近 N 份。

備份存放位置：DATA_DIR/backups/
檔案格式：    chroma_backup_{YYYY-MM-DD_HHmmss}.zip
保留策略：    預設保留最近 7 份（可配置）

使用方式：
    from services.backup import BackupService

    svc = BackupService( config )
    path, err = svc.backup_chromadb()   # 建立一份備份
    svc.cleanup( max_keep=7 )           # 清理舊備份

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.7
@date 2026.04.10
"""
from __future__ import annotations

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from config import AppConfig, DATA_DIR
from core.logger import get_logger

_logger = get_logger( __name__ )

## <summary>備份存放目錄</summary>
BACKUP_DIR: Path = DATA_DIR / "backups"

## <summary>預設保留份數</summary>
DEFAULT_MAX_KEEP: int = 7


class BackupService:
    """ChromaDB 備份與清理服務。"""

    #region 成員變數
    ## <summary>應用程式設定</summary>
    m_Config: AppConfig
    #endregion

    def __init__( self, iConfig: AppConfig ):
        self.m_Config = iConfig

    def backup_chromadb( self ) -> Tuple[Optional[str], Optional[str]]:
        """
        壓縮 ChromaDB 目錄為 zip 備份。

        Returns:
            (backup_path, error_message) — 成功時 error 為 None。
        """
        _ChromaPath = Path( self.m_Config.database.get_chroma_path() )

        if not _ChromaPath.is_dir():
            return None, f"ChromaDB 目錄不存在：{_ChromaPath}"

        BACKUP_DIR.mkdir( parents=True, exist_ok=True )

        _Timestamp = datetime.now().strftime( "%Y-%m-%d_%H%M%S" )
        _ZipName   = f"chroma_backup_{_Timestamp}.zip"
        _ZipPath   = BACKUP_DIR / _ZipName

        try:
            with zipfile.ZipFile( _ZipPath, "w", zipfile.ZIP_DEFLATED ) as _Zf:
                for _Root, _Dirs, _Files in os.walk( _ChromaPath ):
                    for _File in _Files:
                        _FilePath = Path( _Root ) / _File
                        _ArcName  = _FilePath.relative_to( _ChromaPath.parent )
                        _Zf.write( _FilePath, _ArcName )

            _SizeMb = _ZipPath.stat().st_size / ( 1024 * 1024 )
            _logger.info( "ChromaDB 備份完成：%s（%.1f MB）", _ZipName, _SizeMb )
            return str( _ZipPath ), None

        except Exception as _Ex:
            _logger.error( "ChromaDB 備份失敗：%s", _Ex )
            # 清除不完整的 zip
            if _ZipPath.is_file():
                _ZipPath.unlink()
            return None, str( _Ex )

    def cleanup( self, iMaxKeep: int = DEFAULT_MAX_KEEP ) -> int:
        """
        清理舊備份，僅保留最近 N 份。

        Args:
            iMaxKeep: 最多保留幾份備份。

        Returns:
            刪除的備份數量。
        """
        if not BACKUP_DIR.is_dir():
            return 0

        _Backups = sorted(
            BACKUP_DIR.glob( "chroma_backup_*.zip" ),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        _ToDelete = _Backups[iMaxKeep:]
        for _Old in _ToDelete:
            _Old.unlink()
            _logger.info( "已清除舊備份：%s", _Old.name )

        return len( _ToDelete )

    def list_backups( self ) -> list:
        """
        列出所有現有備份。

        Returns:
            [{"name": str, "size_mb": float, "created": str}, ...]
        """
        if not BACKUP_DIR.is_dir():
            return []

        _Result = []
        for _F in sorted( BACKUP_DIR.glob( "chroma_backup_*.zip" ), reverse=True ):
            _Stat = _F.stat()
            _Result.append({
                "name":     _F.name,
                "size_mb":  round( _Stat.st_size / ( 1024 * 1024 ), 2 ),
                "created":  datetime.fromtimestamp( _Stat.st_mtime ).strftime( "%Y-%m-%d %H:%M:%S" ),
            })

        return _Result
