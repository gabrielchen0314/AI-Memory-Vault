# 交接索引

last_updated: 2026.04.11

## 上次活躍專案

| 專案 | 狀態 | 連結 |
|------|------|------|
| ai-memory-vault (LIFEOFDEVELOPMENT) | 活躍 | [status.md](workspaces/LIFEOFDEVELOPMENT/projects/ai-memory-vault/status.md) |

## 跨專案備註

- build.spec 清理完成：移除 torch/sentence_transformers/langchain_huggingface，exe 790→395 MB（2026-04-11 Session 4）
- 修復 scheduler 進入點 _bootstrap bug：monthly-ai frozen exe 失敗已修復
- 套件降版已確認安全：transformers 4.57.6 / huggingface_hub 0.36.2 無副作用
- frozen exe 完整驗證通過：weekly-ai + monthly-ai + --help + --list-tasks
- Instinct 新增：`entrypoint-needs-bootstrap`（信心 0.8）、`idempotent-hides-bugs`（信心 0.7）
- 下次工作優先：Docker 建置測試（需先安裝 Docker Desktop）/ `--setup-section data` CLI
