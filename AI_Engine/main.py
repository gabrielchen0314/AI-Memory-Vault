"""
AI Memory Vault v3 — 入口程式
支援 CLI / API / MCP 三種模式，首次執行自動觸發 Setup Wizard。

用法：
    python main.py                          → 啟動 Setup Wizard（首次）或 CLI 模式
    python main.py --mode cli               → CLI 互動模式
    python main.py --mode api               → FastAPI 伺服器
    python main.py --mode mcp               → MCP stdio 伺服器
    python main.py --scheduler              → 啟動 APScheduler 守護模式（週/月/日自動生成）
    python main.py --setup                  → 強制重新執行完整 Setup Wizard
    python main.py --setup-section vault    → 僅設定 Vault 路徑
    python main.py --setup-section user     → 僅設定使用者資訊
    python main.py --setup-section org      → 組織管理（新增/移除）
    python main.py --setup-section llm      → 僅設定 LLM

@author gabrielchen
@version 3.3
@since AI-Memory-Vault 3.0
@date 2026.04.04
"""
import argparse
import sys
import os

# 確保 AI_Engine 目錄在 sys.path 中
_ENGINE_DIR = os.path.dirname( os.path.abspath( __file__ ) )
if _ENGINE_DIR not in sys.path:
    sys.path.insert( 0, _ENGINE_DIR )
os.chdir( _ENGINE_DIR )

## <summary>--setup-section 允許的區段名稱</summary>
SETUP_SECTIONS = [ "vault", "user", "org", "llm" ]


def main():
    """主入口：解析參數 → 檢查初始化 → 分發執行模式。"""
    _Parser = argparse.ArgumentParser( description="AI Memory Vault v3 — 記憶庫引擎" )
    _Parser.add_argument(
        "--mode",
        choices=[ "cli", "api", "mcp" ],
        default="cli",
        help="啟動模式：cli（互動終端）/ api（FastAPI 伺服器）/ mcp（MCP stdio 伺服器）",
    )
    _Parser.add_argument(
        "--setup",
        action="store_true",
        help="強制重新執行完整 Setup Wizard",
    )
    _Parser.add_argument(
        "--setup-section",
        choices=SETUP_SECTIONS,
        help="設定特定區段：vault / user / org / llm",
    )
    _Parser.add_argument(
        "--reconfigure",
        action="store_true",
        help="重新設定所有區段（保留資料庫，逐項引導）",
    )
    _Parser.add_argument(
        "--scheduler",
        action="store_true",
        help="啟動 APScheduler 守護模式（weekly/monthly/daily 自動生成摘要）",
    )
    _Parser.add_argument(
        "--menu",
        action="store_true",
        help="CLI 選單模式（方向鍵圓式選單，預設 CLI 指令列）",
    )
    _Args = _Parser.parse_args()

    from config import ConfigManager

    # ── 首次執行或強制 Setup ──────────────────────────────
    if _Args.setup or not ConfigManager.is_initialized():
        _run_setup_wizard()
        if _Args.setup:
            return

    # ── 重新完整設定（保留資料庫，逐項引導） ──────────────
    if _Args.reconfigure:
        _run_full_reconfigure()
        return

    # ── 單一區段設定 ──────────────────────────────────────
    if _Args.setup_section:
        _dispatch_section( _Args.setup_section )
        return

    # ── 排程守護模式 ──────────────────────────────────────
    if _Args.scheduler:
        _start_scheduler()
        return

    # ── 正常啟動 ──────────────────────────────────────────
    _Config = ConfigManager.load()

    # MCP stdio 模式：bootstrap 期間同時封鎖 Python 層（sys.stdout）
    # 和 fd 層（fd 1），防止 C 擴展汙染 JSON-RPC 通道。
    # bootstrap 結束後兩層都必須還原，FastMCP 用 sys.stdout 寫回應。
    if _Args.mode == "mcp":
        _RealStdout = sys.stdout
        sys.stdout = sys.stderr
        _SavedFd1 = os.dup( 1 )
        os.dup2( 2, 1 )

    _bootstrap( _Config )

    if _Args.mode == "api":
        _start_api( _Config )
    elif _Args.mode == "mcp":
        # 還原 fd 1 + sys.stdout → FastMCP stdio transport 需要兩層都正常
        os.dup2( _SavedFd1, 1 )
        os.close( _SavedFd1 )
        sys.stdout = _RealStdout
        _start_mcp()
    else:
        _start_cli( _Config, getattr( _Args, "menu", False ) )


def _bootstrap( iConfig ):
    """
    初始化所有核心模組（Embeddings → VectorStore → VaultService）。

    Args:
        iConfig: 應用程式設定。
    """
    from core import embeddings as _EmbModule
    from core import vectorstore as _VsModule
    from services.vault import VaultService

    _EmbModule.initialize( iConfig.embedding.model )
    _VsModule.initialize(
        iChromaDir=iConfig.database.get_chroma_path(),
        iRecordDbUrl=iConfig.database.get_record_db_url(),
        iCollectionName=iConfig.database.collection_name,
    )
    VaultService.initialize( iConfig )


def _run_setup_wizard():
    """互動式初始化引導（首次或 --setup 強制）。"""
    from config import AppConfig, UserConfig, LLMConfig, ENGINE_DIR
    from services.setup import SetupService

    print( "=" * 60 )
    print( "  🚀 AI Memory Vault v3 — 初始化引導" )
    print( "=" * 60 )

    # Step 1: Vault 路徑
    _DefaultVault = str( ENGINE_DIR.parent / "Vault" )
    _VaultInput = input( f"\n📁 Vault 路徑 [{_DefaultVault}]: " ).strip()
    _VaultPath = _VaultInput if _VaultInput else _DefaultVault
    _VaultPath = os.path.realpath( _VaultPath )

    # Step 2: 使用者資訊
    _UserName = input( "👤 使用者名稱（用於 @author）: " ).strip()
    _UserEmail = input( "📧 電子信箱（可留空）: " ).strip()

    # Step 3: 所屬組織（可多個）
    print( "\n🏢 所屬組織（輸入完畢按 Enter 跳過）：" )
    _Orgs: list = []
    while True:
        _OrgInput = input( f"  組織名稱（已加入 {len( _Orgs )} 個，Enter 完成）: " ).strip()
        if not _OrgInput:
            break
        _OrgLower = _OrgInput.lower()
        _Invalid = set( _OrgLower ) - set( "abcdefghijklmnopqrstuvwxyz0123456789-_" )
        if _Invalid:
            print( f"  ❌ 名稱含無效字元：{''.join( sorted( _Invalid ) )}" )
            continue
        if _OrgLower in _Orgs:
            print( f"  ℹ️  {_OrgLower} 已加入" )
            continue
        _Orgs.append( _OrgLower )
        print( f"  ✅ 已加入：{_OrgLower}" )

    # Step 4: LLM 設定
    print( "\n🤖 LLM 供應商：" )
    print( "  1. ollama（本地免費，需先安裝）" )
    print( "  2. gemini（Google API，需 API Key）" )
    _LlmChoice = input( "選擇 [1]: " ).strip()

    _LlmProvider = "gemini" if _LlmChoice == "2" else "ollama"
    _ApiKeyEnv = ""
    if _LlmProvider == "gemini":
        _ApiKeyEnv = "GOOGLE_API_KEY"
        print( f"💡 請確認環境變數 {_ApiKeyEnv} 已設定。" )

    # 組裝 Config
    _Config = AppConfig(
        vault_path=_VaultPath,
        user=UserConfig(
            name=_UserName,
            email=_UserEmail,
            organizations=_Orgs,
        ),
        llm=LLMConfig( provider=_LlmProvider, api_key_env=_ApiKeyEnv ),
    )

    # 執行初始化
    SetupService.run_setup( _Config )

    print( "\n✅ 設定完成！可以開始使用：" )
    print( "   python main.py              → CLI 模式" )
    print( "   python main.py --mode mcp   → MCP 模式" )
    print( "   python main.py --mode api   → API 模式" )


# ── 重新完整設定 ──────────────────────────────────────────
def _run_full_reconfigure():
    """
    依序引導所有設定區段（Vault → 使用者 → 組織 → LLM）。
    不重建資料庫，僅更新 config.json。
    """
    print( "" )
    print( "=" * 56 )
    print( "  ⚠️  重新完整設定" )
    print( "=" * 56 )
    print( "  將依序引導您重新設定所有項目。" )
    print( "  每個欄位按 Enter 可保持原值，資料庫不受影響。" )
    print( "" )

    _Confirm = input( "確定要重新設定？(y/Enter = 確定，n = 取消): " ).strip().lower()
    if _Confirm == "n":
        print( "  已取消。" )
        return

    _SECTION_ORDER = [
        ( "1/4", "Vault 路徑",  _setup_vault_path ),
        ( "2/4", "使用者資訊",  _setup_user_info ),
        ( "3/4", "組織管理",    _run_org_wizard ),
        ( "4/4", "LLM 設定",   _setup_llm ),
    ]

    for _Step, _Label, _Fn in _SECTION_ORDER:
        print( "" )
        print( f"  ── [{_Step}] {_Label} ──" )
        _Fn()

    print( "" )
    print( "  ✅ 所有設定已完成！" )
    print( "" )


# ── 單一區段設定 ──────────────────────────────────────────
def _dispatch_section( iSection: str ):
    """
    根據區段名稱分發至對應的設定函式。

    Args:
        iSection: vault / user / org / llm
    """
    _Map = {
        "vault": _setup_vault_path,
        "user":  _setup_user_info,
        "org":   _run_org_wizard,
        "llm":   _setup_llm,
    }
    _Fn = _Map.get( iSection )
    if _Fn:
        _Fn()


def _setup_vault_path():
    """互動式修改 Vault 路徑。"""
    from config import ConfigManager

    _Config = ConfigManager.load()
    _Current = _Config.vault_path

    print( "" )
    print( "=" * 56 )
    print( "  📁 Vault 路徑設定" )
    print( "=" * 56 )
    print( f"  目前：{_Current}" )
    print( "" )

    _Input = input( f"新路徑（Enter 保持不變）: " ).strip()
    if not _Input:
        print( "  保持不變。" )
        return

    _Config.vault_path = os.path.realpath( _Input )
    ConfigManager.save( _Config )
    print( f"  ✅ Vault 路徑已更新：{_Config.vault_path}" )
    print( "" )


def _setup_user_info():
    """互動式修改使用者名稱與信箱。"""
    from config import ConfigManager

    _Config = ConfigManager.load()

    print( "" )
    print( "=" * 56 )
    print( "  👤 使用者資訊設定" )
    print( "=" * 56 )
    print( f"  目前名稱：{_Config.user.name or '（未設定）'}" )
    print( f"  目前信箱：{_Config.user.email or '（未設定）'}" )
    print( "" )

    _Name = input( f"使用者名稱（Enter 保持不變）[{_Config.user.name}]: " ).strip()
    if _Name:
        _Config.user.name = _Name

    _Email = input( f"電子信箱（Enter 保持不變）[{_Config.user.email}]: " ).strip()
    if _Email:
        _Config.user.email = _Email

    ConfigManager.save( _Config )
    print( f"  ✅ 使用者資訊已儲存" )
    print( "" )


def _setup_llm():
    """互動式修改 LLM 設定。"""
    from config import ConfigManager

    _Config = ConfigManager.load()

    print( "" )
    print( "=" * 56 )
    print( "  🤖 LLM 設定" )
    print( "=" * 56 )
    print( f"  目前供應商：{_Config.llm.provider}" )
    print( f"  目前模型  ：{_Config.llm.model or '（預設）'}" )
    if _Config.llm.provider == "ollama":
        print( f"  Ollama URL：{_Config.llm.ollama_base_url}" )
    print( "" )

    print( "  供應商選項：" )
    print( "    1. ollama（本地免費）" )
    print( "    2. gemini（Google API）" )
    _Default = "1" if _Config.llm.provider == "ollama" else "2"
    _Choice = input( f"  選擇（Enter 保持不變）[{_Default}]: " ).strip() or _Default

    if _Choice == "2":
        _Config.llm.provider = "gemini"
        _Config.llm.api_key_env = _Config.llm.api_key_env or "GOOGLE_API_KEY"
        print( f"  💡 請確認環境變數 {_Config.llm.api_key_env} 已設定。" )
    else:
        _Config.llm.provider = "ollama"
        _UrlInput = input(
            f"  Ollama URL（Enter 保持不變）[{_Config.llm.ollama_base_url}]: "
        ).strip()
        if _UrlInput:
            _Config.llm.ollama_base_url = _UrlInput

    _ModelInput = input(
        f"  模型名稱（Enter 保持不變）[{_Config.llm.model or '留空=供應商預設'}]: "
    ).strip()
    if _ModelInput:
        _Config.llm.model = _ModelInput

    ConfigManager.save( _Config )
    print( f"  ✅ LLM 設定已儲存" )
    print( "" )


def _run_org_wizard():
    """
    組織管理精靈。
    - 顯示目前所有已加入的組織
    - 操作選項：新增組織 / 移除組織
    - 移除時可選擇是否同時刪除 Vault 目錄
    """
    import shutil
    from config import ConfigManager

    _Config     = ConfigManager.load()
    _VaultRoot  = _Config.vault_path
    _P          = _Config.paths
    _WorkspacesAbs = os.path.join( _VaultRoot, _P.workspaces )

    # ── 掃描 Vault 現有組織目錄（排除 _global 保留目錄） ──
    def _scan_vault_orgs() -> list:
        _Result = []
        if os.path.isdir( _WorkspacesAbs ):
            for _Name in sorted( os.listdir( _WorkspacesAbs ) ):
                if not _Name.startswith( "_" ) and os.path.isdir(
                    os.path.join( _WorkspacesAbs, _Name )
                ):
                    _Result.append( _Name )
        return _Result

    _CurrentOrgs: list = list( _Config.user.organizations )

    while True:
        print( "" )
        print( "=" * 56 )
        print( "  🏢 AI Memory Vault — 組織管理" )
        print( "=" * 56 )
        if _CurrentOrgs:
            for _Org in _CurrentOrgs:
                print( f"  • {_Org}" )
        else:
            print( "  ⚠️  尚未加入任何組織" )
        print( "" )
        print( "  1.  ＋ 新增組織" )
        print( "  2.  － 移除組織" )
        print( "" )

        _Input = input( "選擇操作 [1-2]（Enter 離開）: " ).strip()

        if not _Input:
            break

        # ── 新增組織 ──────────────────────────────────────
        if _Input == "1":
            _VaultOrgs   = _scan_vault_orgs()
            _Unregistered = [ _O for _O in _VaultOrgs if _O not in _CurrentOrgs ]

            print( "" )
            print( "  --- 新增組織 ---" )

            _AddOptions: list = list( _Unregistered )
            _ADD_INPUT = "＋ 輸入新名稱"
            _AddOptions.append( _ADD_INPUT )

            for _Idx, _Opt in enumerate( _AddOptions, 1 ):
                print( f"  {_Idx}.  {_Opt}" )

            print( "" )
            _Sel = input( f"選擇 [1-{len( _AddOptions )}]（Enter 取消）: " ).strip()
            if not _Sel:
                continue

            if not _Sel.isdigit() or not ( 1 <= int( _Sel ) <= len( _AddOptions ) ):
                print( "  ❌ 無效選項" )
                continue

            _NewOrg = _AddOptions[ int( _Sel ) - 1 ]

            if _NewOrg == _ADD_INPUT:
                _NewOrg = input( "  輸入名稱（英文小寫，例如 mycompany）: " ).strip().lower()
                if not _NewOrg:
                    continue
                _Invalid = set( _NewOrg ) - set( "abcdefghijklmnopqrstuvwxyz0123456789-_" )
                if _Invalid:
                    print( f"  ❌ 名稱含無效字元：{''.join( sorted( _Invalid ) )}" )
                    continue

            if _NewOrg in _CurrentOrgs:
                print( f"  ℹ️  {_NewOrg} 已在清單中" )
                continue

            _CurrentOrgs.append( _NewOrg )

            # 立即建立目錄骨架
            os.makedirs( os.path.join( _VaultRoot, _P.org_rules_dir( _NewOrg ) ),    exist_ok=True )
            os.makedirs( os.path.join( _VaultRoot, _P.org_projects_dir( _NewOrg ) ), exist_ok=True )

            print( f"  ✅ 已新增：{_NewOrg}" )

        # ── 移除組織 ──────────────────────────────────────
        elif _Input == "2":
            if not _CurrentOrgs:
                print( "  ℹ️  目前沒有可移除的組織" )
                continue

            print( "" )
            print( "  --- 移除組織 ---" )
            for _Idx, _Org in enumerate( _CurrentOrgs, 1 ):
                print( f"  {_Idx}.  {_Org}" )

            print( "" )
            _Sel = input( f"選擇要移除的組織 [1-{len( _CurrentOrgs )}]（Enter 取消）: " ).strip()
            if not _Sel:
                continue

            if not _Sel.isdigit() or not ( 1 <= int( _Sel ) <= len( _CurrentOrgs ) ):
                print( "  ❌ 無效選項" )
                continue

            _Target = _CurrentOrgs[ int( _Sel ) - 1 ]

            # 問是否同時刪除 Vault 目錄
            _OrgDirAbs = os.path.join( _WorkspacesAbs, _Target )
            _DirExists  = os.path.isdir( _OrgDirAbs )

            print( "" )
            if _DirExists:
                print( f"  ⚠️  Vault 目錄：{_OrgDirAbs}" )
                print( "  是否同時刪除目錄內的所有資料？" )
                print( "  1.  僅從設定移除（保留 Vault 目錄）" )
                print( "  2.  移除設定 + 刪除 Vault 目錄" )
                print( "" )
                _DelSel = input( "選擇 [1-2]（Enter 取消）: " ).strip()
                if not _DelSel:
                    continue
                if _DelSel not in ( "1", "2" ):
                    print( "  ❌ 無效選項" )
                    continue
                _DeleteDir = ( _DelSel == "2" )
            else:
                _DeleteDir = False

            _CurrentOrgs.remove( _Target )

            if _DeleteDir:
                shutil.rmtree( _OrgDirAbs )
                print( f"  ✅ 已移除：{_Target}（目錄已刪除）" )
            else:
                print( f"  ✅ 已移除：{_Target}（Vault 目錄保留）" )

        else:
            print( "  ❌ 無效選項" )

    # ── 儲存設定 ──────────────────────────────────────────
    _Config.user.organizations = _CurrentOrgs
    ConfigManager.save( _Config )

    print( "" )
    if _CurrentOrgs:
        print( f"  ✅ 組織設定已儲存：{', '.join( _CurrentOrgs )}" )
    else:
        print( "  ⚠️  組織清單為空" )
    print( "" )


def _start_scheduler():
    """啟動 APScheduler 守護模式（非互動，阻塞直到 Ctrl+C）。"""
    from config import ConfigManager
    from services.auto_scheduler import AutoScheduler

    _Config = ConfigManager.load()
    _Sched  = AutoScheduler( _Config )
    _Sched.start()
    _Sched.block()


def _start_cli( iConfig, iMenu: bool = False ):
    """啟動 CLI 互動模式。"""
    from cli.repl import VaultRepl
    _Repl = VaultRepl( iConfig )
    if iMenu:
        _Repl.run_menu()
    else:
        _Repl.run()


def _start_api( iConfig ):
    """啟動 FastAPI 伺服器。"""
    print( "🔧 API 模式尚未實作（V3 Phase 2）" )


def _start_mcp():
    """啟動 MCP stdio 伺服器。"""
    from mcp_app.server import run_mcp_server
    run_mcp_server()


if __name__ == "__main__":
    main()
