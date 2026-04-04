"""
tools/registry.py — 宣告式 MCP↔CLI 工具登記表 (v1.0)

新增 MCP 工具方法時，只需在 TOOL_REGISTRY 增加一個 ToolEntry，
CLI 介面（repl.py）即可自動橋接，無需手動修改 8 處：
  _ALIASES、_HELP、_setup_readline、run_menu、_menu_dispatch、
  _dispatch、_cmd_* 方法 × N。

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.1
@date 2026.04.05
"""
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ToolParam:
    """描述一個指令參數的元資料。"""
    name:     str             # kwargs key（也作為 REPL positional arg 名稱）
    prompt:   str             # 選單模式的提示文字
    kind:     str             # "org" | "project" | "date" | "session" | "multiline" | "text"
    required: bool = True
    default:  str  = ""


@dataclass
class ToolEntry:
    """一個可自動橋接到 CLI 的 MCP 工具描述。"""
    name:       str                    # CLI 指令名稱
    alias:      str                    # 短別名（2 字元）
    group:      str                    # "files" | "projects" | "reviews" | "ai" | "other"
    icon:       str                    # 選單圖示
    menu_label: str                    # 選單顯示文字（含 (name)）
    help_line:  str                    # help 頁面的說明文字（含 usage）
    params:     list                   # list[ToolParam]
    invoke:     Optional[Callable]     # None = 保留手動 _cmd_* 方法（複雜輸出格式）


# ── 工具登記表 ────────────────────────────────────────────────
# invoke=None 代表 repl.py 保留對應的手動 _cmd_* 方法（不自動橋接）。
# 新增工具：在此加一個 ToolEntry → CLI 自動更新。

TOOL_REGISTRY: list = [

    # ── files ──────────────────────────────────────────────────
    ToolEntry(
        name="sync", alias="sy", group="files",
        icon="🔄", menu_label="同步 ChromaDB   (sync)",
        help_line="sync                  增量同步 .md → ChromaDB",
        params=[],
        invoke=None,   # 保留 _cmd_sync（格式化輸出）
    ),

    # ── projects ───────────────────────────────────────────────
    ToolEntry(
        name="genstatus", alias="gs", group="projects",
        icon="⚙️ ", menu_label="生成 status.md   (genstatus)",
        help_line="genstatus <org> <proj> 生成 status.md 模板（冪等）",
        params=[
            ToolParam( "org",     "選擇組織：",  "org" ),
            ToolParam( "project", "選擇專案：",  "project" ),
        ],
        invoke=lambda sched, vault, org, project, **_:
            sched.generate_project_status( org, project ),
    ),

    # ── reviews ────────────────────────────────────────────────
    ToolEntry(
        name="daily", alias="da", group="reviews",
        icon="📅", menu_label="每日進度        (daily)",
        help_line="daily <org> <proj> [<YYYY-MM-DD>]  生成/取得專案每日進度",
        params=[
            ToolParam( "org",     "選擇組織：",                      "org" ),
            ToolParam( "project", "選擇專案：",                      "project" ),
            ToolParam( "date",    "日期（YYYY-MM-DD，留空=今天）：", "date", required=False ),
        ],
        invoke=lambda sched, vault, org, project, date=None, **_:
            sched.generate_project_daily( org, project, date ),
    ),

    ToolEntry(
        name="review", alias="rv", group="reviews",
        icon="📜", menu_label="每日總進度表      (review)",
        help_line="review [<YYYY-MM-DD>]  生成每日總進度表",
        params=[
            ToolParam( "date", "日期（YYYY-MM-DD，留空=今天）：", "date", required=False ),
        ],
        invoke=lambda sched, vault, date=None, **_:
            sched.generate_daily_summary( date ),
    ),

    ToolEntry(
        name="weekly", alias="wk", group="reviews",
        icon="📆", menu_label="本週總結        (weekly)",
        help_line="weekly                生成本週總進度表",
        params=[],
        invoke=lambda sched, vault, **_: sched.generate_weekly_summary(),
    ),

    ToolEntry(
        name="monthly", alias="mo", group="reviews",
        icon="🗓️ ", menu_label="本月總結        (monthly)",
        help_line="monthly               生成本月總進度表",
        params=[],
        invoke=lambda sched, vault, **_: sched.generate_monthly_summary(),
    ),

    # ── ai ─────────────────────────────────────────────────────
    ToolEntry(
        name="log", alias="la", group="ai",
        icon="💬", menu_label="記錄 AI 對話      (log)",
        help_line="log <org> <proj> <session>          記錄 AI 對話",
        params=[
            ToolParam( "org",     "選擇組織：",                         "org" ),
            ToolParam( "project", "選擇專案：",                         "project" ),
            ToolParam( "session", "Session 名稱（例：vault-debug）：",  "session" ),
            ToolParam( "content", "輸入對話內容（空行結束）：",         "multiline" ),
        ],
        invoke=lambda sched, vault, org, project, session, content, **_:
            sched.log_conversation( org, project, session, content ),
    ),

    ToolEntry(
        name="aiweekly", alias="aw", group="ai",
        icon="🤖", menu_label="AI 對話週報       (aiweekly)",
        help_line="aiweekly [<YYYY-MM-DD>]             生成 AI 對話週報",
        params=[
            ToolParam( "date", "日期（YYYY-MM-DD，留空=今天）：", "date", required=False ),
        ],
        invoke=lambda sched, vault, date=None, **_:
            sched.generate_ai_weekly_analysis( date ),
    ),

    ToolEntry(
        name="aimonthly", alias="am", group="ai",
        icon="🤖", menu_label="AI 對話月報       (aimonthly)",
        help_line="aimonthly [<YYYY-MM-DD>]            生成 AI 對話月報",
        params=[
            ToolParam( "date", "日期（YYYY-MM-DD，留空=今天）：", "date", required=False ),
        ],
        invoke=lambda sched, vault, date=None, **_:
            sched.generate_ai_monthly_analysis( date ),
    ),

    ToolEntry(
        name="extract", alias="ex", group="ai",
        icon="🧠", menu_label="萃取知識卡片      (extract)",
        help_line="extract <org> <proj> <topic> [<session>]  從 conversations/ 生成知識卡片",
        params=[
            ToolParam( "org",     "選擇組織：",                           "org" ),
            ToolParam( "project", "選擇專案：",                           "project" ),
            ToolParam( "topic",   "知識主題（英文 slug，例如 git-hooks）：", "text" ),
            ToolParam( "session", "篩選 session（留空=全部）：",           "session", required=False ),
        ],
        invoke=lambda sched, vault, org, project, topic, session=None, **_:
            sched.extract_knowledge( org, project, topic, session ),
    ),

    # ── other ──────────────────────────────────────────────────
    ToolEntry(
        name="integrity", alias="ig", group="other",
        icon="🛡️ ", menu_label="完整性檢查      (integrity)",
        help_line="integrity             檢查 ChromaDB 向量完整性",
        params=[],
        invoke=None,   # 保留 _cmd_integrity（格式化輸出）
    ),
]


# ── 快速查找字典 ──────────────────────────────────────────────
REGISTRY_BY_NAME:  dict = { t.name:  t for t in TOOL_REGISTRY }
REGISTRY_BY_ALIAS: dict = { t.alias: t for t in TOOL_REGISTRY }
