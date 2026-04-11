"""
AI Memory Vault v3 — 統一設定管理
config.json（主設定）+ .env（敏感密鑰向後相容）。
首次啟動時若 config.json 不存在 → 觸發 SetupService。

@author gabrielchen
@version 3.0
@since AI-Memory-Vault 3.0
@date 2026.04.01
"""
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ── 路徑常數 ──────────────────────────────────────────────
# ENGINE_DIR：程式所在目錄（frozen = exe 旁；dev = AI_Engine/）
# DATA_DIR  ：可寫資料目錄（統一使用 %APPDATA%\AI-Memory-Vault）
#   dev 與 frozen 共用同一目錄，避免 config / chroma_db / vault_meta 各自獨立導致不同步。
#   所有模式均可透過 VAULT_DATA_DIR 環境變數覆蓋 DATA_DIR
_ENV_DATA = os.environ.get( 'VAULT_DATA_DIR' )
if getattr( sys, 'frozen', False ):
    ENGINE_DIR: Path = Path( sys.executable ).resolve().parent
else:
    ENGINE_DIR: Path = Path( __file__ ).resolve().parent
DATA_DIR: Path = Path( _ENV_DATA ) if _ENV_DATA else Path( os.environ.get( 'APPDATA', str( ENGINE_DIR ) ) ) / "AI-Memory-Vault"
DATA_DIR.mkdir( parents=True, exist_ok=True )
PROJECT_ROOT: Path = ENGINE_DIR.parent
CONFIG_FILE:  Path = DATA_DIR / "config.json"

__version__: str = "3.7.0"


# region 設定資料結構
@dataclass
class UserConfig:
    """使用者資訊。"""
    ## <summary>使用者名稱（用於 @author）</summary>
    name: str = ""
    ## <summary>所屬組織清單（可多組）</summary>
    organizations: list = field( default_factory=list )
    ## <summary>電子信箱（可選）</summary>
    email: str = ""


@dataclass
class LLMConfig:
    """LLM 供應商設定。"""
    ## <summary>供應商名稱（copilot / gemini / ollama）</summary>
    provider: str = "ollama"
    ## <summary>模型名稱</summary>
    model: str = ""
    ## <summary>API Key 環境變數名稱（不直接存密鑰）</summary>
    api_key_env: str = ""
    ## <summary>Ollama 本機 URL</summary>
    ollama_base_url: str = "http://localhost:11434"


@dataclass
class EmbeddingConfig:
    """嵌入模型設定。"""
    ## <summary>模型名稱</summary>
    model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ## <summary>運行裝置（cpu / cuda）</summary>
    device: str = "cpu"
    ## <summary>單一 chunk 最大字元數（MarkdownHeader 切塊後的二次裁切上限）</summary>
    chunk_size: int = 500
    ## <summary>相鄰 chunk 重疊字元數（保留上下文連貫性）</summary>
    chunk_overlap: int = 50


@dataclass
class SearchConfig:
    """搜尋相關設定。"""
    ## <summary>回傳筆數</summary>
    top_k: int = 5
    ## <summary>是否啟用混合搜尋（BM25 + Vector）</summary>
    use_hybrid: bool = True
    ## <summary>預設 BM25 權重（均衡模式）</summary>
    bm25_weight: float = 0.4
    ## <summary>預設 Vector 權重（均衡模式）</summary>
    vector_weight: float = 0.6
    ## <summary>關鍵字模式 BM25 權重（mode=keyword）</summary>
    keyword_bm25_weight: float = 0.7
    ## <summary>語意模式 BM25 權重（mode=semantic）</summary>
    semantic_bm25_weight: float = 0.2
    ## <summary>是否啟用近期偏好重排序</summary>
    recency_bias_enabled: bool = True
    ## <summary>半衰期天數</summary>
    recency_decay_days: int = 90


@dataclass
class DatabaseConfig:
    """資料庫路徑設定。"""
    ## <summary>ChromaDB 目錄（相對於 ENGINE_DIR）</summary>
    chroma_dir: str = "chroma_db"
    ## <summary>RecordManager SQLite 路徑（相對於 ENGINE_DIR）</summary>
    record_db: str = "record_manager_cache.sql"
    ## <summary>ChromaDB 集合名稱</summary>
    collection_name: str = "vault_main"

    def get_chroma_path( self ) -> str:
        """取得 ChromaDB 絕對路徑（frozen 模式使用 DATA_DIR，確保可寫）。"""
        return str( DATA_DIR / self.chroma_dir )

    def get_record_db_url( self ) -> str:
        """取得 RecordManager SQLite URL（frozen 模式使用 DATA_DIR，確保可寫）。"""
        return f"sqlite:///{DATA_DIR / self.record_db}"


@dataclass
class APIConfig:
    """API 伺服器設定。"""
    ## <summary>監聽位址</summary>
    host: str = "127.0.0.1"
    ## <summary>監聽埠</summary>
    port: int = 8000


@dataclass
class GitConfig:
    """Git 版本控制設定。"""
    ## <summary>是否啟用自動提交（每次 write/delete 後 git commit）</summary>
    auto_commit: bool = False
    ## <summary>提交者名稱</summary>
    author_name: str = "AI Memory Vault"
    ## <summary>提交者 Email</summary>
    author_email: str = "vault@localhost"


@dataclass
class VaultPaths:
    """
    Vault 目錄路徑對照表（三層架構：組織 → 專案 → 進度）。
    所有路徑均相對於 AppConfig.vault_path。
    修改此處即可調整整個 Vault 的目錄結構，無需逐一修改程式碼。
    """
    # ── 頂層目錄 ──
    ## <summary>AI 系統設定目錄</summary>
    config: str = "_config"
    ## <summary>工作空間根目錄</summary>
    workspaces: str = "workspaces"
    ## <summary>個人空間根目錄</summary>
    personal: str = "personal"
    ## <summary>知識卡片目錄</summary>
    knowledge: str = "knowledge"
    ## <summary>模板系統根目錄</summary>
    templates: str = "templates"
    ## <summary>附件目錄</summary>
    attachments: str = "attachments"

    # ── _global（跨組織共用）──
    ## <summary>全域共用根目錄</summary>
    global_dir: str = "workspaces/_global"
    ## <summary>全域共用規則</summary>
    global_rules: str = "workspaces/_global/rules"
    ## <summary>全域程式碼片段</summary>
    global_snippets: str = "workspaces/_global/snippets"
    ## <summary>全域技術筆記</summary>
    global_tech_notes: str = "workspaces/_global/tech-notes"
    ## <summary>全域每日回顧連結目錄</summary>
    global_reviews_daily: str = "workspaces/_global/reviews/daily"
    ## <summary>全域每週回顧連結目錄</summary>
    global_reviews_weekly: str = "workspaces/_global/reviews/weekly"
    ## <summary>全域每月回顧連結目錄</summary>
    global_reviews_monthly: str = "workspaces/_global/reviews/monthly"

    # ── 個人空間子目錄 ──
    ## <summary>日記</summary>
    personal_journal: str = "personal/journal"
    ## <summary>學習筆記</summary>
    personal_learning: str = "personal/learning"
    ## <summary>目標</summary>
    personal_goals: str = "personal/goals"
    ## <summary>靈感</summary>
    personal_ideas: str = "personal/ideas"
    ## <summary>個人每日總進度（文本實體）</summary>
    personal_reviews_daily: str = "personal/reviews/daily"
    ## <summary>個人每週總進度（文本實體）</summary>
    personal_reviews_weekly: str = "personal/reviews/weekly"
    ## <summary>個人每月總進度（文本實體）</summary>
    personal_reviews_monthly: str = "personal/reviews/monthly"
    ## <summary>AI 每週對話分析</summary>
    ai_analysis_weekly: str = "personal/ai-analysis/weekly"
    ## <summary>AI 每月對話分析</summary>
    ai_analysis_monthly: str = "personal/ai-analysis/monthly"
    ## <summary>直覺記憶卡片目錄</summary>
    personal_instincts: str = "personal/instincts"

    # ── 模板子目錄 ──
    ## <summary>Agent 模板</summary>
    templates_agents: str = "templates/agents"
    ## <summary>專案模板</summary>
    templates_projects: str = "templates/projects"
    ## <summary>區段模板</summary>
    templates_sections: str = "templates/sections"

    # ── 組織內相對路徑（拼接於 workspaces/{org}/ 之下） ──
    ## <summary>組織規則目錄（相對於組織根）</summary>
    org_rules: str = "rules"
    ## <summary>組織專案根目錄（相對於組織根）</summary>
    org_projects: str = "projects"

    # ── 專案內相對路徑（拼接於 .../projects/{proj}/ 之下） ──
    ## <summary>專案每日詳細進度（相對於專案根）</summary>
    proj_daily: str = "daily"
    ## <summary>專案筆記（相對於專案根）</summary>
    proj_notes: str = "notes"
    ## <summary>專案會議紀錄（相對於專案根）</summary>
    proj_meetings: str = "meetings"
    ## <summary>專案 AI 對話紀錄（相對於專案根）</summary>
    proj_conversations: str = "conversations"
    ## <summary>專案狀態檔（待辦 + 工作脈絡合一，相對於專案根）</summary>
    proj_status: str = "status.md"

    # ── Helper：組織層級 ──────────────────────────────────

    def org_dir( self, iOrg: str ) -> str:
        """取得指定組織的根目錄路徑。"""
        return f"{self.workspaces}/{iOrg}"

    def org_rules_dir( self, iOrg: str ) -> str:
        """取得指定組織的規則目錄路徑。"""
        return f"{self.workspaces}/{iOrg}/{self.org_rules}"

    def org_projects_dir( self, iOrg: str ) -> str:
        """取得指定組織的專案根目錄路徑。"""
        return f"{self.workspaces}/{iOrg}/{self.org_projects}"

    # ── Helper：專案層級 ──────────────────────────────────

    def project_dir( self, iOrg: str, iProject: str ) -> str:
        """取得指定專案的根目錄路徑。"""
        return f"{self.workspaces}/{iOrg}/{self.org_projects}/{iProject}"

    def project_daily_dir( self, iOrg: str, iProject: str ) -> str:
        """取得指定專案的每日進度目錄路徑。"""
        return f"{self.project_dir( iOrg, iProject )}/{self.proj_daily}"

    def project_notes_dir( self, iOrg: str, iProject: str ) -> str:
        """取得指定專案的筆記目錄路徑。"""
        return f"{self.project_dir( iOrg, iProject )}/{self.proj_notes}"

    def project_meetings_dir( self, iOrg: str, iProject: str ) -> str:
        """取得指定專案的會議紀錄目錄路徑。"""
        return f"{self.project_dir( iOrg, iProject )}/{self.proj_meetings}"

    def project_conversations_dir( self, iOrg: str, iProject: str ) -> str:
        """取得指定專案的 AI 對話紀錄目錄路徑。"""
        return f"{self.project_dir( iOrg, iProject )}/{self.proj_conversations}"

    def project_status_file( self, iOrg: str, iProject: str ) -> str:
        """取得指定專案的狀態檔路徑（status.md，待辦 + 工作脈絡 + 決策記錄）。"""
        return f"{self.project_dir( iOrg, iProject )}/{self.proj_status}"

    # ── 骨架目錄列表 ─────────────────────────────────────

    def get_all_dirs( self ) -> list:
        """
        取得初始化時需要建立的所有目錄列表（供 SetupService 使用）。
        不含組織/專案目錄（那些是動態建立的）。

        Returns:
            目錄路徑列表（相對於 vault_path）。
        """
        return [
            self.config,
            self.global_rules,
            self.global_snippets,
            self.global_tech_notes,
            self.global_reviews_daily,
            self.global_reviews_weekly,
            self.global_reviews_monthly,
            self.personal_journal,
            self.personal_learning,
            self.personal_goals,
            self.personal_ideas,
            self.personal_reviews_daily,
            self.personal_reviews_weekly,
            self.personal_reviews_monthly,
            self.ai_analysis_weekly,
            self.ai_analysis_monthly,
            self.personal_instincts,
            self.knowledge,
            self.templates_agents,
            self.templates_projects,
            self.templates_sections,
            self.attachments,
        ]

    def get_project_skeleton_dirs( self ) -> list:
        """
        取得新專案建立時需要建立的子目錄列表。

        Returns:
            相對於專案根目錄的子目錄名稱列表。
        """
        return [
            self.proj_daily,
            self.proj_notes,
            self.proj_meetings,
            self.proj_conversations,
        ]

    def get_initial_files( self ) -> dict:
        """
        取得初始化時需要建立的檔案對照表（相對路徑 → 生成函式名稱）。

        Returns:
            {相對路徑: 生成函式名稱} 字典。
        """
        return {
            f"{self.config}/nav.md": "_gen_nav",
            f"{self.config}/handoff.md": "_gen_handoff",
            f"{self.config}/agents.md": "_gen_agents",
            f"{self.global_dir}/index.md": "_gen_global_index",
            f"{self.personal}/index.md": "_gen_personal_index",
            f"{self.knowledge}/index.md": "_gen_knowledge_index",
            f"{self.templates}/index.md": "_gen_templates_index",
        }

    def parse_project_path( self, iRelPath: str ) -> tuple:
        """
        從相對路徑中解析出組織名稱和專案名稱。

        Args:
            iRelPath: 相對於 vault_path 的路徑。

        Returns:
            (org, project) 若為專案路徑；否則 (None, None)。
        """
        _Parts = iRelPath.replace( "\\", "/" ).split( "/" )
        # 預期格式: workspaces/{org}/projects/{project}/...
        if( len( _Parts ) >= 4
            and _Parts[0] == self.workspaces.split( "/" )[0]
            and _Parts[2] == self.org_projects.split( "/" )[0] ):
            return _Parts[1], _Parts[3]
        return None, None


@dataclass
class AppConfig:
    """應用程式頂層設定。"""
    ## <summary>設定檔版本</summary>
    version: str = "3.0"
    ## <summary>Vault 根目錄絕對路徑</summary>
    vault_path: str = ""
    ## <summary>VS Code / Cursor 全域使用者設定目錄（含 prompts/ 子目錄）</summary>
    vscode_user_path: str = ""
    ## <summary>VS Code chatSessions 目錄（用於 session_extractor 零 Token 對話提取）
    ## 格式：%APPDATA%\Code\User\workspaceStorage\<workspace-id>\chatSessions</summary>
    vscode_chat_dir: str = ""
    ## <summary>Vault 目錄路徑對照表</summary>
    paths: VaultPaths = field( default_factory=VaultPaths )
    ## <summary>使用者資訊</summary>
    user: UserConfig = field( default_factory=UserConfig )
    ## <summary>LLM 設定</summary>
    llm: LLMConfig = field( default_factory=LLMConfig )
    ## <summary>嵌入模型設定</summary>
    embedding: EmbeddingConfig = field( default_factory=EmbeddingConfig )
    ## <summary>搜尋設定</summary>
    search: SearchConfig = field( default_factory=SearchConfig )
    ## <summary>資料庫設定</summary>
    database: DatabaseConfig = field( default_factory=DatabaseConfig )
    ## <summary>API 設定</summary>
    api: APIConfig = field( default_factory=APIConfig )
    ## <summary>Git 版本控制設定</summary>
    git: GitConfig = field( default_factory=GitConfig )
# endregion


# region 分類標籤對照表（對齊 V3 Vault 結構）
CATEGORY_MAP: dict = {
    "workspaces": "💼 工作空間",
    "personal":   "🏠 個人",
    "knowledge":  "📚 知識",
    "templates":  "🧩 模板",
    "_config":    "⚙️ 系統",
}
CATEGORY_UNKNOWN: str = "📁 未分類"
# endregion


# region 索引設定
## <summary>索引時需排除的目錄</summary>
EXCLUDE_DIRS: set = {
    ".venv", "chroma_db", "node_modules",
    ".git", "__pycache__", ".obsidian", ".trash",
}

## <summary>Frontmatter 中要提取的欄位</summary>
FRONTMATTER_FIELDS: list = [
    "type", "domain", "workspace", "organization", "project",
    "severity", "ai_summary", "date", "created", "last_updated",
]
# endregion


# region ConfigManager
class ConfigManager:
    """
    統一設定管理器。
    config.json（主設定）+ .env（敏感密鑰向後相容）。
    """

    @classmethod
    def is_initialized( cls ) -> bool:
        """檢查 config.json 是否存在。"""
        return CONFIG_FILE.exists()

    @classmethod
    def load( cls ) -> AppConfig:
        """
        載入設定。
        優先讀取 config.json；密鑰類欄位可從 .env 覆蓋。

        Returns:
            載入完成的 AppConfig 實例。
        """
        if not CONFIG_FILE.exists():
            return AppConfig()

        with open( CONFIG_FILE, "r", encoding="utf-8" ) as _F:
            _Raw = json.load( _F )

        # 向後相容：舊版 organization: str → organizations: list
        _UserRaw = dict( _Raw.get( "user", {} ) )
        if "organization" in _UserRaw and "organizations" not in _UserRaw:
            _OldOrg = _UserRaw.pop( "organization" )
            _UserRaw["organizations"] = [ _OldOrg ] if _OldOrg else []
        elif "organization" in _UserRaw:
            del _UserRaw["organization"]

        _Config = AppConfig(
            version=_Raw.get( "version", "3.0" ),
            vault_path=_Raw.get( "vault_path", "" ),
            vscode_user_path=_Raw.get( "vscode_user_path", "" ),
            vscode_chat_dir=_Raw.get( "vscode_chat_dir", "" ),
            paths=VaultPaths( **_Raw.get( "paths", {} ) ),
            user=UserConfig( **_UserRaw ),
            llm=LLMConfig( **_Raw.get( "llm", {} ) ),
            embedding=EmbeddingConfig( **_Raw.get( "embedding", {} ) ),
            search=SearchConfig( **_Raw.get( "search", {} ) ),
            database=DatabaseConfig( **_Raw.get( "database", {} ) ),
            api=APIConfig( **_Raw.get( "api", {} ) ),
            git=GitConfig( **_Raw.get( "git", {} ) ),
        )

        # .env 覆蓋：密鑰類欄位從環境變數讀取
        cls._apply_env_overrides( _Config )

        return _Config

    @classmethod
    def save( cls, iConfig: AppConfig ) -> None:
        """
        將設定寫入 config.json。

        Args:
            iConfig: 要保存的 AppConfig 實例。
        """
        _Data = asdict( iConfig )
        with open( CONFIG_FILE, "w", encoding="utf-8" ) as _F:
            json.dump( _Data, _F, indent=4, ensure_ascii=False )

    @classmethod
    def _apply_env_overrides( cls, iConfig: AppConfig ) -> None:
        """
        從環境變數覆蓋密鑰類欄位（向後相容 .env）。

        Args:
            iConfig: 要套用覆蓋的 AppConfig 實例。
        """
        # 嘗試載入 .env（如果存在）
        _EnvFile = ENGINE_DIR / ".env"
        if _EnvFile.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv( str( _EnvFile ), override=False )
            except ImportError:
                pass

        # LLM 密鑰：從 api_key_env 指定的環境變數名稱讀取
        if iConfig.llm.api_key_env:
            _Key = os.environ.get( iConfig.llm.api_key_env, "" )
            if _Key:
                os.environ[iConfig.llm.api_key_env] = _Key
# endregion
