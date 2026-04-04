---
type: rule
domain: workflow
category: multi-project-git
workspace: _global
applies_to: [git, typescript, vscode-api]
severity: should
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, git, multi-project, vscode, extension, workflow]
ai_summary: "VS Code Extensions 多專案 Git 管理：4 個專案的狀態檢查、批次操作（git-all.bat）、跨專案依賴更新順序、scope 格式的 commit message。"
---

# 多專案 Git 管理

---

## 依賴順序（更新 shared 時）

```
1️⃣ vscode-extensions-shared          ← 先提交
   ↓
2️⃣ 各依賴專案 npm install
   ↓
3️⃣ 各依賴專案個別 commit & push
```

---

## 批次操作工具

```batch
git-all.bat pull      # 拉取所有專案
git-all.bat status    # 檢查所有專案狀態
git-all.bat push      # 推送所有專案
```

### 手動批次指令

```bash
# 檢查所有專案狀態
for /d %d in (vscode-extensions-*) do @echo === %d === && cd %d && git status -s && cd ..
```

---

## Commit Message 格式（Extension 專用）

與一般規則（rule 10）的差異：加上 `(scope)`

```
<type>(<scope>): <描述>
```

範例：
```
feat(auth): 新增公司網路驗證服務
fix(webpack): 修正環境變數繼承問題
chore(deps): 更新 webpack-obfuscator 到 3.5.1
```

---

## ⚠️ 注意事項

1. **shared 優先**：永遠先提交 shared，再提交依賴它的專案
2. **npm install**：更新 shared 後，依賴專案要跑 `npm install`
3. **獨立提交**：每個專案獨立 commit

---

## ✅ 快速檢查清單

- [ ] shared 有變更時，先提交 shared
- [ ] 依賴專案有跑 `npm install`
- [ ] 每個專案的 commit message 都有 scope
- [ ] 最後用 `git-all.bat status` 確認全部乾淨
