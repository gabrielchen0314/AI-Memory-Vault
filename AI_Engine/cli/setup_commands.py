"""
CLI 設定指令集
互動式 Setup Wizard、單一區段設定、完整重新設定。

從 main.py 提取，減少 main.py 的行數。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.5
@date 2026.04.10
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


SETUP_SECTIONS = [ "vault", "user", "org", "llm" ]


def run_setup_wizard():
    """互動式初始化引導（首次或 --setup 強制）。"""
    from config import AppConfig, UserConfig, LLMConfig, ENGINE_DIR
    from services.setup import SetupService

    print( "=" * 60 )
    print( "  AI Memory Vault v3 -- 初始化設定" )
    print( "=" * 60 )

    # Step 1: Vault 路徑
    if getattr( sys, 'frozen', False ):
        _DefaultVault = str( Path.home() / "AI-Memory-Vault" / "Vault" )
    else:
        _DefaultVault = str( ENGINE_DIR.parent / "Vault" )
    _VaultInput = input( f"\nVault 目前路徑 [{_DefaultVault}]（選填，直接 Enter 略過）：" ).strip()
    _VaultPath = _VaultInput if _VaultInput else _DefaultVault
    _VaultPath = os.path.realpath( _VaultPath )

    # Step 2: 使用者資訊
    _UserName = input( "使用者名稱（@author 顯示名）：" ).strip()
    _UserEmail = input( "電子郵件（選填，直接 Enter 略過）：" ).strip()

    # Step 3: 所屬組織（可多個）
    print( "\n所屬組織（完成後直接 Enter）：" )
    _Orgs: list = []
    while True:
        _OrgInput = input( f"  組織名稱（已加 {len( _Orgs )} 個，Enter 完成）：" ).strip()
        if not _OrgInput:
            break
        _OrgLower = _OrgInput.lower()
        _Invalid = set( _OrgLower ) - set( "abcdefghijklmnopqrstuvwxyz0123456789-_" )
        if _Invalid:
            print( f"  [!] 包含不允許的字元：{''.join( sorted( _Invalid ) )}" )
            continue
        if _OrgLower in _Orgs:
            print( f"  [i] {_OrgLower} 已加入" )
            continue
        _Orgs.append( _OrgLower )
        print( f"  [+] 已加入：{_OrgLower}" )

    # Step 4: LLM 設定
    print( "\nLLM 供應商：" )
    print( "  1. ollama（本機，免費，需另行安裝）" )
    print( "  2. gemini（Google API，需要 API Key）" )
    _LlmChoice = input( "選擇：" ).strip()

    _LlmProvider = "gemini" if _LlmChoice == "2" else "ollama"
    _ApiKeyEnv = ""
    if _LlmProvider == "gemini":
        _ApiKeyEnv = "GOOGLE_API_KEY"
        print( f"[i] 請確認環境變數 {_ApiKeyEnv} 已設定。" )

    _Config = AppConfig(
        vault_path=_VaultPath,
        user=UserConfig(
            name=_UserName,
            email=_UserEmail,
            organizations=_Orgs,
        ),
        llm=LLMConfig( provider=_LlmProvider, api_key_env=_ApiKeyEnv ),
    )

    SetupService.run_setup( _Config )

    print( "\n[完成] 初始化成功！現在可以使用：" )
    print( "   vault-cli.exe              -> CLI 互動模式" )
    print( "   vault-mcp.exe              -> MCP 伺服器" )


def run_full_reconfigure():
    """依序引導所有設定區段（Vault → 使用者 → 組織 → LLM）。不重建資料庫。"""
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
        ( "1/4", "Vault 路徑",  setup_vault_path ),
        ( "2/4", "使用者資訊",  setup_user_info ),
        ( "3/4", "組織管理",    run_org_wizard ),
        ( "4/4", "LLM 設定",   setup_llm ),
    ]

    for _Step, _Label, _Fn in _SECTION_ORDER:
        print( "" )
        print( f"  ── [{_Step}] {_Label} ──" )
        _Fn()

    print( "" )
    print( "  ✅ 所有設定已完成！" )
    print( "" )


def dispatch_section( iSection: str ):
    """根據區段名稱分發至對應的設定函式。"""
    _Map = {
        "vault": setup_vault_path,
        "user":  setup_user_info,
        "org":   run_org_wizard,
        "llm":   setup_llm,
    }
    _Fn = _Map.get( iSection )
    if _Fn:
        _Fn()


def setup_vault_path():
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


def setup_user_info():
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


def setup_llm():
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


def run_org_wizard():
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

            os.makedirs( os.path.join( _VaultRoot, _P.org_rules_dir( _NewOrg ) ),    exist_ok=True )
            os.makedirs( os.path.join( _VaultRoot, _P.org_projects_dir( _NewOrg ) ), exist_ok=True )

            print( f"  ✅ 已新增：{_NewOrg}" )

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

    _Config.user.organizations = _CurrentOrgs
    ConfigManager.save( _Config )

    print( "" )
    if _CurrentOrgs:
        print( f"  ✅ 組織設定已儲存：{', '.join( _CurrentOrgs )}" )
    else:
        print( "  ⚠️  組織清單為空" )
    print( "" )
