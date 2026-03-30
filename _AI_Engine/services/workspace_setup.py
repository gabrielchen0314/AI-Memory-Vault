"""
Workspace Setup Service
MCP Server 啟動時自動偵測 Vault 內容，在 VS Code 全域設定中建立：
  1. 每個 templates/agents/*.md → 全域 {name}.agent.md
  2. work/*/rules/*.md 清單    → 全域 vault-coding-rules.instructions.md

所有操作均為冪等（Idempotent）：已存在的檔案直接跳過。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 2.2
@date 2026.03.30
"""
import os
import platform
from pathlib import Path

import yaml

from config import VAULT_ROOT


class WorkspaceSetupService:
    """
    自動偵測 Vault Agent 定義與規則，並在 VS Code 全域設定中建立對應連結檔案。
    所有寫入操作均為冪等：目標檔案存在則跳過，不覆蓋使用者手動修改的內容。
    """

    #region 常數定義
    AGENTS_VAULT_DIR: str        = "templates/agents"
    RULES_INSTRUCTIONS_FILE: str = "vault-coding-rules.instructions.md"
    DEFAULT_MCP_TOOLS: list      = ["read_note", "search_vault"]
    DEFAULT_EDITOR_TOOLS: list   = ["read", "edit", "search", "execute", "todo"]
    #endregion

    #region 私有方法
    @classmethod
    def _find_vscode_prompts_dir( cls ) -> Path | None:
        """
        依作業系統偵測 VS Code 全域 prompts 目錄。
        依序嘗試 Stable → Insiders，找到存在的目錄即回傳。

        Returns:
            存在的 prompts 目錄 Path，或 None（找不到時）。
        """
        _System = platform.system()

        if _System == "Windows":
            _Base = Path( os.environ.get( "APPDATA", "" ) )
        elif _System == "Darwin":
            _Base = Path.home() / "Library" / "Application Support"
        else:
            _Base = Path( os.environ.get( "XDG_CONFIG_HOME", str( Path.home() / ".config" ) ) )

        for _Variant in ( "Code", "Code - Insiders" ):
            _Dir = _Base / _Variant / "User" / "prompts"
            if _Dir.exists():
                return _Dir

        return None

    @classmethod
    def _parse_frontmatter( cls, iContent: str ) -> dict:
        """
        解析 Markdown 的 YAML Frontmatter（--- 區塊）。

        Args:
            iContent: 完整的 Markdown 文字內容。

        Returns:
            解析後的欄位字典，若無 Frontmatter 回傳空 dict。
        """
        if not iContent.startswith( "---" ):
            return {}

        _End = iContent.find( "\n---", 3 )
        if _End == -1:
            return {}

        try:
            _Parsed = yaml.safe_load( iContent[3:_End].strip() )
            return _Parsed if isinstance( _Parsed, dict ) else {}
        except yaml.YAMLError:
            return {}

    @classmethod
    def _collect_rule_files( cls ) -> list[str]:
        """
        掃描 work/*/rules/*.md（排除 index.md），
        回傳相對於 Vault 根目錄的路徑清單（posix 格式）。

        Returns:
            規則檔案的相對路徑清單。
        """
        _WorkDir = Path( VAULT_ROOT ) / "work"
        _Rules = []

        if not _WorkDir.exists():
            return _Rules

        for _Company in sorted( _WorkDir.iterdir() ):
            if not _Company.is_dir() or _Company.name.startswith( "_" ):
                continue

            _RulesDir = _Company / "rules"
            if not _RulesDir.exists():
                continue

            for _File in sorted( _RulesDir.glob( "*.md" ) ):
                if _File.stem.lower() != "index":
                    _Rules.append( _File.relative_to( VAULT_ROOT ).as_posix() )

        return _Rules

    @classmethod
    def _build_agent_md( cls, iAgentName: str, iFm: dict ) -> str:
        """
        依 Vault Agent 定義的 Frontmatter 產生 .agent.md 內容。
        工具清單從 mcp_tools / editor_tools 欄位讀取，無硬編碼對照表。

        Args:
            iAgentName: Agent 名稱（對應 templates/agents/ 的 stem）。
            iFm:        已解析的 Frontmatter 字典。

        Returns:
            完整的 .agent.md 字串。
        """
        _DisplayName  = iFm.get( "agent", iAgentName.replace( "-", " " ).title() )
        _Summary      = iFm.get( "ai_summary", f"{_DisplayName} 專業 Agent" )
        _Trigger      = iFm.get( "trigger", "" )
        _Description  = f"{_DisplayName} — {_Summary}"[:120]
        _ArgumentHint = _Trigger.replace( "@", "" ) if _Trigger else f"描述任務給 {_DisplayName}"

        # 從 frontmatter 讀取工具清單，找不到則用預設值
        _McpTools    = iFm.get( "mcp_tools", cls.DEFAULT_MCP_TOOLS )
        _EditorTools = iFm.get( "editor_tools", cls.DEFAULT_EDITOR_TOOLS )

        _AllTools  = [f"ai-memory-vault/{_T}" for _T in _McpTools] + list( _EditorTools )
        _ToolsYaml = "\n".join( f"  - {_T}" for _T in _AllTools )
        _VaultPath = f"D:/AI-Memory-Vault/templates/agents/{iAgentName}.md"

        return (
            f"---\n"
            f"description: \"{_Description}\"\n"
            f"tools:\n{_ToolsYaml}\n"
            f"argument-hint: \"{_ArgumentHint}\"\n"
            f"---\n\n"
            f"使用 `read_note` 工具讀取 `{_VaultPath}`，完整載入 {_DisplayName} Agent 的角色定義與工作流程。\n\n"
            f"載入完成後，以該角色的身份處理使用者提供的任務。\n"
        )

    @classmethod
    def _build_rules_instructions( cls, iRuleFiles: list[str] ) -> str:
        """
        依規則檔案清單產生 vault-coding-rules.instructions.md 內容。

        Args:
            iRuleFiles: 規則檔案的相對路徑清單（posix 格式）。

        Returns:
            完整的 .instructions.md 字串。
        """
        _RulesList = "\n".join(
            f"- `{_P}` — {Path( _P ).stem.replace( '-', ' ' ).title()}"
            for _P in iRuleFiles
        )

        return (
            f"---\n"
            f"applyTo: \"**\"\n"
            f"---\n\n"
            f"# AI Memory Vault — 編碼規則\n\n"
            f"此設定關聯的 AI Memory Vault 含有以下編碼規則。\n"
            f"協助撰寫程式碼、Code Review 或設計架構時，\n"
            f"請透過 `read_note`（`ai-memory-vault` MCP）讀取相關規則後再回應。\n\n"
            f"## 規則清單\n\n"
            f"{_RulesList}\n"
        )
    #endregion

    #region 公開方法
    @classmethod
    def setup( cls ) -> dict:
        """
        執行全量偵測並建立缺少的 VS Code 設定檔案。

        Returns:
            dict: {
                "agents_created": list[str],
                "agents_skipped": list[str],
                "rules_created":  bool,
                "rules_skipped":  bool,
                "error":          str | None,
            }
        """
        _Stats = {
            "agents_created": [],
            "agents_skipped": [],
            "rules_created":  False,
            "rules_skipped":  False,
            "error":          None,
        }

        _PromptsDir = cls._find_vscode_prompts_dir()
        if _PromptsDir is None:
            _Stats["error"] = "VS Code user prompts directory not found."
            return _Stats

        # ── 1. Agent .agent.md ─────────────────────────────────
        _AgentsDir = Path( VAULT_ROOT ) / cls.AGENTS_VAULT_DIR
        if _AgentsDir.exists():
            for _AgentFile in sorted( _AgentsDir.glob( "*.md" ) ):
                _Name   = _AgentFile.stem
                _Fm     = cls._parse_frontmatter( _AgentFile.read_text( encoding="utf-8" ) )

                # 若 editor_tools 中無任何可編輯動作，以 Ask_ 為前置
                _EditorTools    = _Fm.get( "editor_tools", cls.DEFAULT_EDITOR_TOOLS )
                _EDIT_ACTIONS   = { "edit" }
                _HasEditAction  = bool( _EDIT_ACTIONS & set( _EditorTools ) )
                _Prefix         = "" if _HasEditAction else "Ask_"
                _Target         = _PromptsDir / f"{_Prefix}{_Name}.agent.md"

                if _Target.exists():
                    _Stats["agents_skipped"].append( f"{_Prefix}{_Name}" )
                    continue

                _Target.write_text( cls._build_agent_md( _Name, _Fm ), encoding="utf-8" )
                _Stats["agents_created"].append( f"{_Prefix}{_Name}" )

        # ── 2. Rules .instructions.md ──────────────────────────
        _RulesTarget = _PromptsDir / cls.RULES_INSTRUCTIONS_FILE
        if _RulesTarget.exists():
            _Stats["rules_skipped"] = True
        else:
            _RuleFiles = cls._collect_rule_files()
            if _RuleFiles:
                _RulesTarget.write_text(
                    cls._build_rules_instructions( _RuleFiles ),
                    encoding="utf-8"
                )
                _Stats["rules_created"] = True

        return _Stats
    #endregion
