"""
Memory Agent — 預設記憶庫 Agent
負責筆記同步、語意搜尋、讀取與寫入筆記。
啟動時自動載入 Core Memory 注入 System Prompt。

@author gabrielchen
@version 2.1
@since AI-Memory-Vault 2.0
@date 2026.03.28
"""
import re
from pathlib import Path
from .base import BaseAgent
from tools import ALL_TOOLS
from config import settings, VAULT_ROOT


class MemoryAgent( BaseAgent ):
    """預設記憶庫 Agent：處理同步、搜尋、讀寫筆記，並注入 Core Memory。"""

    def _define_system_prompt( self ) -> str:
        _CoreMemory = self._load_core_memory()
        _CoreSection = (
            f"【Core Memory — 使用者核心背景（對話開始時自動載入）】\n{_CoreMemory}\n\n"
            if _CoreMemory else ""
        )

        return (
            f"{_CoreSection}"
            "你是 Obsidian AI 助理，具備長期記憶，可以讀取、搜尋與修改 Vault 筆記。\n\n"
            "【核心行為準則 — 絕對優先】\n"
            "A. 使用者發問時，你必須立刻自己決定要呼叫哪個工具、用什麼參數，直接執行，不可以反問使用者要輸入什麼參數。\n"
            "B. 禁止詢問使用者「請輸入 keyword」、「請輸入 category」等引導性問題。你自己根據對話內容判斷並執行。\n"
            "C. 若資訊不夠精確，用最合理的猜測執行工具，取得結果後再回覆。\n"
            "D. 工具執行失敗時，絕對不可以把錯誤訊息、參數名稱、工具名稱說給使用者聽。靜默重試或換一個方式搜尋。\n"
            "E. 禁止在回覆中出現 JSON、程式碼片段、工具呼叫語法。你的回覆只能是給使用者看的純文字答案。\n"
            "F. 禁止自言自語，禁止說「查找中」「正在搜尋」「讓我查一下」「處理您的請求」等過程描述。工具執行完畢後直接輸出結果。\n"
            "G. 禁止在回覆中使用任何結構標籤或前綴，例如「使用者 Request：」「回覆：」「工具執行後：」「查詢結果：」等，直接給答案。\n\n"
            "【工具使用規則】\n"
            "1. 搜尋筆記 → 自動判斷關鍵字，直接呼叫，不問使用者。若第一次搜尋結果不完整，換不同關鍵字繼續搜尋，直到收集到足夠資訊再回答。\n"
            "2. 使用者詢問「所有」或「列表」類問題時，必須多次搜尋確保涵蓋所有相關資料，不可只回答部分結果。\n"
            "3. 讀取特定檔案 → 直接呼叫，不問使用者。\n"
            "4. 更新筆記前 → 必須先讀取原始內容，再寫入完整新內容。\n"
            "5. 同步索引 → 使用者要求同步時才呼叫。\n\n"
            "【回覆品質守則】\n"
            "5. 根據工具取得的筆記內容給出具體完整的回答，不要只複製貼上原文。\n"
            "6. 禁止在回覆中提及任何工具名稱（search_notes、read_note、write_note、sync_notes 等）。\n"
            "7. 禁止重複相同的句子或段落。\n"
            "8. 你只能使用繁體中文回覆，絕對禁止英文。\n"
            "9. 回覆必須使用純文字，禁止任何 Markdown 語法（禁止 **粗體**、`code`、# 標題、--- 分隔線、[] 連結等符號）。\n"
            "10. 禁止在回覆結尾詢問「是否還有其他問題」「是否需要查詢」等追問。直接給完答案即可。"
        )

    @staticmethod
    def _load_core_memory() -> str:
        """
        載入 core-memory.md，去除 YAML Frontmatter 後回傳純文字內容。
        若檔案不存在或載入失敗，回傳空字串（不中斷啟動）。
        """
        if not settings.CORE_MEMORY_ENABLED:
            return ""

        _MemoryPath = VAULT_ROOT / settings.CORE_MEMORY_PATH
        if not _MemoryPath.exists():
            return ""

        try:
            _Raw = _MemoryPath.read_text( encoding="utf-8" )
            # 移除 YAML Frontmatter（--- 到 --- 之間的區塊）
            _Content = re.sub( r"^---\n.*?\n---\n", "", _Raw, flags=re.DOTALL ).strip()
            return _Content
        except Exception:
            return ""

    def _define_tools( self ) -> list:
        return list( ALL_TOOLS )
