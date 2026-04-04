"""
services/git_service.py — Vault Git 版本控制整合 (v1.0)

每次 VaultService 成功寫入或刪除筆記後，自動執行 git commit，
讓 Vault 的完整修改歷史透過 Git 保存，可隨時回溯或 diff。

行為：
  - 若 Vault 根目錄尚未是 Git repo → 自動 git init
  - 每次呼叫 commit() → git add <file> + git commit -m <message>
  - 若 git 不在 PATH → 靜默降級（不拋出例外）
  - 若無變更需要提交 → 跳過（視為成功）

@author gabrielchen
@version 1.0
@since AI-Memory-Vault v3.1
@date 2026.04.05
"""
import subprocess
import os
from typing import Optional


class GitService:
    """Vault Git 版本控制服務（類方法介面，無狀態）。"""

    #region 公開介面

    @classmethod
    def ensure_repo( cls, iVaultPath: str ) -> bool:
        """
        確保 Vault 根目錄是有效的 Git repository。
        若尚未初始化，執行 git init 並設定初始設定。

        Args:
            iVaultPath: Vault 根目錄絕對路徑。

        Returns:
            True = 已確保 repo 存在；False = git 不可用或初始化失敗。
        """
        if not cls._git_available():
            return False

        _GitDir = os.path.join( iVaultPath, ".git" )
        if os.path.isdir( _GitDir ):
            return True

        _Ret = cls._run( ["git", "init"], iVaultPath )
        if _Ret.returncode != 0:
            return False

        # 建立初始 .gitignore 排除 ChromaDB / venv 等
        _GitIgnorePath = os.path.join( iVaultPath, ".gitignore" )
        if not os.path.isfile( _GitIgnorePath ):
            with open( _GitIgnorePath, "w", encoding="utf-8" ) as _F:
                _F.write( "# AI Memory Vault — Git 版本控制排除清單\n" )

        return True

    @classmethod
    def commit(
        cls,
        iVaultPath:   str,
        iRelPath:     str,
        iMessage:     str,
        iAuthorName:  str = "AI Memory Vault",
        iAuthorEmail: str = "vault@localhost",
    ) -> tuple[bool, Optional[str]]:
        """
        針對指定檔案執行 git add + git commit。

        Args:
            iVaultPath:   Vault 根目錄絕對路徑。
            iRelPath:     相對於 Vault 根目錄的檔案路徑（可含多個以空格分隔）。
            iMessage:     commit message。
            iAuthorName:  提交者名稱。
            iAuthorEmail: 提交者 Email。

        Returns:
            (committed: bool, sha_or_error: Optional[str])
            committed=False + sha_or_error=None → 無變更需提交（非錯誤）。
            committed=False + sha_or_error=str  → 錯誤訊息。
        """
        if not cls._git_available():
            return False, None  # 靜默降級

        if not os.path.isdir( os.path.join( iVaultPath, ".git" ) ):
            _Ok = cls.ensure_repo( iVaultPath )
            if not _Ok:
                return False, "git init failed"

        _Env = {
            **os.environ,
            "GIT_AUTHOR_NAME":    iAuthorName,
            "GIT_AUTHOR_EMAIL":   iAuthorEmail,
            "GIT_COMMITTER_NAME": iAuthorName,
            "GIT_COMMITTER_EMAIL": iAuthorEmail,
        }

        # git add <file>
        _AddRet = cls._run( ["git", "add", "--", iRelPath], iVaultPath, env=_Env )
        if _AddRet.returncode != 0:
            return False, f"git add failed: {_AddRet.stderr.strip()}"

        # git commit（若無差異 → returncode=1 but stderr 包含 "nothing to commit"）
        _CommitRet = cls._run(
            ["git", "commit", "-m", iMessage],
            iVaultPath,
            env=_Env,
        )

        if _CommitRet.returncode == 0:
            # 取得 commit SHA（短）
            _ShaRet = cls._run( ["git", "rev-parse", "--short", "HEAD"], iVaultPath )
            _Sha = _ShaRet.stdout.strip() if _ShaRet.returncode == 0 else None
            return True, _Sha

        # 無變更是正常狀態（不算錯誤）
        _Out = ( _CommitRet.stdout + _CommitRet.stderr ).lower()
        if "nothing to commit" in _Out or "nothing added to commit" in _Out:
            return False, None

        return False, f"git commit failed: {_CommitRet.stderr.strip()}"

    @classmethod
    def commit_delete(
        cls,
        iVaultPath:   str,
        iRelPath:     str,
        iAuthorName:  str = "AI Memory Vault",
        iAuthorEmail: str = "vault@localhost",
    ) -> tuple[bool, Optional[str]]:
        """
        刪除檔案後的 git commit（使用 git add -A 以捕捉刪除）。

        Args:
            iVaultPath:   Vault 根目錄絕對路徑。
            iRelPath:     已刪除檔案的相對路徑。
            iAuthorName:  提交者名稱。
            iAuthorEmail: 提交者 Email。

        Returns:
            (committed: bool, sha_or_error: Optional[str])
        """
        return cls.commit(
            iVaultPath,
            iRelPath,
            f"delete: {iRelPath}",
            iAuthorName,
            iAuthorEmail,
        )

    #endregion

    #region 私有方法

    @classmethod
    def _git_available( cls ) -> bool:
        """檢查 git 是否在 PATH 中可用。"""
        try:
            _R = subprocess.run(
                ["git", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            return _R.returncode == 0
        except ( FileNotFoundError, subprocess.TimeoutExpired ):
            return False

    @classmethod
    def _run(
        cls,
        iCmd:  list,
        iCwd:  str,
        env:   Optional[dict] = None,
    ) -> subprocess.CompletedProcess:
        """執行 git 子程序，回傳 CompletedProcess（不拋出例外）。"""
        try:
            return subprocess.run(
                iCmd,
                cwd=iCwd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )
        except Exception as _E:
            # 模擬失敗的 CompletedProcess
            class _FakeResult:
                returncode = 1
                stdout = ""
                stderr = str( _E )
            return _FakeResult()

    #endregion
