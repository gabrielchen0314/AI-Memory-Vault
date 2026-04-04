"""
.env 啟動前驗證與互動設定精靈
若偵測到 .env 缺少必要設定，引導使用者輸入或跳過，
並說明跳過後哪些功能將無法使用。

@author gabrielchen
@version 1.1
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ── 路徑 ──────────────────────────────────────────────────────────────────────
_ENV_PATH: Path = Path( __file__ ).resolve().parent / ".env"

# ── 各模式所需套件定義 ────────────────────────────────────────────────────────
#   格式：( import_module_name, pip_install_spec, 功能說明 )

## <summary>所有模式共用的基礎套件</summary>
_BASE_PACKAGES: list = [
    ( "langchain",            "langchain>=0.3.0",            "LangChain 核心框架" ),
    ( "langchain_core",       "langchain-core>=0.3.0",       "LangChain 核心元件" ),
    ( "langchain_community",  "langchain-community>=0.3.0",  "LangChain 社群工具" ),
    ( "sentence_transformers","sentence-transformers>=3.0.0", "向量嵌入模型" ),
    ( "chromadb",             "chromadb>=0.5.0",             "向量資料庫" ),
    ( "langchain_chroma",     "langchain-chroma>=0.2.0",     "ChromaDB 整合" ),
    ( "rank_bm25",            "rank_bm25>=0.2.0",            "BM25 混合搜尋" ),
    ( "yaml",                 "PyYAML>=6.0",                 "YAML 解析" ),
    ( "pydantic_settings",    "pydantic-settings>=2.0.0",    "設定管理" ),
    ( "sqlalchemy",           "SQLAlchemy>=2.0.0",           "資料庫 ORM" ),
]

## <summary>各 LLM provider 專屬套件</summary>
_LLM_PACKAGES: dict = {
    "gemini": [
        ( "langchain_google_genai", "langchain-google-genai>=2.0.0", "Google Gemini 整合" ),
    ],
    "ollama": [
        ( "langchain_ollama", "langchain-ollama>=0.2.0", "Ollama 本地模型整合" ),
    ],
}

## <summary>各模式額外需要的套件</summary>
_MODE_EXTRA_PACKAGES: dict = {
    "cli": [],
    "api": [
        ( "fastapi",  "fastapi>=0.115.0",          "FastAPI 框架" ),
        ( "uvicorn",  "uvicorn[standard]>=0.30.0",  "ASGI 伺服器" ),
        ( "httpx",    "httpx>=0.27.0",              "HTTP 客戶端（Webhook）" ),
    ],
    "mcp": [
        ( "mcp", "mcp[cli]>=1.0.0", "MCP stdio 伺服器" ),
    ],
}

# ── 設定群組定義 ──────────────────────────────────────────────────────────────
#   每個群組包含：
#     name             - 顯示名稱
#     description      - 功能說明
#     condition_key    - 條件欄位（可選）：只有當此欄位的值符合 condition_value 才啟用
#     condition_value  - 條件值（可選）
#     fields           - 欄位清單
#     disabled_features - 跳過後無法使用的功能清單
#
_SETUP_GROUPS: list = [
    {
        "name": "LLM 供應商",
        "description": "決定使用哪個 AI 模型引擎（必填；建議初次使用者選 gemini）",
        "fields": [
            {
                "key":      "LLM_PROVIDER",
                "label":    "LLM 供應商（gemini / ollama）",
                "default":  "gemini",
                "secret":   False,
                "required": True,
            },
        ],
        "disabled_features": [],  # 有預設值，不需特別警告
    },
    {
        "name": "Google Gemini API 金鑰",
        "description": "使用 Google Gemini 模型（LLM_PROVIDER=gemini 時必填）",
        "condition_key":   "LLM_PROVIDER",
        "condition_value": "gemini",
        "fields": [
            {
                "key":      "GOOGLE_API_KEY",
                "label":    "Google API Key",
                "default":  "",
                "secret":   True,
                "required": True,
            },
        ],
        "disabled_features": [
            "CLI 對話模式（所有 AI 問答）",
            "API 模式對話端點（/chat）",
            "LINE 機器人 AI 回覆",
        ],
    },
    {
        "name": "Ollama 本地伺服器",
        "description": "使用本機 Ollama 模型（LLM_PROVIDER=ollama 時可選）",
        "condition_key":   "LLM_PROVIDER",
        "condition_value": "ollama",
        "fields": [
            {
                "key":      "OLLAMA_BASE_URL",
                "label":    "Ollama Base URL",
                "default":  "http://localhost:11434",
                "secret":   False,
                "required": False,
            },
            {
                "key":      "OLLAMA_MODEL",
                "label":    "Ollama 模型名稱",
                "default":  "llama3.2",
                "secret":   False,
                "required": False,
            },
        ],
        "disabled_features": [],  # 有預設值，Ollama 本地不強制
    },
    {
        "name": "LINE Messaging API",
        "description": "LINE 機器人 Webhook 整合（可選，跳過後仍可使用 CLI/API 模式）",
        "fields": [
            {
                "key":      "LINE_CHANNEL_SECRET",
                "label":    "LINE Channel Secret",
                "default":  "",
                "secret":   True,
                "required": False,
            },
            {
                "key":      "LINE_CHANNEL_ACCESS_TOKEN",
                "label":    "LINE Channel Access Token",
                "default":  "",
                "secret":   True,
                "required": False,
            },
        ],
        "disabled_features": [
            "LINE 訊息接收（Webhook /webhook/line）",
            "LINE Bot 自動回覆",
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
#  公開介面
# ═══════════════════════════════════════════════════════════════════════════════

def check_and_setup_env() -> None:
    """
    啟動時呼叫此函式。
    若 .env 缺少必要設定，將進入互動精靈引導使用者填寫或跳過。
    """
    _EnvValues = _load_env()
    _MissingGroups = _collect_missing_groups( _EnvValues )

    if not _MissingGroups:
        return  # 所有設定均已填寫，直接啟動

    _print_header()
    _SkippedFeatures: list = []

    for _Group in _MissingGroups:
        _IsAllSkipped = _prompt_group( _Group, _EnvValues )
        if _IsAllSkipped and _Group.get( "disabled_features" ):
            _SkippedFeatures.extend( _Group["disabled_features"] )

    _save_env( _EnvValues )

    if _SkippedFeatures:
        _print_skip_warning( _SkippedFeatures )

    _print_footer()


def check_mode_prerequisites( iMode: str, iPort: int = 8000 ) -> None:
    """
    依啟動模式執行完整 pre-flight 檢查：
      1. 基礎套件 + LLM provider 套件 + 模式專屬套件是否已安裝
      2. Ollama 使用者：服務連線測試
      3. API 模式：requirements.txt 變動偵測 + ngrok 自動啟動
    """
    _EnvValues = _load_env()
    _Provider  = _EnvValues.get( "LLM_PROVIDER", "gemini" ).lower().strip()

    _ToCheck: list = (
        list( _BASE_PACKAGES )
        + list( _LLM_PACKAGES.get( _Provider, [] ) )
        + list( _MODE_EXTRA_PACKAGES.get( iMode, [] ) )
    )
    _check_packages( _ToCheck )

    if _Provider == "ollama":
        _OllamaUrl = _EnvValues.get( "OLLAMA_BASE_URL", "http://localhost:11434" )
        _check_ollama_service( _OllamaUrl )

    if iMode == "api":
        _check_requirements_changed()
        _check_ngrok( iPort )


# ═══════════════════════════════════════════════════════════════════════════════
#  內部實作
# ═══════════════════════════════════════════════════════════════════════════════

def _load_env() -> dict:
    """讀取 .env 檔案，回傳 key-value dict（含空值欄位）。"""
    _Result: dict = {}

    if not _ENV_PATH.exists():
        return _Result

    _Lines = _ENV_PATH.read_text( encoding="utf-8" ).splitlines()
    for _Line in _Lines:
        _Line = _Line.strip()
        if not _Line or _Line.startswith( "#" ):
            continue
        if "=" in _Line:
            _Key, _, _Val = _Line.partition( "=" )
            _Result[_Key.strip()] = _Val.strip()

    return _Result


def _save_env( iValues: dict ) -> None:
    """將 key-value dict 寫回 .env（保留既有內容，追加/更新欄位）。"""
    _Existing: dict[str, int] = {}  # key → line index
    _Lines: list = []

    if _ENV_PATH.exists():
        _Lines = _ENV_PATH.read_text( encoding="utf-8" ).splitlines()
        for _Idx, _Line in enumerate( _Lines ):
            _Line = _Line.strip()
            if "=" in _Line and not _Line.startswith( "#" ):
                _Key = _Line.partition( "=" )[0].strip()
                _Existing[_Key] = _Idx

    for _Key, _Val in iValues.items():
        if _Key in _Existing:
            _Lines[_Existing[_Key]] = f"{_Key}={_Val}"
        else:
            _Lines.append( f"{_Key}={_Val}" )

    _ENV_PATH.write_text( "\n".join( _Lines ) + "\n", encoding="utf-8" )


def _resolve_condition( iGroup: dict, iEnvValues: dict ) -> bool:
    """判斷此群組的設定條件是否符合當前環境值。"""
    _CondKey: Optional[str]   = iGroup.get( "condition_key" )
    _CondVal: Optional[str]   = iGroup.get( "condition_value" )

    if _CondKey is None:
        return True  # 無條件，永遠檢查

    _CurrentVal = iEnvValues.get( _CondKey, "" ).lower().strip()
    return _CurrentVal == ( _CondVal or "" ).lower().strip()


def _collect_missing_groups( iEnvValues: dict ) -> list:
    """找出所有有空白必填欄位（或有空白選填欄位且需要引導）的群組。"""
    _Result: list = []

    for _Group in _SETUP_GROUPS:
        if not _resolve_condition( _Group, iEnvValues ):
            continue

        _HasMissing = any(
            not iEnvValues.get( _Field["key"], "").strip()
            for _Field in _Group["fields"]
        )
        if _HasMissing:
            _Result.append( _Group )

    return _Result


def _prompt_group( iGroup: dict, ioEnvValues: dict ) -> bool:
    """
    針對單一設定群組進行互動式提示。

    Returns:
        True  → 使用者選擇跳過整個群組（或所有欄位均留空）
        False → 至少填寫了一個欄位
    """
    _IsRequired: bool = any( _F.get( "required", False ) for _F in iGroup["fields"] )
    _AnyFilled: bool  = False

    print( f"\n{'─' * 60}" )
    print( f"  {iGroup['name']}" )
    print( f"  {iGroup['description']}" )
    if _IsRequired:
        print( "  [必填]" )
    else:
        print( "  [選填：可按 Enter 跳過]" )
    print( f"{'─' * 60}" )

    for _Field in iGroup["fields"]:
        _Key     = _Field["key"]
        _Label   = _Field["label"]
        _Default = _Field.get( "default", "" )
        _Secret  = _Field.get( "secret", False )
        _IsReq   = _Field.get( "required", False )

        # 若該欄位已有值，跳過
        if ioEnvValues.get( _Key, "" ).strip():
            print( f"  ✅ {_Label} — 已設定，略過" )
            _AnyFilled = True
            continue

        # 組合提示文字
        _Hint = "[必填]" if _IsReq else "[選填，Enter 跳過]"
        if _Default:
            _Hint += f" 預設：{_Default}"

        _Prompt = f"\n  {_Label} {_Hint}\n  > "

        # 輸入迴圈（必填欄位要求至少填寫一次，或允許強制跳過）
        while True:
            if _Secret:
                try:
                    import getpass
                    _Input = getpass.getpass( _Prompt )
                except Exception:
                    _Input = input( _Prompt )
            else:
                _Input = input( _Prompt )

            _Input = _Input.strip()

            if _Input:
                ioEnvValues[_Key] = _Input
                _AnyFilled = True
                print( f"  ✅ {_Label} 已儲存" )
                break
            elif _Default:
                ioEnvValues[_Key] = _Default
                _AnyFilled = True
                print( f"  ✅ {_Label} 使用預設值：{_Default}" )
                break
            elif _IsReq:
                print( f"  ⚠️  此欄位為必填，請輸入值（或輸入 skip 強制跳過）：" )
                _Confirm = input( "  > " ).strip().lower()
                if _Confirm == "skip":
                    print( f"  ⏭️  強制跳過 {_Label}" )
                    break
                # 否則繼續迴圈
            else:
                # 選填且沒有輸入，跳過
                print( f"  ⏭️  略過 {_Label}" )
                break

    return not _AnyFilled


def _print_header() -> None:
    print( "\n" + "═" * 60 )
    print( "  🔧  AI 第二大腦 — 初始設定精靈" )
    print( "  偵測到部分設定尚未完成，請依序填寫。" )
    print( "  設定將自動儲存至 _AI_Engine/.env" )
    print( "═" * 60 )


def _print_skip_warning( iFeatures: list ) -> None:
    print( "\n" + "━" * 60 )
    print( "  ⚠️  以下功能因缺少設定將無法使用：" )
    for _Feature in iFeatures:
        print( f"      • {_Feature}" )
    print( "  👉 日後可編輯 _AI_Engine/.env 補齊設定後重啟。" )
    print( "━" * 60 )


def _print_footer() -> None:
    print( "\n  ✅ 設定完成，正在啟動系統...\n" )


# ═══════════════════════════════════════════════════════════════════════════════
#  Pre-flight 檢查（套件 / 服務 / ngrok）
# ═══════════════════════════════════════════════════════════════════════════════

def _check_packages( iPackages: list ) -> None:
    """
    逐一檢查套件是否已安裝；若有未安裝者詢問是否自動 pip install。
    iPackages: list of ( import_module_name, pip_install_spec, 功能說明 )
    """
    import importlib.util

    _Missing: list = []
    for _ImportName, _PipName, _Desc in iPackages:
        if importlib.util.find_spec( _ImportName ) is None:
            _Missing.append( ( _ImportName, _PipName, _Desc ) )

    if not _Missing:
        return

    print( "\n" + "-" * 60 )
    print( "  [PKG] 偵測到以下套件尚未安裝：" )
    for _, _PipName, _Desc in _Missing:
        print( f"    -  {_PipName:<42}  ({_Desc})" )
    print( "" )
    print( "  >> 也可手動執行：pip install -r requirements.txt" )
    print( "" )

    _Answer = input( "  是否立即自動安裝？ [y/N] " ).strip().lower()
    if _Answer == "y":
        _PipExe = sys.executable
        for _, _PipName, _Desc in _Missing:
            print( f"  >> 安裝 {_PipName} ..." )
            _Proc = subprocess.run(
                [_PipExe, "-m", "pip", "install", _PipName],
                capture_output=True, text=True,
            )
            if _Proc.returncode == 0:
                print( f"  OK  {_PipName} 安裝成功" )
            else:
                print( f"  WARN  {_PipName} 安裝失敗，請手動安裝" )
                _ErrLine = _Proc.stderr.strip().splitlines()
                if _ErrLine:
                    print( f"        {_ErrLine[-1][:200]}" )
    else:
        print( "  WARN  部分套件未安裝，啟動時可能拋出 ImportError。" )
        print( "  >>  pip install -r requirements.txt" )
    print( "-" * 60 )


def _check_ollama_service( iBaseUrl: str ) -> None:
    """嘗試連線到 Ollama 服務，若失敗則顯示安裝與啟動說明。"""
    import urllib.request

    print( "\n" + "-" * 60 )
    print( f"  [Ollama] 服務連線檢查：{iBaseUrl}" )
    try:
        with urllib.request.urlopen( iBaseUrl.rstrip( "/" ) + "/api/tags", timeout=3 ) as _Resp:
            if _Resp.status == 200:
                print( "  OK  Ollama 服務已連線" )
                print( "-" * 60 )
                return
    except Exception:
        pass

    print( "  WARN  無法連線到 Ollama 服務" )
    print( "  >>  請確認 Ollama 已安裝並執行中：" )
    print( "        1. 安裝：https://ollama.ai" )
    print( "        2. 執行：ollama serve" )
    print( f"        3. 確認 OLLAMA_BASE_URL={iBaseUrl} 正確" )
    print( "-" * 60 )

## <summary>ngrok 執行檔的常見安裝路徑（依優先順序搜尋）</summary>
_NGROK_SEARCH_PATHS: list = [
    # WinGet 安裝路徑
    Path( os.environ.get( "LOCALAPPDATA", "" ) )
    / "Microsoft" / "WinGet" / "Packages"
    / "Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ngrok.exe",
    # PATH 直接可用（Linux / macOS / 手動安裝）
]

## <summary>pip hash 快取檔路徑，用於偵測套件環境是否有變動</summary>
_REQ_HASH_CACHE: Path = Path( __file__ ).resolve().parent / ".req_hash"

## <summary>requirements.txt 路徑</summary>
_REQ_FILE: Path = Path( __file__ ).resolve().parent / "requirements.txt"


def check_api_prerequisites( iPort: int = 8000 ) -> None:
    """
    API 模式啟動前的 pre-flight 檢查：
      1. ngrok 是否已安裝（找執行檔）
      2. ngrok authtoken 是否已設定（若已設定則自動啟動）
      3. requirements.txt 是否有變動（提示重新 pip install）
    """
    _check_requirements_changed()
    _check_ngrok( iPort )


def _check_requirements_changed() -> None:
    """比對 requirements.txt 的 hash 與上次快取，若不同則提示重新安裝。"""
    if not _REQ_FILE.exists():
        return

    _CurrentHash = hashlib.md5( _REQ_FILE.read_bytes() ).hexdigest()

    if _REQ_HASH_CACHE.exists():
        _CachedHash = _REQ_HASH_CACHE.read_text( encoding="utf-8" ).strip()
        if _CachedHash == _CurrentHash:
            return  # 無變動，跳過

    # Hash 不同（或快取不存在）→ 提示使用者
    print( "\n" + "-" * 60 )
    print( "  [PKG] requirements.txt 有變動（或首次啟動）" )
    print( "  請確認是否已重新安裝套件：" )
    print( "  >>  pip install -r requirements.txt" )
    print( "" )

    _Answer = input( "  已安裝完成？ [y/N] " ).strip().lower()
    if _Answer == "y":
        _REQ_HASH_CACHE.write_text( _CurrentHash, encoding="utf-8" )
        print( "  OK  已記錄，下次啟動不再提示。\n" )
    else:
        print( "  WARN  請先執行安裝後再重啟，否則可能發生 ImportError。\n" )
    print( "-" * 60 )


def _find_ngrok_exe() -> Optional[Path]:
    """搜尋 ngrok 執行檔，回傳 Path 或 None。"""
    # 1. 先試 PATH（跨平台通用安裝）
    try:
        _Which = subprocess.run(
            ["where", "ngrok"] if sys.platform == "win32" else ["which", "ngrok"],
            capture_output=True, text=True, timeout=3,
        )
        if _Which.returncode == 0:
            _FirstLine = _Which.stdout.strip().splitlines()[0]
            if _FirstLine:
                return Path( _FirstLine )
    except Exception:
        pass

    # 2. 已知 WinGet 安裝路徑
    for _Candidate in _NGROK_SEARCH_PATHS:
        if _Candidate.exists():
            return _Candidate

    return None


def _launch_ngrok( iExe: Path, iPort: int ) -> None:
    """若 ngrok 尚未執行則在背景自動啟動，等待取得 Public URL 後印出。"""
    import urllib.request
    import json as _json
    import time as _time

    _ApiUrl = "http://localhost:4040/api/tunnels"

    # 先查 ngrok local API（已在執行則直接印 URL）
    try:
        with urllib.request.urlopen( _ApiUrl, timeout=1 ) as _Resp:
            _Data = _json.loads( _Resp.read() )
            for _T in _Data.get( "tunnels", [] ):
                if _T.get( "proto" ) == "https":
                    print( "  OK  ngrok 已在執行中" )
                    print( f"  >>  Public URL：{_T['public_url']}" )
                    print( "-" * 60 + "\n" )
                    return
    except Exception:
        pass

    # 啟動 ngrok 背景程序
    print( f"  >>  自動啟動 ngrok tunnel (port {iPort}) ..." )
    _CreationFlags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    subprocess.Popen(
        [str( iExe ), "http", str( iPort )],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_CreationFlags,
    )

    # 等待 ngrok 啟動（最多 5 秒）
    for _ in range( 10 ):
        _time.sleep( 0.5 )
        try:
            with urllib.request.urlopen( _ApiUrl, timeout=1 ) as _Resp:
                _Data = _json.loads( _Resp.read() )
                for _T in _Data.get( "tunnels", [] ):
                    if _T.get( "proto" ) == "https":
                        print( "  OK  ngrok 已啟動" )
                        print( f"  >>  Public URL：{_T['public_url']}" )
                        print( "-" * 60 + "\n" )
                        return
        except Exception:
            continue

    print( "  WARN  ngrok 啟動中，請稍後至 http://localhost:4040 確認 Public URL" )
    print( "-" * 60 + "\n" )


def _check_ngrok( iPort: int = 8000 ) -> None:
    """檢查 ngrok 安裝狀態與 authtoken 設定，若條件符合則自動啟動 tunnel。"""
    print( "\n" + "-" * 60 )
    print( "  [ngrok] tunnel 狀態檢查（對外公開 webhook 必要）" )

    _NgrokExe = _find_ngrok_exe()

    if _NgrokExe is None:
        print( "  WARN  找不到 ngrok 執行檔" )
        print( "  安裝方式（擇一）：" )
        print( "    winget install Ngrok.Ngrok" )
        print( "    下載：https://ngrok.com/download" )
        print( "  安裝後至 https://dashboard.ngrok.com/get-started/your-authtoken" )
        print( "  執行：ngrok config add-authtoken <YOUR_TOKEN>" )
        print( "  WARN  未安裝 ngrok 時，LINE Webhook 只能在本機測試。" )
        print( "-" * 60 + "\n" )
        return

    print( f"  OK  ngrok 已找到：{_NgrokExe}" )

    # 檢查 authtoken：嘗試讀取 ngrok config 檔
    _ConfigPaths = [
        Path( os.environ.get( "USERPROFILE", "" ) ) / ".config" / "ngrok" / "ngrok.yml",
        Path( os.environ.get( "HOME", "" ) ) / ".config" / "ngrok" / "ngrok.yml",
        Path( os.environ.get( "USERPROFILE", "" ) ) / "AppData" / "Local" / "ngrok" / "ngrok.yml",
    ]
    _TokenFound = False
    for _CfgPath in _ConfigPaths:
        if _CfgPath.exists():
            _Content = _CfgPath.read_text( encoding="utf-8", errors="ignore" )
            if "authtoken" in _Content:
                _TokenFound = True
                break

    if _TokenFound:
        print( "  OK  ngrok authtoken 已設定" )
        _launch_ngrok( _NgrokExe, iPort )
    else:
        print( "  WARN  ngrok 尚未設定 authtoken" )
        print( "  請至 https://dashboard.ngrok.com/get-started/your-authtoken 取得 token" )
        print( f"  執行：\"{_NgrokExe}\" config add-authtoken <YOUR_TOKEN>" )
        print( "  WARN  LINE Webhook 需要公開 HTTPS URL，沒有 authtoken 無法建立 tunnel。" )
        print( "-" * 60 + "\n" )
