# -*- mode: python ; coding: utf-8 -*-
"""
AI Memory Vault v3.5 — PyInstaller Build Spec

產出三個 exe（共用同一份 library 目錄，節省磁碟空間）：
  dist/vault-ai/vault-cli.exe       → 互動式 CLI（consoleTrue）
  dist/vault-ai/vault-mcp.exe       → MCP stdio server（console=False，背景執行）
  dist/vault-ai/vault-scheduler.exe → APScheduler 排程守護（console=True）

exe 名稱偵測邏輯（main.py _detect_frozen_mode）：
  vault-mcp.exe       自動加 --mode mcp
  vault-scheduler.exe 自動加 --scheduler
  vault-cli.exe       沿用 argparse 預設（CLI 互動介面）

執行方式：
  pyinstaller build.spec            （在 AI_Engine/ 目錄下）
  .\build.ps1                       （一鍵打包腳本）

@version 3.4.0
"""

import os

from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None
# SPECPATH：spec 檔案所在目錄（packaging/），已由 PyInstaller 自動注入
# ENGINE_DIR：AI_Engine/，spec 的上一層
ENGINE_DIR = os.path.abspath( os.path.join( SPECPATH, '..' ) )

# ── 動態收集複雜套件的資料檔 + 隱藏 import ─────────────────
# chromadb：SQL migrations + segment 動態載入
_datas_chroma,  _bins_chroma,  _hi_chroma  = collect_all( 'chromadb' )
# sentence_transformers：tokenizer 設定
_datas_st,      _bins_st,      _hi_st      = collect_all( 'sentence_transformers' )
# mcp SDK：schema 資料
_datas_mcp,     _bins_mcp,     _hi_mcp     = collect_all( 'mcp' )
# huggingface_hub：模型快取管理（比 collect_all('transformers') 安全）
_datas_hf,      _bins_hf,      _hi_hf      = collect_all( 'huggingface_hub' )

ALL_DATAS = (
    _datas_chroma
    + _datas_st
    + _datas_mcp
    + _datas_hf
    + [ ( os.path.join( ENGINE_DIR, '.env.example' ), '.' ),
        ( os.path.join( ENGINE_DIR, 'requirements.txt' ), '.' ) ]
)
ALL_BINS = _bins_chroma + _bins_st + _bins_mcp + _bins_hf

HIDDEN_IMPORTS = (
    _hi_chroma
    + _hi_st
    + _hi_mcp
    + _hi_hf
    + [
        # torch.distributed：torch.utils.data.dataloader 啟動時就需要，不可排除
        'torch.distributed',
        'torch.distributed.elastic',
        'torch.distributed.elastic.multiprocessing',
        # tokenizers（sentence_transformers 依賴，二進位延遲 import）
        'tokenizers',
        'tokenizers.models',
        'tokenizers.pre_tokenizers',
        # safetensors（模型載入需要）
        'safetensors',
        'safetensors.torch',
        # filelock（HuggingFace 快取鎖）
        'filelock',
        # SQLAlchemy（RecordManager 使用）
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        'langchain_community.indexes._sql_record_manager',
        # LangChain 生態系延遲 import
        'langchain_core.load',
        'langchain_core.messages',
        'langchain_core.documents',
        'langchain_core.embeddings',
        'langchain_core.vectorstores',
        'langchain_huggingface',
        'langchain_chroma',
        'langchain_text_splitters',
        'langchain_community.document_loaders',
        'langchain_community.document_loaders.text',
        # APScheduler
        'apscheduler',
        'apscheduler.schedulers.background',
        'apscheduler.triggers.cron',
        'apscheduler.executors.pool',
        # FastAPI / uvicorn（API 模式）
        'fastapi',
        'uvicorn.main',
        'uvicorn.config',
        'uvicorn.lifespan.off',
        'uvicorn.lifespan.on',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.loops.asyncio',
        # tkinter（GUI 安裝詢問彈窗）
        'tkinter',
        'tkinter.messagebox',
        # 本地套件
        'config',
        'core',
        'core.embeddings',
        'core.errors',
        'core.indexer',
        'core.logger',
        'core.migration',
        'core.retriever',
        'core.vectorstore',
        'services',
        'services.vault',
        'services.setup',
        'services.scheduler',
        'services.auto_scheduler',
        'services.agent_router',
        'services.git_service',
        'services.knowledge_extractor',
        'services.token_counter',
        'mcp_app',
        'mcp_app.server',
        'mcp_app.utils',
        'mcp_app.tools',
        'mcp_app.tools.vault_tools',
        'mcp_app.tools.scheduler_tools',
        'mcp_app.tools.project_tools',
        'mcp_app.tools.todo_tools',
        'mcp_app.tools.index_tools',
        'mcp_app.tools.agent_tools',
        'cli',
        'cli.repl',
        'cli.setup_commands',
        'tools',
        'tools.registry',
        # 其他工具
        'yaml',
        'pydantic',
        'questionary',
        'git',
        'rank_bm25',
        'dotenv',
    ]
)

# ── 單一 Analysis（三個 exe 共用，build 一次）─────────────────
a = Analysis(
    [ os.path.join( ENGINE_DIR, 'main.py' ) ],
    pathex=[ ENGINE_DIR ],
    binaries=ALL_BINS,
    datas=ALL_DATAS,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型套件，減少打包體積
        'IPython', 'jupyter', 'matplotlib', 'PIL', 'Pillow',
        'sklearn', 'scipy', 'pandas',
        'numpy.testing', 'unittest',
        'pytest', 'setuptools', 'pkg_resources',
        'notebook', 'nbformat', 'nbconvert',
        'torchaudio', 'torchvision',
        'torch.testing', 'torch.utils.benchmark',
        # torch.distributed 已移至 hiddenimports，不可排除（dataloader 啟動需要它）
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ( a.pure, a.zipped_data, cipher=block_cipher )

# ── vault-cli.exe（互動式 CLI，有終端視窗）───────────────────
exe_cli = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='vault-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

# ── vault-mcp.exe（MCP stdio，無終端視窗）───────────────────
# console=False：VS Code 以 subprocess 啟動，stdin/stdout 作為 pipe 傳輸 JSON-RPC
exe_mcp = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='vault-mcp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

# ── vault-scheduler.exe（排程守護，有終端視窗顯示日誌）───────
exe_scheduler = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='vault-scheduler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

# ── 共用 library 目錄（三個 exe 共享，節省磁碟空間）───────────
coll = COLLECT(
    exe_cli,
    exe_mcp,
    exe_scheduler,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='vault-ai',   # → dist/vault-ai/
)
