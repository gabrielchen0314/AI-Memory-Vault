## 對話摘要

本次工作延續上次 Session 的待辦事項：清理 build.spec、確認套件降版、驗證 frozen exe。

主要成果：
1. **build.spec 清理**：移除 torch/sentence_transformers/langchain_huggingface 相關的 collect_all、hidden imports，新增 excludes 清單。exe 從 790 MB 降至 395 MB（減半）。
2. **發現並修復 _bootstrap bug**：scheduler 進入點（`_start_scheduler_task/once/daemon`）未呼叫 `_bootstrap()` 初始化 vectorstore，monthly-ai 在 frozen exe 中失敗。修正後三處均加入 `_bootstrap(_Config)`。
3. **套件降版確認安全**：transformers 4.57.6 / huggingface_hub 0.36.2，OnnxEmbeddings dim=384 正常。
4. **全面驗證通過**：247 tests、frozen exe --help/--list-tasks/weekly-ai/monthly-ai 全成功。