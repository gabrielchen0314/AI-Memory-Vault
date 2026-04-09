---
type: rule
domain: workflow
category: documentation
workspace: _global
applies_to: [all-projects]
severity: must
created: 2026.03.29
last_updated: 2026.04.09
ai_summary: "程式專案必須在專案原始碼建立 API Map（主要存放位置），Vault 僅存索引連結。適用所有語言、所有組織。"
tags: [rule, workflow, documentation, api-map, global]
---

# 02 — 專案 API Map 同步規則（全域）

> 本規範適用於**所有組織、所有語言**的程式碼專案。
> 原始來源：`workspaces/LIFEOFDEVELOPMENT/rules/03-project-api-map-sync.md`（2026.04.04 升級為全域規則）
> 撰寫模板與格式指南：`workspaces/_global/rules/15-api-map-writing-guide.md`

---

## 核心原則

**專案側為主、Vault 存索引。**

- API Map 的**主要存放位置**是專案原始碼目錄（跟著程式碼走、AI 可直接讀取）
- Vault 只存「哪些模組有 API Map」的**索引連結**，不複製完整內容

```
               新建/修改模組
                    │
                    ▼
          ┌─────────────────┐
          │ 專案原始碼目錄    │
          │ 建立/更新        │
          │ API Map（主要）   │  ← 跟著 git 版控走
          └────────┬────────┘
                   │
              觸發同步
                   │
          ┌────────▼────────┐
          │ Vault 更新索引    │
          │ status.md 或      │
          │ module-catalog.md │  ← 只存「哪裡有 API Map」
          └─────────────────┘
```

---

## 判斷「程式碼專案」

專案中包含**任何程式語言原始碼**即判定為程式碼專案，不限定特定語言。

| 判定 | 說明 |
|------|------|
| ✅ 程式碼專案 | 包含原始碼檔案（`.py` `.cs` `.lua` `.ts` `.js` `.go` `.rs` `.java` `.rb` `.cpp` `.swift` 等任何程式語言） |
| ❌ 非程式碼專案 | 純文件 / Vault 筆記 / 設定檔 / 純資源 |

> **原則**：只要專案有可被 AI 理解的程式碼模組，就需要 API Map。不需要逐一列舉副檔名。

---

## API Map 放置位置

### 專案側（主要）

| 情境 | 專案側路徑 | 說明 |
|------|-----------|------|
| 模組級（推薦） | `{ModulePath}/APIMap/{ModuleName}_APIMap.md` | 靠近原始碼，AI 容易發現 |
| 專案有 `docs/` | `{PROJECT_ROOT}/docs/api-maps/{Module}_APIMap.md` | 集中管理 |
| 小型專案 | `{PROJECT_ROOT}/docs/API_MAP.md` 或 `{PROJECT_ROOT}/API_MAP.md` | 單檔彙整 |

### Vault 側（索引）

在 `workspaces/{ORG}/projects/{PROJECT}/status.md` 或 `module-catalog.md` 中記錄：

```markdown
## API Map 索引

| 模組 | 專案路徑 | 最後更新 |
|------|---------|---------|
| ColliderMgr | `Assets/.../ColliderMgr/APIMap/ColliderMgr_APIMap.md` | 2026.04.09 |
| UIMgr | `Assets/.../UIMgr/APIMap/UIMgr_APIMap.md` | 2026.04.09 |
```

---

## API Map 內容格式

完整模板與撰寫指南請參照：`workspaces/_global/rules/15-api-map-writing-guide.md`

精簡格式（適用於專案級彙整）：

```markdown
# API Map — {ProjectName}

## 模組總覽

| 模組 | 職責 | 入口檔案 | 對外方法數 |
|------|------|---------|-----------| 

## 各模組詳細 API

### {ModuleName}
| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
```

---

## 同步觸發時機

| 觸發事件 | 專案側（主要） | Vault 側（索引） |
|----------|--------------|----------------|
| 新建專案 | 建立 API_MAP.md 骨架 | 建立索引連結 |
| 新增/修改模組公開 API | 更新對應 API Map | 更新索引時間戳 |
| 重構模組 | 更新或重建 API Map | 更新 architecture.md |
| 刪除模組 | 刪除對應 API Map | 移除索引項目 |

---

## ⚠️ 注意事項

1. API Map 是**工作手冊**，內容應精簡（方法簽章 + 一句話說明），不是原始碼複製
2. 專案側的 API Map 建議**納入 Git 版控**（跟著程式碼走）
3. 若專案原始碼不在本機（遠端 repo），則只在 Vault 側建立完整版，並標註「專案側待同步」
4. AI 修改公開 API 簽章時，應**主動提醒**更新 API Map
