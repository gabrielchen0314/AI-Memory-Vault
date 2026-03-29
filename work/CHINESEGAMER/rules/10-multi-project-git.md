---
type: rule
domain: workflow
category: multi-project-git
workspace: CHINESEGAMER
applies_to: [git, typescript, vscode-api]
severity: should
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, git, multi-project, vscode, extension, workflow]
source: RD-指示-多專案 Git 管理.instructions.md
ai_summary: "VS Code Extensions 多專案 Git 管理：4 個專案的狀態檢查、批次操作（git-all.bat）、跨專案依賴更新順序、scope 格式的 commit message。"
---

# 多專案 Git 管理 — CHINESE GAMER

> 📦 VS Code Extensions 專案群的 Git 狀態檢查、Commit 和 Push

---

## 📋 適用專案

| 專案 | 說明 | 依賴 shared |
|------|------|:----------:|
| `vscode-extensions-shared` | 共用工具庫 | — |
| `vscode-extensions-synapse` | AI 對話同步 | ✅ |
| `vscode-extensions-workpilot` | 工作管理擴充 | ✅ |
| `vscode-extensions-continuous-learning` | 持續學習擴充 | ✅ |

### 依賴順序（更新 shared 時）

```
1️⃣ vscode-extensions-shared          ← 先提交
   ↓
2️⃣ 各依賴專案執行 npm install        ← 同步依賴
   ↓
3️⃣ 各依賴專案個別 commit & push      ← 再提交
```

---

## 🔧 批次操作工具

### git-all.bat

```batch
# 檔案位置
E:\WorkSpace\git-all.bat

# 使用方式
git-all.bat pull      # 拉取所有專案
git-all.bat status    # 檢查所有專案狀態
git-all.bat push      # 推送所有專案
git-all.bat fetch     # Fetch 所有專案
```

### 手動批次指令

```bash
# 檢查所有專案狀態
cd e:\WorkSpace
for /d %d in (vscode-extensions-*) do @echo === %d === && cd %d && git status -s && cd ..

# 全部 Pull
for /d %d in (vscode-extensions-*) do @echo === %d === && cd %d && git pull && cd ..

# 全部 Push
for /d %d in (vscode-extensions-*) do @echo === %d === && cd %d && git push && cd ..
```

---

## 📝 Commit Message 格式（Extension 專用）

### 與遊戲端的差異

| 項目 | 遊戲端（Rule 07） | Extension |
|------|:------------------:|:---------:|
| 格式 | `<type>: <描述>` | `<type>(<scope>): <描述>` |
| scope | 不使用 | 使用模組名 |
| 語言 | 繁體中文 | 繁體中文 |

### 格式

```
<type>(<scope>): <描述>

[optional body]
```

### 範例

```
feat(auth): 新增公司網路驗證服務
fix(webpack): 修正環境變數繼承問題
chore(deps): 更新 webpack-obfuscator 到 3.5.1
refactor(parser): 重構 ChatSession 解析邏輯
docs: 更新 README 使用說明
```

---

## 🔄 標準工作流程

### 單一專案變更

```
1️⃣ git status                      ← 確認變更
2️⃣ 分析變更（新功能/修復/重構）
3️⃣ git add .
4️⃣ git commit -m "type(scope): 描述"
5️⃣ git push
```

### 跨專案變更（涉及 shared）

```
1️⃣ 先 commit & push shared
2️⃣ 各專案 npm install（更新 shared 依賴）
3️⃣ 各專案個別 commit & push
4️⃣ 用 git-all.bat status 確認全部乾淨
```

---

## ⚠️ 注意事項

1. **shared 優先**：永遠先提交 shared，再提交依賴它的專案
2. **npm install**：更新 shared 後，依賴專案要跑 `npm install` 才能取得最新版
3. **獨立提交**：每個專案獨立 commit，不要跨專案合併
4. **狀態確認**：提交前用 `git-all.bat status` 確認沒有遺漏

---

## ✅ 快速檢查清單

- [ ] 確認所有專案都沒有未追蹤的重要檔案
- [ ] shared 有變更時，先提交 shared
- [ ] 依賴專案有跑 `npm install` 同步 shared
- [ ] 每個專案的 commit message 都有 scope
- [ ] 最後用 `git-all.bat status` 確認全部乾淨

---

## 例外情況

- 純文件更新（README、instructions）的 commit 可省略 scope
- 緊急 hotfix 可先 push 再補 shared 更新
- `git-all.bat` 如果在新環境使用，需確認 WorkSpace 路徑正確
