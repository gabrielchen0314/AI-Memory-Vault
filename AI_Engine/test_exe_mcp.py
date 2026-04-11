"""
MCP Client 測試腳本 — 連線 frozen exe 並逐一測試所有 40 個 MCP 工具。
"""
import asyncio
import sys
import os
import json
import traceback

sys.path.insert( 0, os.path.dirname( __file__ ) )

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


EXE_PATH = os.path.join( os.path.dirname( __file__ ), "dist", "vault-ai", "vault-mcp.exe" )
EXE_DIR  = os.path.dirname( EXE_PATH )


async def call_tool( session, name, args=None, timeout=120 ):
    """呼叫工具並回傳結果摘要。"""
    try:
        result = await asyncio.wait_for(
            session.call_tool( name, args or {} ),
            timeout=timeout,
        )
        texts = []
        for c in result.content:
            if hasattr( c, 'text' ):
                texts.append( c.text[:200] )
        detail = " | ".join( texts ) if texts else str( result )
        if getattr( result, 'isError', False ):
            return "ERROR", detail
        return "OK", detail
    except asyncio.TimeoutError:
        return "TIMEOUT", f"{timeout}s"
    except Exception as e:
        return "ERROR", f"{type(e).__name__}: {e}"


async def main():
    print( f"[TEST] Connecting to: {EXE_PATH}" )
    print( f"[TEST] CWD: {EXE_DIR}" )

    server_params = StdioServerParameters(
        command=EXE_PATH,
        args=[],
        cwd=EXE_DIR,
    )

    try:
        async with stdio_client( server_params ) as streams:
            read_stream, write_stream = streams
            async with ClientSession( read_stream, write_stream ) as session:
                print( "[TEST] Initializing session..." )
                result = await session.initialize()
                print( f"[TEST] Server: {result.serverInfo}" )

                tools = await session.list_tools()
                print( f"[TEST] Tools count: {len(tools.tools)}" )
                tool_names = sorted( [ t.name for t in tools.tools ] )
                for t in tool_names:
                    print( f"  - {t}" )

                # ── 全面測試計畫（40 unique tools + cleanup） ──
                test_cases = [
                    # ── Phase 1: Read-only tools ──
                    ( "list_projects",        {},                                               30 ),
                    ( "list_notes",           { "directory": "_config" },                       30 ),
                    ( "read_note",            { "file_path": "_config/nav.md" },                30 ),
                    ( "list_agents",          {},                                               30 ),
                    ( "list_skills",          {},                                               30 ),
                    ( "list_instincts",       {},                                               30 ),
                    ( "list_scheduled_tasks", {},                                               30 ),
                    ( "check_index_status",   {},                                               30 ),
                    ( "grep_vault",           { "pattern": "type: system", "max_results": 3 },  30 ),
                    ( "get_project_status",   { "organization": "LIFEOFDEVELOPMENT",
                                                "project": "ai-memory-vault" },                 30 ),

                    # ── Phase 2: Agent / Skill ──
                    ( "dispatch_agent",       { "agent_name": "Architect" },                    30 ),
                    ( "load_skill",           { "skill_name": "ApiMap_Skill.md" },              30 ),

                    # ── Phase 3: Embedding-dependent (search + sync) ──
                    ( "search_vault",         { "query": "sync test", "top_k": 3 },             90 ),
                    ( "search_instincts",     { "query": "debugging", "min_confidence": 0.3 },  90 ),
                    ( "sync_vault",           {},                                              300 ),

                    # ── Phase 4: Note lifecycle (write → edit → rename → delete) ──
                    ( "write_note",           { "file_path": "_test/exe-test.md",
                                                "content": "# Test\n\n測試筆記",
                                                "mode": "overwrite" },                          30 ),
                    ( "edit_note",            { "file_path": "_test/exe-test.md",
                                                "old_text": "測試筆記",
                                                "new_text": "修改後筆記" },                       30 ),
                    ( "rename_note",          { "old_path": "_test/exe-test.md",
                                                "new_path": "_test/exe-renamed.md" },           30 ),
                    ( "delete_note",          { "file_path": "_test/exe-renamed.md" },          30 ),

                    # ── Phase 5: Batch write ──
                    ( "batch_write_notes",    { "notes": [
                                                { "file_path": "_test/b1.md", "content": "# B1" },
                                                { "file_path": "_test/b2.md", "content": "# B2" },
                                              ] },                                             30 ),

                    # ── Phase 6: Todo lifecycle ──
                    ( "write_note",           { "file_path": "_test/todo.md",
                                                "content": "# Todo\n\n## 待辦\n\n- [ ] 原有",
                                                "mode": "overwrite" },                          30 ),
                    ( "add_todo",             { "file_path": "_test/todo.md",
                                                "todo_text": "測試項目",
                                                "section": "待辦" },                            30 ),
                    ( "update_todo",          { "file_path": "_test/todo.md",
                                                "todo_text": "測試項目",
                                                "done": True },                                 30 ),
                    ( "remove_todo",          { "file_path": "_test/todo.md",
                                                "todo_text": "測試項目" },                       30 ),

                    # ── Phase 7: Instinct lifecycle ──
                    ( "create_instinct",      { "id": "exe-test-instinct",
                                                "trigger": "自動化測試觸發",
                                                "domain": "testing",
                                                "title": "Exe 測試直覺",
                                                "action": "自動化測試建立",
                                                "confidence": 0.5 },                           30 ),
                    ( "update_instinct",      { "id": "exe-test-instinct",
                                                "confidence_delta": 0.1,
                                                "new_evidence": "測試驗證通過" },                 30 ),

                    # ── Phase 8: Generate tools ──
                    ( "generate_project_status", { "organization": "TEST_ORG",
                                                   "project": "exe-test" },                     30 ),
                    ( "generate_project_daily",  { "organization": "TEST_ORG",
                                                   "project": "exe-test" },                     30 ),
                    ( "log_ai_conversation",     { "organization": "TEST_ORG",
                                                   "project": "exe-test",
                                                   "session_name": "auto-test",
                                                   "content": "## 自動化測試\n\n測試對話紀錄。" }, 30 ),
                    ( "generate_daily_review",   {},                                             30 ),
                    ( "generate_weekly_review",   {},                                            30 ),
                    ( "generate_monthly_review",  {},                                            30 ),
                    ( "generate_ai_weekly_analysis",  {},                                        60 ),
                    ( "generate_ai_monthly_analysis", {},                                        60 ),
                    ( "generate_retrospective",      {},                                         60 ),
                    ( "run_scheduled_task",           { "task_id": "daily-summary" },            120 ),

                    # ── Phase 9: Knowledge extraction ──
                    ( "extract_knowledge",    { "organization": "TEST_ORG",
                                                "project": "exe-test",
                                                "topic": "測試知識" },                            60 ),

                    # ── Phase 10: Index management ──
                    ( "check_vault_integrity", {},                                               60 ),
                    ( "clean_orphans",         {},                                               60 ),
                    ( "backup_chromadb",        {},                                             120 ),
                    ( "reindex_vault",          {},                                             600 ),

                    # ── Cleanup: 刪除測試產生的檔案 ──
                    ( "delete_note", { "file_path": "_test/b1.md" },                            30 ),
                    ( "delete_note", { "file_path": "_test/b2.md" },                            30 ),
                    ( "delete_note", { "file_path": "_test/todo.md" },                          30 ),
                    ( "delete_note", { "file_path": "personal/instincts/exe-test-instinct.md" }, 30 ),
                ]

                print( f"\n{'='*60}" )
                print( f" Running {len(test_cases)} steps (40 unique tools)" )
                print( f"{'='*60}" )

                passed = 0
                failed = 0
                tested_tools = set()
                failed_tools = []
                for name, args, timeout in test_cases:
                    print( f"\n[{name}] calling...", end=" ", flush=True )
                    status, detail = await call_tool( session, name, args, timeout )
                    if status == "OK":
                        passed += 1
                        tested_tools.add( name )
                        print( f"✓ {detail[:120]}" )
                    else:
                        failed += 1
                        failed_tools.append( ( name, status, detail ) )
                        print( f"✗ {status}: {detail[:200]}" )

                print( f"\n{'='*60}" )
                print( f" Results: {passed} passed, {failed} failed, {len(test_cases)} total" )
                print( f" Unique tools tested: {len(tested_tools)} / 40" )
                if failed_tools:
                    print( f"\n Failed tools:" )
                    for n, s, d in failed_tools:
                        print( f"   ✗ {n}: {s} — {d[:150]}" )
                missing = set(tool_names) - tested_tools
                if missing:
                    print( f"\n Untested tools: {', '.join(sorted(missing))}" )
                print( f"{'='*60}" )

    except BaseException as e:
        if isinstance( e, BaseExceptionGroup ):
            print( f"[TEST] ExceptionGroup with {len(e.exceptions)} sub-exceptions:" )
            for i, sub in enumerate( e.exceptions ):
                print( f"  [{i}] {type(sub).__name__}: {sub}" )
                traceback.print_exception( type(sub), sub, sub.__traceback__ )
        else:
            print( f"[TEST] {type(e).__name__}: {e}" )
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run( main() )
