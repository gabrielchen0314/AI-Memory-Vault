---
type: project-status
project: ai-memory-vault
org: LIFEOFDEVELOPMENT
last_updated: 2026.04.10
---

# 專案狀態 — ai-memory-vault

## 工作脈絡

v3.6 已完成所有核心功能（39 MCP 工具、Agent/Skill/Instinct 三大系統、7 個工具模組）。
目前進入穩定化 + 打包期：Skills 知識包已建立首批（3個），detail 參數已驗證正常。

### 最近完成的重大項目
- Phase 22: Agent Router + 10 個 Agent 模板 + Instinct 系統
- Phase 21: server.py 拆分為 7 個 tool 模組 + SchedulerService lifespan 單例
- Skills 目錄建立（workspaces/_global/skills/）+ 首批 3 個 Skill 知識包
- Roadmap 更新至 v3.6（39 工具完整清單）
- `log_ai_conversation` detail 參數驗證（Optional[dict] 正確）

## 待辦事項

### 進行中

- [ ] PyInstaller rebuild（打包至 v3.6.0）

### 待處理

- [ ] 安裝包版本號更新（v3.5.0 → v3.6.0）
- [ ] 更多 Skill 知識包建立（e.g. CSharpCodingStyle_Skill, LuaCodingStyle_Skill）
- [ ] detail 參數實際呼叫測試（重啟 MCP 後呼叫 log_ai_conversation 傳入 detail 確認）

### 已完成

- [x] Roadmap.md 更新至 v3.6（完整 39 工具清單）
- [x] server.py 版本號更新至 3.6 + log 修正
- [x] Skills 目錄 + 首批 Skill 知識包建立
- [x] Agent 系統（10 個 Agent 模板）驗證正常
- [x] API Map 規則整備（02 修正 + 15 新增）
- [x] `log_ai_conversation` 強化（detail 參數）
- [x] 收工 SOP 更新（6步→5步）
- [x] MCP 工具繁體中文化
- [x] VS Code prompts 架構重構
- [x] 排程器任務名稱 bug 修正
- [x] 安裝包 v3.5.0 重建

## 重要決策

| 決策 | 原因 | 日期 |
|------|------|------|
| vault-bridge.instructions.md 為唯一橋接入口 | 避免多個 .instructions.md 重複注入 | 2026-04-08 |
| agents.md + nav.md 設 inject:true | MCP 連線時自動注入，不需手動讀取 | 2026-04-08 |
| 程式碼專案判斷改為通用（不列舉副檔名） | 列表永遠不完整 | 2026-04-09 |
| 專案側 API Map 為主、Vault 存索引 | AI 直接讀取、git 同步 | 2026-04-09 |
| log_ai_conversation 合併摘要+詳細 | 一次呼叫完成，減少收工步驟 | 2026-04-09 |
| Skills 放於 workspaces/_global/skills/ | 全組織共用、list_skills 直接掃描 | 2026-04-10 |
| index.md 從 list_skills 結果排除（未來） | index.md 不是 Skill 本體，需過濾 | 2026-04-10 |
