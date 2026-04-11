## 對話摘要

修復 PyInstaller frozen exe 的 MCP 模式崩潰問題（exit code 0xC0000409 STATUS_STACK_BUFFER_OVERRUN），根因分析、修復、清理、重建索引。

### 主要成果
1. **找到根因**：`langchain_text_splitters/__init__.py` 在 import 時載入所有子模組（spacy/nltk/konlpy/sentence_transformers），在 frozen exe 環境觸發 C-level crash
2. **修復方式**：用 importlib 在 sys.modules 預註冊空 package，繞過 __init__.py 全量匯入，直接載入需要的 markdown.py 和 character.py
3. **統一 DATA_DIR**：dev 和 frozen 都使用 `%APPDATA%\AI-Memory-Vault\`，消除設定不同步問題
4. **清理舊資料**：刪除 AI_Engine/ 下的舊 config.json、vault_meta.json、chroma_db、record_manager_cache.sql、根目錄 debug txt、多餘 .venv、.pytest_cache
5. **重建索引**：用正確的 paraphrase-multilingual-MiniLM-L12-v2 模型重建 751 chunks