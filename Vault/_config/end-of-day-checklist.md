---
type: system
created: 2026.04.04
last_updated: 2026.04.04
inject: true
---

# 🔚 收工檢查清單（End-of-Day Checklist）

> 每次工作結束時，AI 與使用者應依序完成以下項目。
> 所有文件路徑參照 `_config/nav.md` 的分層結構。

---

## 檢查項目

### 1. 專案每日進度（必須）
- **路徑**：`workspaces/{org}/projects/{project}/daily/YYYY-MM-DD.md`
- **內容**：今日完成、遇到的問題、明日計畫、學到的事
- 每個有實作的專案各寫一份

### 2. 對話紀錄（必須）
- **路徑**：`workspaces/{org}/projects/{project}/conversations/YYYY-MM-DD-{session}.md`
- **內容**：對話主題、關鍵決策、問題與解法、修改的檔案清單
- 一次對話一份，多次對話分開記錄

### 3. 每日總回顧（必須）
- **路徑**：`personal/reviews/daily/YYYY-MM-DD.md`
- **內容**：跨專案簡短總表 — 今日活躍專案、各專案重點一句話、明日接續
- 不需技術細節，看一眼就知道今天幹了什麼

### 4. 專案狀態更新（必須）
- **路徑**：`workspaces/{org}/projects/{project}/status.md`
- **內容**：工作脈絡更新 + 待辦事項(進行中/待處理/已完成) + 重要決策
- **每個有動過的專案各更新一份**（取代舊的全域 todos.md + handoff.md）

### 5. 交接索引更新（必須）
- **路徑**：`_config/handoff.md`
- **內容**：上次活躍專案清單（連結到各 status.md）+ 跨專案備註
- 只放「這次動了哪些專案」，細節放在各 status.md

### 6. 知識卡片（有學到新東西時）
- **路徑**：`knowledge/{topic-slug}.md`
- **內容**：核心知識、問題表現、解法、注意事項
- 扁平存放，靠 tags 分類，不用建子目錄
- 只記值得保留的概念，不記瑣碎操作步驟

### 7. 專案筆記 / 技術決策（有架構性變更時）
- **路徑**：`workspaces/{org}/projects/{project}/notes/{topic}.md`
- **內容**：決策背景、方案比較、最終選擇及原因

---

## 執行順序建議

```
1 → 專案日報（每個活躍專案）
2 → 對話紀錄
3 → 知識卡片（有東西才寫）
4 → 各活躍專案的 status.md 更新
5 → _config/handoff.md 索引更新
6 → 每日總回顧（最後寫，因為它是總表）
```

## 備註

- 所有寫入透過 `write_note` MCP 工具，自動索引至向量資料庫
- `status.md` = 舊 `todos.md` + 舊 `handoff.md` 合一，不再有全域 todos
- 此清單本身不需每次更新，除非流程有調整
