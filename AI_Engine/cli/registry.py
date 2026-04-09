"""
tools/registry.py — 宣告式 CLI 工具登記表 (v2.0)

所有 CLI 工具（自動分發 + 手動 _cmd_*）皆登記於此。
CLI 介面（repl.py）自動從 TOOL_REGISTRY 產生：
  _ALIASES、help 頁面、選單選項、Tab 補全、指令分發。

  - invoke != None → auto-dispatch（positional args → params → invoke()）
  - invoke == None → 保留 repl.py 手動 _cmd_{name}() 方法（複雜互動 / 格式化輸出）

@author gabrielchen
@version 2.0
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
        name="search", alias="s", group="files",
        icon="🔍", menu_label="搜尋記憶庫      (search)",
        help_line="search <query> [--cat C] [--type T] [--mode M]  搜尋記憶庫",
        params=[
            ToolParam( "query", "搜尋關鍵字：", "text" ),
        ],
        invoke=None,   # 保留 _cmd_search（支援 --cat / --type / --mode 旗標）
    ),
    ToolEntry(
        name="read", alias="r", group="files",
        icon="📖", menu_label="讀取筆記        (read)",
        help_line="read <path>           讀取筆記",
        params=[
            ToolParam( "path", "筆記路徑：", "vault_path" ),
        ],
        invoke=None,   # 保留 _cmd_read（格式化輸出）
    ),
    ToolEntry(
        name="write", alias="w", group="files",
        icon="✏️ ", menu_label="寫入筆記        (write)",
        help_line="write <path>          寫入/覆蓋筆記（多行輸入）",
        params=[
            ToolParam( "path", "筆記路徑：", "vault_path" ),
        ],
        invoke=None,   # 保留 _cmd_write（多行互動輸入）
    ),
    ToolEntry(
        name="delete", alias="d", group="files",
        icon="🗑️ ", menu_label="刪除筆記        (delete)",
        help_line="delete <path>         刪除筆記",
        params=[
            ToolParam( "path", "筆記路徑：", "vault_path" ),
        ],
        invoke=None,   # 保留 _cmd_delete（確認提示）
    ),
    ToolEntry(
        name="rename", alias="mv", group="files",
        icon="✂️ ", menu_label="移動或重命名     (rename)",
        help_line="rename <old> <new>    移動或重命名（同步 DB 向量）",
        params=[
            ToolParam( "old_path", "來源路徑：", "vault_path" ),
            ToolParam( "new_path", "目標路徑：", "text" ),
        ],
        invoke=None,   # 保留 _cmd_rename（格式化輸出）
    ),
    ToolEntry(
        name="list", alias="ls", group="files",
        icon="📋", menu_label="列出目錄        (list)",
        help_line="list [<path>] [-r]    列出目錄下 .md 檔案（-r 遞迴）",
        params=[
            ToolParam( "path", "目錄路徑：", "top_folder", required=False ),
        ],
        invoke=None,   # 保留 _cmd_list（格式化表格 + -r 旗標）
    ),
    ToolEntry(
        name="sync", alias="sy", group="files",
        icon="🔄", menu_label="同步 ChromaDB   (sync)",
        help_line="sync                  增量同步 .md → ChromaDB",
        params=[],
        invoke=None,   # 保留 _cmd_sync（格式化輸出）
    ),

    # ── projects ───────────────────────────────────────────────
    ToolEntry(
        name="status", alias="st", group="projects",
        icon="📋", menu_label="專案狀態        (status)",
        help_line="status <org> <proj>   讀取專案狀態",
        params=[
            ToolParam( "org",     "選擇組織：", "org" ),
            ToolParam( "project", "選擇專案：", "project" ),
        ],
        invoke=None,   # 保留 _cmd_status（格式化輸出）
    ),
    ToolEntry(
        name="todo", alias="t", group="projects",
        icon="☑️ ", menu_label="切換 Todo       (todo)",
        help_line="todo <path> <text> [done|undone]  切換 todo 狀態",
        params=[
            ToolParam( "org",     "選擇組織：",  "org" ),
            ToolParam( "project", "選擇專案：",  "project" ),
            ToolParam( "file",    "選擇檔案：",  "project_file" ),
            ToolParam( "text",    "Todo 文字：",  "text" ),
            ToolParam( "state",   "狀態：",       "text", required=False, default="done" ),
        ],
        invoke=None,   # 保留 _cmd_todo（互動式選取）
    ),
    ToolEntry(
        name="projects", alias="p", group="projects",
        icon="📁", menu_label="列出所有專案    (projects)",
        help_line="projects              列出所有組織與專案",
        params=[],
        invoke=None,   # 保留 _cmd_projects（格式化輸出）
    ),
    ToolEntry(
        name="genstatus", alias="gs", group="projects",
        icon="⚙️ ", menu_label="生成 status.md   (genstatus)",
        help_line="genstatus <org> <proj> 生成 status.md 模板（冪等）",
        params=[
            ToolParam( "org",     "選擇組織：",  "org" ),
            ToolParam( "project", "選擇專案：",  "project" ),
        ],
        invoke=lambda sched, _vault, org, project, **_:
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
        invoke=lambda sched, _vault, org, project, date=None, **_:
            sched.generate_project_daily( org, project, date ),
    ),

    ToolEntry(
        name="review", alias="rv", group="reviews",
        icon="📜", menu_label="每日總進度表      (review)",
        help_line="review [<YYYY-MM-DD>]  生成每日總進度表",
        params=[
            ToolParam( "date", "日期（YYYY-MM-DD，留空=今天）：", "date", required=False ),
        ],
        invoke=lambda sched, _vault, date=None, **_:
            sched.generate_daily_summary( date ),
    ),

    ToolEntry(
        name="weekly", alias="wk", group="reviews",
        icon="📆", menu_label="本週總結        (weekly)",
        help_line="weekly                生成本週總進度表",
        params=[],
        invoke=lambda sched, _vault, **_: sched.generate_weekly_summary(),
    ),

    ToolEntry(
        name="monthly", alias="mo", group="reviews",
        icon="🗓️ ", menu_label="本月總結        (monthly)",
        help_line="monthly               生成本月總進度表",
        params=[],
        invoke=lambda sched, _vault, **_: sched.generate_monthly_summary(),
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
        invoke=lambda sched, _vault, org, project, session, content, **_:
            sched.log_conversation( org, project, session, content ),
    ),

    ToolEntry(
        name="aiweekly", alias="aw", group="ai",
        icon="🤖", menu_label="AI 對話週報       (aiweekly)",
        help_line="aiweekly [<YYYY-MM-DD>]             生成 AI 對話週報",
        params=[
            ToolParam( "date", "日期（YYYY-MM-DD，留空=今天）：", "date", required=False ),
        ],
        invoke=lambda sched, _vault, date=None, **_:
            sched.generate_ai_weekly_analysis( date ),
    ),

    ToolEntry(
        name="aimonthly", alias="am", group="ai",
        icon="🤖", menu_label="AI 對話月報       (aimonthly)",
        help_line="aimonthly [<YYYY-MM-DD>]            生成 AI 對話月報",
        params=[
            ToolParam( "date", "日期（YYYY-MM-DD，留空=今天）：", "date", required=False ),
        ],
        invoke=lambda sched, _vault, date=None, **_:
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
        invoke=lambda sched, _vault, org, project, topic, session=None, **_:
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
    ToolEntry(
        name="clean", alias="cl", group="other",
        icon="🧹", menu_label="清除孤立向量    (clean)",
        help_line="clean                 清除孤立向量（DB 有但 .md 已刪）",
        params=[],
        invoke=None,   # 保留 _cmd_clean_orphans（確認提示 + 格式化輸出）
    ),
    ToolEntry(
        name="checkindex", alias="ci", group="other",
        icon="🔍", menu_label="索引狀態檢查    (checkindex)",
        help_line="checkindex            檢查向量索引是否需要重建",
        params=[],
        invoke=None,   # 保留 _cmd_checkindex（格式化輸出）
    ),
    ToolEntry(
        name="reindex", alias="ri", group="other",
        icon="🔄", menu_label="重建向量索引    (reindex)",
        help_line="reindex               清除並重建 ChromaDB 向量索引",
        params=[],
        invoke=None,   # 保留 _cmd_reindex（確認提示 + 格式化輸出）
    ),
]


# ── 快速查找字典 ──────────────────────────────────────────────
REGISTRY_BY_NAME:  dict = { t.name:  t for t in TOOL_REGISTRY }
REGISTRY_BY_ALIAS: dict = { t.alias: t for t in TOOL_REGISTRY }
