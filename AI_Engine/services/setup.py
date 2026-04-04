"""
Vault 初始化引導服務
首次執行時建立 V3 Vault 目錄結構、初始化空 ChromaDB、寫入 config.json。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
import os
from datetime import datetime

from config import AppConfig, ConfigManager


class SetupService:
    """
    首次執行初始化：建立 Vault 目錄結構 + 空 ChromaDB + config.json。
    冪等設計：已存在的目錄/檔案不會被覆蓋。
    """

    #region 公開方法
    @classmethod
    def run_setup( cls, iConfig: AppConfig ) -> dict:
        """
        完整初始化流程。

        Args:
            iConfig: 應用程式設定（含 vault_path）。

        Returns:
            統計結果字典 {"dirs_created", "files_created", "db_initialized"}。
        """
        _Stats = {
            "dirs_created": 0,
            "files_created": 0,
            "db_initialized": False,
            "chunks_indexed": 0,
            "vscode_files_created": 0,
        }

        print( "\n[Setup] 🚀 開始初始化 AI Memory Vault v3..." )
        print( f"[Setup] 📁 Vault 路徑：{iConfig.vault_path}" )

        # Step 1: 建立目錄結構
        _Stats["dirs_created"] = cls._create_vault_structure( iConfig.vault_path, iConfig.paths )

        # Step 2: 建立初始檔案
        _Stats["files_created"] = cls._create_initial_files( iConfig )

        # Step 3: 初始化資料庫
        cls._init_database( iConfig )
        _Stats["db_initialized"] = True

        # Step 4: 寫入 config.json
        ConfigManager.save( iConfig )
        print( f"[Setup] 💾 config.json 已寫入" )

        # Step 5: 初始同步 Vault 至向量資料庫
        _Stats["chunks_indexed"] = cls._initial_sync( iConfig )
        # Step 6: 生成 VS Code 全域設定檔
        _Stats["vscode_files_created"] = cls._setup_vscode_integration( iConfig )
        print( f"\n[Setup] ✅ 初始化完成！" )
        print( f"        目錄：{_Stats['dirs_created']} 個" )
        print( f"        檔案：{_Stats['files_created']} 個" )
        print( f"        資料庫：{'已初始化' if _Stats['db_initialized'] else '失敗'}" )
        print( f"        向量索引：{_Stats['chunks_indexed']} 個 chunks" )
        print( f"        VS Code 設定檔：{_Stats['vscode_files_created']} 個" )
        return _Stats
    #endregion

    #region 私有方法 — 目錄與檔案
    @classmethod
    def _create_vault_structure( cls, iVaultPath: str, iPaths ) -> int:
        """
        建立 V3 Vault 目錄骨架。

        Args:
            iVaultPath: Vault 根目錄絕對路徑。
            iPaths:     VaultPaths 路徑對照表。

        Returns:
            新建的目錄數。
        """
        _Count = 0
        for _RelDir in iPaths.get_all_dirs():
            _AbsDir = os.path.join( iVaultPath, _RelDir )
            if not os.path.exists( _AbsDir ):
                os.makedirs( _AbsDir, exist_ok=True )
                _Count += 1
                print( f"[Setup] 📂 建立目錄：{_RelDir}" )
        return _Count

    @classmethod
    def _create_initial_files( cls, iConfig: AppConfig ) -> int:
        """
        建立初始 Markdown 檔案（冪等：已存在跳過）。

        Args:
            iConfig: 應用程式設定。

        Returns:
            新建的檔案數。
        """
        _Count = 0
        _Today = datetime.now().strftime( "%Y.%m.%d" )

        for _RelPath, _GenFunc in iConfig.paths.get_initial_files().items():
            _AbsPath = os.path.join( iConfig.vault_path, _RelPath )
            if os.path.exists( _AbsPath ):
                continue

            _Dir = os.path.dirname( _AbsPath )
            if not os.path.exists( _Dir ):
                os.makedirs( _Dir, exist_ok=True )

            _Content = getattr( cls, _GenFunc )( iConfig, _Today )
            with open( _AbsPath, "w", encoding="utf-8" ) as _F:
                _F.write( _Content )
            _Count += 1
            print( f"[Setup] 📄 建立檔案：{_RelPath}" )

        # .gitkeep for attachments
        _Gitkeep = os.path.join( iConfig.vault_path, iConfig.paths.attachments, ".gitkeep" )
        if not os.path.exists( _Gitkeep ):
            with open( _Gitkeep, "w" ) as _F:
                _F.write( "" )

        return _Count
    #endregion

    #region 私有方法 — 資料庫
    @classmethod
    def _init_database( cls, iConfig: AppConfig ) -> None:
        """
        初始化空的 ChromaDB 與 RecordManager schema。

        Args:
            iConfig: 應用程式設定。
        """
        from core import embeddings as _EmbModule
        from core import vectorstore as _VsModule

        # 確保 ChromaDB 目錄存在
        _ChromaDir = iConfig.database.get_chroma_path()
        os.makedirs( _ChromaDir, exist_ok=True )

        # 初始化嵌入模型設定
        _EmbModule.initialize( iConfig.embedding.model )

        # 初始化向量庫設定
        _VsModule.initialize(
            iChromaDir=_ChromaDir,
            iRecordDbUrl=iConfig.database.get_record_db_url(),
            iCollectionName=iConfig.database.collection_name,
        )

        # 觸發建立（lru_cache 會快取實例）
        _Vs = _VsModule.get_vectorstore()
        _Rm = _VsModule.get_record_manager()

        print( f"[Setup] 🗄️  ChromaDB 初始化完成：{_ChromaDir}" )
        print( f"[Setup] 🗄️  RecordManager 初始化完成" )
    #endregion

    #region 私有方法 — 初始同步
    @classmethod
    def _initial_sync( cls, iConfig: AppConfig ) -> int:
        """
        首次初始化完成後，將 Vault 全部檔案同步至向量資料庫。

        Args:
            iConfig: 應用程式設定。

        Returns:
            索引完成的 chunk 數量。
        """
        from services.vault import VaultService

        print( f"[Setup] 🔄 開始首次同步 Vault → 向量資料庫..." )
        VaultService.initialize( iConfig )
        _SyncResult = VaultService.sync()
        _Total = _SyncResult.get( "total_chunks", 0 )
        _Stats = _SyncResult.get( "index_stats", {} )
        print(
            f"[Setup] ✅ 同步完成：新增 {_Stats.get('num_added', 0)} | "
            f"更新 {_Stats.get('num_updated', 0)} | "
            f"刪除 {_Stats.get('num_deleted', 0)} | "
            f"總計 {_Total} chunks"
        )
        return _Total
    #endregion

    #region 私有方法 — 內容生成
    @classmethod
    def _gen_nav( cls, iConfig: AppConfig, iToday: str ) -> str:
        """生成導航地圖。"""
        _P = iConfig.paths
        return f"""---
type: system
created: {iToday}
last_updated: {iToday}
---

# 🗺️ Vault 導航地圖

## 目錄結構

| 目錄 | 說明 |
|------|------|
| `{_P.config}/` | AI 系統設定（導航/交接索引） |
| `{_P.workspaces}/` | 工作空間（依組織分類） |
| `{_P.global_dir}/` | 全域共用（規則/片段/技術筆記/回顧連結） |
| `{_P.global_rules}/` | 全域共用規則（組織規則可覆蓋） |
| `{_P.personal}/` | 個人空間（日記/學習/目標/靈感/總進度） |
| `{_P.personal_reviews_daily}/` | 每日總進度表（所有專案摘要） |
| `{_P.knowledge}/` | 永久知識卡片（概念萃取） |
| `{_P.templates}/` | 模板系統 |
| `{_P.attachments}/` | 附件存放 |

## 組織結構

```
{_P.workspaces}/{{organization}}/
├── {_P.org_rules}/              ← 組織專屬規則（覆蓋 _global/rules）
└── {_P.org_projects}/
    └── {{project}}/
        ├── {_P.proj_daily}/           ← 專案每日詳細進度
        ├── {_P.proj_notes}/           ← 專案筆記 / 技術決策
        ├── {_P.proj_meetings}/        ← 專案會議紀錄
        ├── {_P.proj_conversations}/   ← AI 對話紀錄
        └── {_P.proj_status}           ← 專案狀態（待辦 + 工作脈絡）
```

## 進度分層

| 層級 | 路徑 | 內容 |
|------|------|------|
| 專案狀態 | `{{org}}/projects/{{proj}}/{_P.proj_status}` | 待辦 + 工作脈絡 + 決策記錄 |
| 專案詳細 | `{{org}}/projects/{{proj}}/{_P.proj_daily}/` | 每日做了什麼、遇到什麼問題 |
| 專案對話 | `{{org}}/projects/{{proj}}/{_P.proj_conversations}/` | AI 工作對話紀錄 |
| 每日總結 | `{_P.personal_reviews_daily}/` | 所有專案重點摘要 |
| 每週總結 | `{_P.personal_reviews_weekly}/` | 當週進度彙整 |
| 每月總結 | `{_P.personal_reviews_monthly}/` | 當月進度彙整 |
| AI 週報 | `{_P.ai_analysis_weekly}/` | 對話準確率、Token 分析 |
| AI 月報 | `{_P.ai_analysis_monthly}/` | 趨勢、優化、評分 |
"""

    @classmethod
    def _gen_handoff( cls, iConfig: AppConfig, iToday: str ) -> str:
        """生成 Session 交接索引（輕量版，各專案詳細狀態見專案的 status.md）。"""
        return f"""---
type: system
created: {iToday}
last_updated: {iToday}
---

# 🤝 Session Handoff

> 記錄上次工作的活躍專案，供下次 AI 對話開場快速定位。
> 各專案詳細狀態（待辦 + 工作脈絡）見各專案的 `status.md`。

## 上次活躍專案

| 專案 | 組織 | 狀態 | 詳細 |
|------|------|------|------|
| （尚無紀錄） | | | |

## 跨專案備註

（無）
"""

    @classmethod
    def _gen_agents( cls, iConfig: AppConfig, iToday: str ) -> str:
        """生成 Agent 架構文件。"""
        return f"""---
type: system
created: {iToday}
last_updated: {iToday}
---

# 🤖 Agent 架構文件

> 此文件描述 AI Memory Vault 的 Agent 設定與能力。

## 可用工具

| 工具 | 說明 |
|------|------|
| `search_vault` | 搜尋記憶庫（BM25 + 向量混合） |
| `read_note` | 讀取指定筆記內容 |
| `write_note` | 寫入/更新筆記（自動索引） |
| `sync_vault` | 全量增量同步至向量庫 |
| `generate_project_daily` | 生成指定專案的每日詳細進度模板 |
| `generate_daily_review` | 生成每日總進度表（所有專案摘要） |
| `generate_weekly_review` | 生成每週總進度表 |
| `generate_monthly_review` | 生成每月總進度表 |
| `log_ai_conversation` | 記錄 AI 對話至專案 conversations/ |
| `generate_ai_weekly_analysis` | 生成 AI 對話週報（準確率/Token/評分） |
| `generate_ai_monthly_analysis` | 生成 AI 對話月報（趨勢/優化/評分） |
"""

    @classmethod
    def _gen_global_index( cls, iConfig: AppConfig, iToday: str ) -> str:
        """生成全域共用入口。"""
        return f"""---
type: index
created: {iToday}
last_updated: {iToday}
---

# 🌐 全域共用資源

跨所有組織通用的資源。組織規則可覆蓋此處的共用規則。

## 目錄

| 目錄 | 說明 |
|------|------|
| `rules/` | 共用規則（組織規則衝突時以組織為準） |
| `snippets/` | 程式碼片段（依語言分類） |
| `tech-notes/` | 技術筆記 |
| `reviews/` | 總進度表連結（實體在 personal/reviews/） |
"""

    @classmethod
    def _gen_personal_index( cls, iConfig: AppConfig, iToday: str ) -> str:
        """生成個人空間入口。"""
        _Name = iConfig.user.name or "使用者"
        return f"""---
type: index
created: {iToday}
last_updated: {iToday}
---

# 🏠 {_Name} 的個人空間

## 目錄

| 目錄 | 說明 |
|------|------|
| `journal/` | 日記 |
| `learning/` | 學習筆記 |
| `goals/` | 目標管理 |
| `ideas/` | 靈感收集 |
| `reviews/daily/` | 每日總進度（所有專案摘要） |
| `reviews/weekly/` | 每週總進度 |
| `reviews/monthly/` | 每月總進度 |
| `ai-analysis/weekly/` | AI 對話週報分析 |
| `ai-analysis/monthly/` | AI 對話月報分析 |
"""

    @classmethod
    def _gen_knowledge_index( cls, iConfig: AppConfig, iToday: str ) -> str:
        """生成知識卡片入口。"""
        return f"""---
type: index
created: {iToday}
last_updated: {iToday}
---

# 📚 知識卡片

> 萃取後的永久知識，去脈絡化的概念卡片。

（尚無卡片）
"""

    @classmethod
    def _gen_templates_index( cls, iConfig: AppConfig, iToday: str ) -> str:
        """生成模板系統入口。"""
        return f"""---
type: index
created: {iToday}
last_updated: {iToday}
---

# 🧩 模板系統

## 目錄

| 目錄 | 說明 |
|------|------|
| `agents/` | Agent 角色定義模板 |
| `projects/` | 專案類型模板 |
| `sections/` | Vault 區域結構模板 |
"""
    #endregion

    #region 私有方法 — VS Code 整合
    @classmethod
    def _setup_vscode_integration( cls, iConfig: AppConfig ) -> int:
        """
        在 vscode_user_path/prompts/ 生成 VS Code 全域 instructions 檔。
        冪等設計：已存在的檔案不會被覆蓋。

        Args:
            iConfig: 應用程式設定（含 vscode_user_path）。

        Returns:
            新建的檔案數（0 表示未設定路徑或全部已存在）。
        """
        if not iConfig.vscode_user_path:
            print( "[Setup] ⚠️  vscode_user_path 未設定，跳過 VS Code 整合" )
            return 0

        _PromptsDir = os.path.join( iConfig.vscode_user_path, "prompts" )
        if not os.path.exists( _PromptsDir ):
            os.makedirs( _PromptsDir, exist_ok=True )

        _Files = {
            "vault-coding-rules.instructions.md": cls._gen_vscode_coding_rules( iConfig ),
            "VaultWriteConventions.instructions.md": cls._gen_vscode_write_conventions( iConfig ),
        }

        _Count = 0
        for _FileName, _Content in _Files.items():
            _AbsPath = os.path.join( _PromptsDir, _FileName )
            if os.path.exists( _AbsPath ):
                print( f"[Setup] [VS Code] \u8df3\u904e\uff1a{_FileName}" )
                continue
            with open( _AbsPath, "w", encoding="utf-8" ) as _F:
                _F.write( _Content )
            _Count += 1
            print( f"[Setup] [VS Code] \u5efa\u7acb\uff1a{_FileName}" )

        return _Count

    @classmethod
    def _gen_vscode_coding_rules( cls, iConfig: AppConfig ) -> str:
        """生成 vault-coding-rules.instructions.md 內容。"""
        _OrgRows = "\n".join(
            f"| `{_Org}` | 僅限 {_Org} 組織的專案 |"
            for _Org in ( iConfig.user.organizations or [] )
        )
        _OrgSection = f"\n{_OrgRows}" if _OrgRows else ""
        return f"""---
applyTo: "**"
---

# AI Memory Vault — 編碼規則

此設定關聯的 AI Memory Vault 含有編碼規則，存放於：
- `workspaces/_global/rules/` — 全域規則（所有專案皆適用）
- `workspaces/{{組織}}/rules/` — 組織特例規則（僅限該組織的專案）

協助撰寫程式碼、Code Review 或設計架構時，請依以下流程取得最新規則：

## 規則取得流程（必須執行）

**Step 1 — 探索現有規則（不需要知道確切檔名）：**
```
search_vault(query="type:rule", top_k=30)
```
回傳結果包含全域與所有組織的規則，以及每條規則的 frontmatter（含 `workspace` 欄位）。

**Step 2 — 依 `workspace` 欄位判斷套用範圍：**

| frontmatter `workspace` | 套用條件 |
|------------------------|---------|
| `_global` | 永遠套用 |{_OrgSection}

**Step 3 — 依任務語言/領域，用 `read_note` 讀取相關規則。**

> **設計原則**：此檔案永遠不需要手動更新規則清單。
> 新增規則（全域或組織特例）只需寫入對應 `rules/` 目錄，並在 frontmatter 設定 `type: rule` 與正確的 `workspace`，下次 search_vault 即可自動發現。
"""

    @classmethod
    def _gen_vscode_write_conventions( cls, iConfig: AppConfig ) -> str:
        """生成 VaultWriteConventions.instructions.md 內容。"""
        return """---
applyTo: "**"
---

# AI Memory Vault — 寫入路徑規範

使用 `write_note` 或 `read_note`（ai-memory-vault MCP）時，`file_path` 必須遵守以下規則。

## 🔗 結構查詢（唯一資料源）

Vault 目錄結構與路徑前綴 **不在此檔案維護**。
需要時請透過 MCP 工具讀取最新版本：

```
read_note("_config/nav.md")    → 完整目錄結構 + 進度分層表
```

## 路徑通用規則

- 所有路徑為**相對路徑**（相對於 Vault 根目錄）
- 只允許 `.md` 檔案
- 專案路徑格式：`workspaces/{組織}/projects/{專案名}/`
- 新專案首次寫入時會**自動建立**骨架目錄（daily/notes/meetings/conversations）

## ⚠️ 禁止

- 不可使用**絕對路徑**（`D:\\...`）
- 不可寫入 `AI_Engine/`（引擎程式碼，不是知識庫）
- 不可直接寫入 `workspaces/projects/`（專案必須在組織子目錄下）

## 判斷邏輯

1. 這筆資料屬於哪個**組織**？→ `workspaces/{組織名}/`
2. 是**跨組織通用**的知識？→ `knowledge/` 或 `workspaces/_global/`
3. 是**個人**相關？→ `personal/`
"""
    #endregion
