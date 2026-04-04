---
type: rule
domain: workflow
category: git-conventions
workspace: _global
applies_to: [git, all-languages]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, git, commit, version-control, workflow]
ai_summary: "Git 提交規範：feat/fix/refactor 等前綴、原子性 commit、路徑分類（04.LuaScript → 串檔/管理器/UI）、提交前檢查清單、commit message 完整範例。"
---

# Git 提交規範

---

## Commit Type 分類

| 前綴 | 用途 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | Bug 修正 |
| `refactor:` | 重構 |
| `docs:` | 文件更新 |
| `style:` | 格式調整 |
| `chore:` | 雜項維護 |
| `test:` | 測試相關 |
| `perf:` | 效能優化 |
| `ci:` | CI/CD |

---

## Commit Message 格式

```
<type>: <簡短描述>

[詳細說明]
- 項目 1
- 項目 2
```

### ✅ 良好範例

```
feat: 新增 Tag 系統與 RewardPicker 獎勵選擇

[Tag 系統]
- 新增 EElementTag, ERaceTag, ESkillTag 列舉
- SkillData/CharacterData 支援 Bit Array 預處理
```

### ❌ 差勁範例

```
update code
fix bug
done
```

---

## 路徑分類

| 路徑模式 | 分類 |
|---------|------|
| `04.LuaScript/Data/` | 串檔相關 |
| `04.LuaScript/Logic/Mgr/` | 管理器 |
| `04.LuaScript/UI/` | UI 控制器 |
| `04.LuaScript/Logic/Utils/` | 工具模組 |
| `Assets/Scripts/` | C# 腳本 |

---

## 最佳實踐

| 原則 | 說明 |
|------|------|
| **原子性** | 一個 commit 做一件事 |
| **可追溯** | 說明「為什麼」改 |
| **可回溯** | 每個 commit 可獨立 revert |

---

## ✅ 提交前檢查清單

- [ ] `git status` 確認所有變更都已 staged
- [ ] 沒有遺漏新增的檔案
- [ ] Commit message 符合 `<type>: <描述>` 格式
- [ ] Commit message 使用繁體中文描述
