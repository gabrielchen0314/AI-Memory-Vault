"""
VS Code chatSessions Extractor
從 VS Code 的 chatSessions/*.jsonl 解析 Copilot Chat 對話記錄，
寫入 Vault conversations/ 目錄，不消耗任何 LLM Token。

資料格式（chatSessions/*.jsonl 每行一個 JSON）：
  kind=0 → Session header（sessionId、creationDate）
  kind=1 → 差異更新（user message、selection、image 等）
  kind=2 → Request 快照列表（包含 user text + AI markdown + tool calls）

提取策略：
  1. 掃描所有 kind=2 行，合併出最新完整 request 列表（後者覆蓋前者）
  2. 按 timestamp 排序後，過濾 > watermark.last_ts 的新 request
  3. 產生 Markdown（增量附加至同一 session 的現有檔案）
  4. 更新 watermark 記錄 last_ts 與累計 Q 數

@author gabrielchen
@version 1.0
@since AI-Memory-Vault 3.7
@date 2026.04.12
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import DATA_DIR

_logger = logging.getLogger( __name__ )


class SessionExtractor:
    """
    從 VS Code chatSessions/*.jsonl 提取 Q&A 對話，寫入 Vault conversations/。

    watermark 格式（存於 DATA_DIR/vscode_sessions_watermark.json）：
      { "<session_id>": { "last_ts": <int ms>, "count": <int> }, ... }
    """

    _WATERMARK_FILENAME: str = "vscode_sessions_watermark.json"

    def __init__( self, iChatSessionsDir: str, iVaultRoot: str ):
        """
        Args:
            iChatSessionsDir: VS Code workspaceStorage/{id}/chatSessions/ 完整路徑。
            iVaultRoot:       Vault 根目錄（AppConfig.vault_path）。
        """
        self._chat_dir   = Path( iChatSessionsDir )
        self._vault_root = Path( iVaultRoot )
        self._watermark  = self._load_watermark()

    # ─────────────────────────────────────────────
    #region Watermark

    def _watermark_path( self ) -> Path:
        # 存放在可寫資料目錄（DATA_DIR），避免被索引進向量庫
        return DATA_DIR / self._WATERMARK_FILENAME

    def _load_watermark( self ) -> dict:
        p = self._watermark_path()
        if p.exists():
            try:
                return json.loads( p.read_text( encoding="utf-8" ) )
            except Exception:
                pass
        return {}

    def _save_watermark( self ) -> None:
        p = self._watermark_path()
        p.write_text(
            json.dumps( self._watermark, ensure_ascii=False, indent=2 ),
            encoding="utf-8"
        )

    #endregion

    # ─────────────────────────────────────────────
    #region JSONL Parsing

    def _get_session_header( self, iJsonlPath: Path ) -> dict:
        try:
            with open( iJsonlPath, encoding="utf-8" ) as f:
                first = json.loads( f.readline() )
            if first.get( "kind" ) == 0:
                return first.get( "v", {} )
        except Exception:
            pass
        return {}

    def _get_all_requests( self, iJsonlPath: Path ) -> dict:
        """
        掃描整個 JSONL，合併所有 kind=2 行的 requests（後者覆蓋前者）。

        Returns:
            { requestId: { timestamp, user_text, ai_text, tool_calls } }
        """
        requests: dict = {}
        try:
            with open( iJsonlPath, encoding="utf-8" ) as f:
                for line in f:
                    try:
                        obj = json.loads( line )
                    except json.JSONDecodeError:
                        continue

                    if obj.get( "kind" ) != 2:
                        continue

                    v = obj.get( "v" )
                    if not isinstance( v, list ):
                        continue

                    for req in v:
                        if not isinstance( req, dict ):
                            continue
                        rid = req.get( "requestId" )
                        if not rid:
                            continue
                        parsed = self._parse_request( req )
                        if parsed:
                            requests[ rid ] = parsed

        except Exception as e:
            _logger.warning( f"[SessionExtractor] 讀取 {iJsonlPath.name} 失敗: {e}" )

        return requests

    def _parse_request( self, iReq: dict ) -> Optional[ dict ]:
        """
        解析單一 request 物件。

        Returns:
            { timestamp, user_text, ai_text, tool_calls } 或 None（空內容）。
        """
        # ── User message ──
        msg       = iReq.get( "message", {} )
        user_text = ""
        if isinstance( msg, dict ):
            user_text = ( msg.get( "text" ) or "" ).strip()

        # ── AI response items ──
        # • 無 "kind" 欄位的項目 + value 為字串 → AI markdown 文字
        # • kind == "toolInvocationSerialized"    → tool call（toolId 欄位）
        ai_parts   = []
        tool_calls = []
        resp       = iReq.get( "response", [] )

        if isinstance( resp, list ):
            for r in resp:
                if not isinstance( r, dict ):
                    continue
                rk = r.get( "kind" )          # None 表示無 kind 欄位
                if rk is None:
                    val = r.get( "value", "" )
                    if isinstance( val, str ) and val.strip():
                        ai_parts.append( val.strip() )
                elif rk == "toolInvocationSerialized":
                    tool_id = r.get( "toolId", "" )
                    if tool_id:
                        tool_calls.append( tool_id )

        ai_text = "\n\n".join( ai_parts )
        if not user_text and not ai_text:
            return None

        return {
            "timestamp":  iReq.get( "timestamp", 0 ),
            "user_text":  user_text,
            "ai_text":    ai_text,
            "tool_calls": tool_calls,
        }

    #endregion

    # ─────────────────────────────────────────────
    #region Markdown Generation

    def _to_markdown(
        self,
        iSessionId: str,
        iSessionDate: str,
        iRequests: list,
        iStartQNum: int = 1,
    ) -> str:
        """
        將 request 列表轉換為 Vault 對話 Markdown。

        Args:
            iStartQNum: 第一個 Q 的編號（增量附加時從現有最後一個 +1 開始）。
        """
        if not iRequests:
            return ""

        short_id = iSessionId[:8]
        now_str  = datetime.now().strftime( "%Y-%m-%d %H:%M" )
        total_q  = iStartQNum + len( iRequests ) - 1

        lines = [
            "---",
            "type: conversation",
            "source: vscode-chat-session",
            f"session_id: {iSessionId}",
            f"date: {iSessionDate[:10]}",
            f"extracted: {now_str}",
            f"qa_count: {total_q}",
            "---",
            "",
            f"# VS Code 對話紀錄 — {iSessionDate[:10]} ({short_id})",
            "",
        ]

        for idx, req in enumerate( iRequests ):
            q_num    = iStartQNum + idx
            ts       = req[ "timestamp" ]
            dt       = datetime.fromtimestamp( ts / 1000, tz=timezone.utc ).astimezone() if ts else None
            time_str = dt.strftime( "%H:%M" ) if dt else "?"
            user     = req[ "user_text" ]
            ai       = req[ "ai_text" ]
            tools    = req[ "tool_calls" ]

            lines.append( f"## Q{q_num}（{time_str}）" )
            lines.append( "" )

            if user:
                lines.append( "**使用者：**" )
                lines.append( "" )
                lines.append( user )
                lines.append( "" )

            if tools:
                unique_tools = list( dict.fromkeys( tools ) )
                lines.append( f"**工具：** {', '.join( unique_tools )}" )
                lines.append( "" )

            if ai:
                lines.append( "**AI：**" )
                lines.append( "" )
                lines.append( ai )
                lines.append( "" )

        return "\n".join( lines )

    #endregion

    # ─────────────────────────────────────────────
    #region Public API

    def extract_new( self, iOrg: str, iProject: str ) -> int:
        """
        提取 chatSessions/ 中所有新增的 Q&A 對話，寫入 Vault conversations/。

        Args:
            iOrg:     Vault 組織名稱（如 LIFEOFDEVELOPMENT）。
            iProject: 專案名稱（如 ai-memory-vault）。

        Returns:
            寫入或更新的對話檔案數量。
        """
        if not self._chat_dir.exists():
            _logger.warning( f"[SessionExtractor] chatSessions 目錄不存在: {self._chat_dir}" )
            return 0

        conv_dir = (
            self._vault_root
            / "workspaces" / iOrg / "projects" / iProject / "conversations"
        )
        conv_dir.mkdir( parents=True, exist_ok=True )

        written = 0

        for jsonl_path in sorted( self._chat_dir.glob( "*.jsonl" ) ):
            session_id = jsonl_path.stem
            wm         = self._watermark.get( session_id, { "last_ts": 0, "count": 0 } )
            last_ts    = wm[ "last_ts" ]

            # 取所有 requests（後者覆蓋前者的最新快照合併）
            all_reqs = self._get_all_requests( jsonl_path )
            if not all_reqs:
                continue

            # 按時間排序，過濾出新增的
            sorted_reqs = sorted( all_reqs.values(), key=lambda r: r[ "timestamp" ] )
            new_reqs    = [ r for r in sorted_reqs if r[ "timestamp" ] > last_ts ]

            if not new_reqs:
                continue

            # Session 建立日期（from header）
            header   = self._get_session_header( jsonl_path )
            raw_ts   = header.get( "creationDate", 0 )
            if raw_ts:
                session_date = datetime.fromtimestamp(
                    raw_ts / 1000, tz=timezone.utc
                ).strftime( "%Y-%m-%d" )
            else:
                session_date = datetime.now().strftime( "%Y-%m-%d" )

            # 輸出路徑
            short_id = session_id[:8]
            fname    = f"{session_date}_vscode-{short_id}.md"
            out_path = conv_dir / fname

            # 若已存在（增量），讀出現有最後一個 Q 編號後附加
            start_q = 1
            if out_path.exists():
                existing = out_path.read_text( encoding="utf-8" )
                q_nums = re.findall( r"^## Q(\d+)", existing, re.MULTILINE )
                if q_nums:
                    start_q = int( q_nums[ -1 ] ) + 1

            md = self._to_markdown( session_id, session_date, new_reqs, start_q )
            if not md:
                continue

            if start_q > 1:
                # 附加模式：更新 frontmatter 的 qa_count 並接在後面
                existing = out_path.read_text( encoding="utf-8" )
                new_total = start_q - 1 + len( new_reqs )
                existing = re.sub(
                    r"^qa_count: \d+",
                    f"qa_count: {new_total}",
                    existing,
                    flags=re.MULTILINE
                )
                # 從 md 中去掉開頭的 frontmatter + 標題（只保留 Q blocks）
                q_block_start = md.find( "\n## Q" )
                if q_block_start != -1:
                    append_part = md[ q_block_start: ]
                    out_path.write_text(
                        existing.rstrip() + "\n" + append_part,
                        encoding="utf-8"
                    )
                else:
                    out_path.write_text( existing, encoding="utf-8" )
            else:
                out_path.write_text( md, encoding="utf-8" )

            # 更新 watermark
            new_last_ts = max( r[ "timestamp" ] for r in new_reqs )
            self._watermark[ session_id ] = {
                "last_ts": new_last_ts,
                "count":   wm[ "count" ] + len( new_reqs ),
            }

            written += 1
            _logger.info(
                f"[SessionExtractor] {fname} → +{len( new_reqs )} Q&A "
                f"（累計 {wm['count'] + len( new_reqs )} 筆）"
            )

        self._save_watermark()
        return written

    def status( self ) -> dict:
        """
        回傳各 session 的提取狀態（供 MCP 工具查詢用）。

        Returns:
            { session_id: { "last_ts": int, "count": int, "file_exists": bool } }
        """
        result = {}
        for session_id, wm in self._watermark.items():
            # 找對應的 jsonl 對照日期
            jsonl_path = self._chat_dir / f"{session_id}.jsonl"
            header     = self._get_session_header( jsonl_path ) if jsonl_path.exists() else {}
            raw_ts     = header.get( "creationDate", 0 )
            session_date = (
                datetime.fromtimestamp( raw_ts / 1000, tz=timezone.utc ).strftime( "%Y-%m-%d" )
                if raw_ts else "unknown"
            )
            result[ session_id ] = {
                "date":    session_date,
                "last_ts": wm[ "last_ts" ],
                "count":   wm[ "count" ],
            }
        return result

    def extract_metadata( self, iSessionId: str ) -> dict:
        """
        從指定 session JSONL 中自動提取結構化元資料。

        解析來源（最後一個 kind=2 快照的 v 陣列）：
          - kind=textEditGroup         → files_changed（修改過的檔案路徑）
          - kind=toolInvocationSerialized + toolSpecificData.kind=terminal → commands

        Returns:
            {
                "files_changed": [{"path": str, "action": "修改"}],
                "commands":      [{"command": str, "purpose": "", "result": str}],
            }
        """
        jsonl_path = self._chat_dir / f"{iSessionId}.jsonl"
        if not jsonl_path.exists():
            return { "files_changed": [], "commands": [] }

        files_seen:    dict = {}   # path → action
        commands_seen: dict = {}   # toolCallId → cmd dict（去重）

        try:
            with open( jsonl_path, encoding="utf-8" ) as f:
                for line in f:
                    try:
                        obj = json.loads( line )
                    except json.JSONDecodeError:
                        continue
                    if obj.get( "kind" ) != 2:
                        continue

                    for item in obj.get( "v", [] ):
                        if not isinstance( item, dict ):
                            continue
                        k = item.get( "kind" )

                        # ── 檔案修改 ──
                        if k == "textEditGroup":
                            uri  = item.get( "uri", "" )
                            path = ""
                            if isinstance( uri, dict ):
                                path = uri.get( "fsPath" ) or uri.get( "path", "" )
                            elif isinstance( uri, str ):
                                path = uri.replace( "file:///", "" ).replace( "%3A", ":" ).replace( "/", "\\" )
                            if path and not path.endswith( (".pyc", ".pyo") ):
                                files_seen[ path ] = "修改"

                        # ── Terminal 指令 ──
                        elif k == "toolInvocationSerialized":
                            td = item.get( "toolSpecificData" )
                            if isinstance( td, dict ) and td.get( "kind" ) == "terminal":
                                cmd_info = td.get( "commandLine", {} )
                                cmd = ( cmd_info.get( "original" ) or "" ) if isinstance( cmd_info, dict ) else ""
                                call_id = item.get( "toolCallId", cmd[:40] )
                                if cmd and call_id not in commands_seen:
                                    done = item.get( "isComplete", True )
                                    commands_seen[ call_id ] = {
                                        "command": cmd[ :300 ],
                                        "purpose": "",
                                        "result":  "完成" if done else "?",
                                    }

        except Exception as e:
            _logger.warning( f"[SessionExtractor.extract_metadata] {e}" )
            return { "files_changed": [], "commands": [] }

        return {
            "files_changed": [ { "path": p, "action": a } for p, a in files_seen.items() ],
            "commands":      list( commands_seen.values() ),
        }

    def extract_script(
        self,
        iSessionId:  str,
        iScriptType: str = "powershell",
    ) -> str:
        """
        從指定 session 提取所有 terminal 指令，輸出為可執行腳本。

        Args:
            iSessionId:  session UUID。
            iScriptType: "powershell" | "python"

        Returns:
            腳本字串（空字串表示無指令）。
        """
        meta = self.extract_metadata( iSessionId )
        cmds = meta.get( "commands", [] )
        if not cmds:
            return ""

        header = self._get_session_header( self._chat_dir / f"{iSessionId}.jsonl" )
        raw_ts      = header.get( "creationDate", 0 )
        session_date = (
            datetime.fromtimestamp( raw_ts / 1000, tz=timezone.utc ).strftime( "%Y-%m-%d" )
            if raw_ts else "unknown"
        )

        lines: list = []
        if iScriptType == "powershell":
            lines.append( f"# Auto-extracted from VS Code session {iSessionId[:8]} ({session_date})" )
            lines.append( f"# 共 {len(cmds)} 個指令\n" )
            for i, c in enumerate( cmds, 1 ):
                purpose = c.get( "purpose" ) or f"步驟 {i}"
                lines.append( f"# [{i}] {purpose}" )
                lines.append( c[ "command" ] )
                lines.append( "" )
        else:  # python shell script style
            lines.append( f"# Auto-extracted from VS Code session {iSessionId[:8]} ({session_date})" )
            lines.append( f"import subprocess, sys\n" )
            for i, c in enumerate( cmds, 1 ):
                purpose = c.get( "purpose" ) or f"步驟 {i}"
                lines.append( f"# [{i}] {purpose}" )
                cmd_escaped = c[ "command" ].replace( '"', '\\"' )
                lines.append( f'subprocess.run([r"{cmd_escaped}"], shell=True, check=True)' )
                lines.append( "" )

        return "\n".join( lines )

    #endregion
