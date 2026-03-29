---
type: rule
domain: workflow
category: git-conventions
workspace: CHINESEGAMER
applies_to: [git, all-languages]
severity: must
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, git, commit, version-control, workflow]
source: RD-指示-Git Commit 快速參考.instructions.md, RD-Agent-Git 提交流程專家.agent.md
ai_summary: "Git 提交規範：feat/fix/refactor 等前綴、原子性 commit、路徑分類（04.LuaScript → 串檔/管理器/UI）、提交前檢查清單、commit message 完整範例。"
---

# Git 提交規範 — CHINESE GAMER

> 🤖 **對應 Agent**：`@GitCommitter`

---

## 📋 Commit Type 分類

| 前綴 | 用途 | 範例 |
|------|------|------|
| `feat:` | 新功能 | `feat: 新增 RewardPicker 獎勵選擇系統` |
| `fix:` | Bug 修正 | `fix: 修正 GameOver 技能殘留問題` |
| `refactor:` | 重構 | `refactor: 重構 Tag 系統使用 Bit Array` |
| `docs:` | 文件更新 | `docs: 新增 TagSystem 指示檔` |
| `style:` | 格式調整 | `style: 統一 Debug Log 格式` |
| `chore:` | 雜項維護 | `chore: 更新 Addressable 設定` |
| `test:` | 測試相關 | `test: 新增 TagUtils 單元測試` |
| `perf:` | 效能優化 | `perf: 優化 Bit Array 查詢效率` |
| `ci:` | CI/CD | `ci: 更新 Jenkins 建置腳本` |

---

## 📝 Commit Message 格式

### 基本格式

```
<type>: <簡短描述>

[詳細說明]
- 項目 1
- 項目 2

[相關檔案]（可選）
- path/to/file1.lua
```

### ✅ 良好的 Commit Message

```
feat: 新增 Tag 系統與 RewardPicker 獎勵選擇

[Tag 系統]
- 新增 EElementTag, ERaceTag, ESkillTag 列舉
- SkillData/CharacterData 支援 Bit Array 預處理
- 新增 TagUtils 工具模組

[RewardPicker 系統]
- 新增 RewardPickerMgr 管理器
- 新增 RewardPicker_Controller UI 控制器

[修正]
- 修正 GameOver 技能殘留問題
```

```
fix: 修正商城購買協定金幣類型錯誤

- Protocol_030 中 Gold 欄位應使用 ReadUInt64 而非 ReadUInt32
- 同步修正 SendProtocol_030._002 的 WriteUInt64
- 影響範圍：商城購買、背包出售
```

### ❌ 差勁的 Commit Message

```
update code
fix bug
done
WIP
asdf
```

---

## 📁 檔案路徑分類

AI 在撰寫 commit message 時，依據檔案路徑自動分類：

| 路徑模式 | 分類 | 說明 |
|---------|------|------|
| `04.LuaScript/Data/` | 串檔相關 | Data 讀取模組 |
| `04.LuaScript/Logic/Mgr/` | 管理器 | 邏輯管理模組 |
| `04.LuaScript/UI/` | UI 控制器 | UI 相關模組 |
| `04.LuaScript/Logic/Role/` | 角色相關 | 角色系統 |
| `04.LuaScript/Logic/Utils/` | 工具模組 | 共用工具 |
| `.github/instructions/` | 指示檔 | AI 規範文件 |
| `.copilot/skills/` | 技能檔 | AI 技能文件 |
| `Assets/Editor/` | 編輯器工具 | Editor 擴充 |
| `Assets/Scripts/` | C# 腳本 | C# 邏輯 |

---

## 🔄 工作流程

```
1️⃣ 分析變更 (git status --porcelain)
   ↓
2️⃣ 分類檔案（依路徑模式）
   ↓
3️⃣ 撰寫 Commit Message
   ↓
4️⃣ 執行 Commit & Push
   ↓
5️⃣ 回報結果
```

### 分析指令

```bash
# 查看變更狀態
git status --porcelain

# 查看最近一次 commit
git log --oneline -1

# 查看詳細差異
git diff --stat
```

### 分析重點

| 狀態碼 | 說明 |
|:------:|------|
| `??` | 新增檔案（untracked） |
| `M` | 修改檔案 |
| `D` | 刪除檔案 |
| `R` | 重命名檔案 |
| `A` | 已 staged 的新檔案 |

---

## 📊 回報格式

```
✅ Git 提交完成

📝 Commit: abc1234
📁 變更: 12 files changed, +345 -67
🚀 Push: Success

[變更摘要]
- feat: 新增 RewardPicker 獎勵選擇系統
- fix: 修正 GameOver 技能殘留問題
```

---

## ⚡ 最佳實踐

| 原則 | 說明 |
|------|------|
| **原子性** | 一個 commit 做一件事，不混合多個不相關的變更 |
| **可追溯** | commit message 說明「為什麼」改，而非只說「改了什麼」 |
| **可回溯** | 每個 commit 應該是可獨立 revert 的 |
| **不拆太細** | 相關聯的變更放同一個 commit，不需要一個檔案一個 commit |

### ✅ 正確的拆分

```
Commit 1: feat: 新增 TagUtils 工具模組
Commit 2: feat: CharacterData 支援 Tag Bit Array
Commit 3: feat: 新增角色篩選 UI
```

### ❌ 不當的拆分

```
Commit 1: add file TagUtils.lua          ← 太細
Commit 2: add function HasIndex           ← 太細
Commit 3: add function HasAnyIndex        ← 太細
```

---

## 🔍 提交前檢查清單

- [ ] `git status` 確認所有變更都已 staged
- [ ] 沒有遺漏新增的檔案（`??` 狀態）
- [ ] 沒有不應該提交的檔案（如 `.meta` 衝突、暫存檔）
- [ ] Commit message 符合 `<type>: <描述>` 格式
- [ ] 重要變更都有在 message 中列出
- [ ] Commit message 使用繁體中文描述
- [ ] 可以回答「這個 commit 為什麼存在？」

---

## 🔗 與其他 Agent 協作

```
@Planner → 規劃任務
    ↓
@TddGuide → 撰寫測試（可選）
    ↓
實作功能
    ↓
@CodeReviewer → 審查程式碼
    ↓
@SecurityReviewer → 安全審查（如涉及敏感功能）
    ↓
@GitCommitter → 提交程式碼 ← 你在這裡！
```

---

## 例外情況

- **WIP commit**：長期功能開發中可使用 `WIP:` 前綴，但合併前必須 squash 或重寫 message
- **merge commit**：使用 Git 預設的 merge message 即可
- **hotfix**：緊急修正可簡化 message，但事後應補充說明
- **指示檔/文件**：純文件更新可使用簡短描述（如 `docs: 更新 Tag 系統指示檔`）
