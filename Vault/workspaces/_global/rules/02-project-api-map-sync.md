---
type: rule
domain: workflow
category: documentation
workspace: _global
applies_to: [python, csharp, lua, typescript, all-projects]
severity: must
created: 2026.03.29
last_updated: 2026.04.04
ai_summary: "程式專案在 Vault 建立知識庫的同時，必須在專案原始碼資料夾建立 API Map，保持雙向同步。適用所有語言、所有組織。"
tags: [rule, workflow, documentation, api-map, global]
---

# 02 — 專案 API Map 同步規則（全域）

> 本規範適用於**所有組織、所有語言**的程式碼專案。  
> 原始來源：`workspaces/LIFEOFDEVELOPMENT/rules/03-project-api-map-sync.md`（2026.04.04 升級為全域規則）

---

## 核心規則

當 Agent（Architect / Doc Updater）為程式專案建立或更新 Vault 知識庫時：

1. **Vault 側**：在 `workspaces/{ORG}/projects/{PROJECT}/` 建立標準知識庫文件
2. **專案側**：在專案原始碼根目錄下建立 `docs/API_MAP.md`（或 `{Module}_APIMap.md`）

```
操作流程：

  建立/更新 Vault 知識庫
          │
          ▼
  ┌────────────────────────┐
  │ 專案是程式碼專案？       │
  ├── YES ─────────────────►──┐
  └── NO → 結束              │
                              ▼
                  ┌─────────────────────────┐
                  │ 在專案原始碼目錄建立      │
                  │ docs/API_MAP.md          │
                  │ ↕ 雙向同步 Vault 版本     │
                  └─────────────────────────┘
```

---

## 判斷「程式碼專案」

| 條件 | 判定 |
|------|------|
| 包含 `.py` / `.cs` / `.lua` / `.ts` / `.js` | ✅ 程式碼專案 |
| 純文件 / Vault 筆記 / 設定檔 | ❌ 非程式碼專案 |

---

## API Map 放置位置

| 情境 | 專案側路徑 | 說明 |
|------|-----------|------|
| 專案根目錄有 `docs/` | `{PROJECT_ROOT}/docs/API_MAP.md` | 優先 |
| 專案根目錄無 `docs/` | `{PROJECT_ROOT}/API_MAP.md` | 降級 |
| 模組級 API Map | `{PROJECT_ROOT}/docs/{Module}_APIMap.md` | 大型專案拆分 |

---

## API Map 內容格式

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

| 觸發事件 | Vault 側 | 專案側 |
|----------|---------|--------|
| 新建專案知識庫 | 建立 architecture.md / module-catalog.md | 建立 API_MAP.md |
| 新增/修改模組 | 更新 module-catalog.md | 更新 API_MAP.md 對應段落 |
| 重構模組 | 更新 architecture.md | 更新 API_MAP.md |

---

## ⚠️ 注意事項

1. API Map 是**工作手冊**，內容應精簡（方法簽章 + 一句話說明），不是原始碼複製
2. 專案側的 API Map 應加入 `.gitignore` 或是納入 Git 版控，由團隊決定
3. 若專案原始碼不在本機（遠端 repo），則只在 Vault 側建立，並在 Vault 文件中標註「專案側待同步」
