---
type: rule
domain: security
category: obfuscation-validation
workspace: CHINESEGAMER
applies_to: [typescript, webpack, vscode-api]
severity: must
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, security, obfuscation, webpack, vscode, extension]
source: RD-指示-VSCode Extension 混淆與驗證.instructions.md
ai_summary: "VS Code Extension 混淆與公司網路驗證：webpack-obfuscator 設定、雙版本打包（公司版/家用版）、authService 整合、build.bat 流程。"
---

# Extension 混淆與驗證 — CHINESE GAMER

> 🔐 **安全原則**：「安全是提高破解成本，不是絕對防禦」
> 📋 **完整指南**：`RD-指示-VSCode Extension 混淆與驗證.instructions.md`

---

## 核心概念

| 目的 | 手段 |
|------|------|
| 防止程式碼被輕易閱讀 | webpack-obfuscator 混淆 |
| 限制使用環境 | 公司網路驗證（HEAD → Redmine） |
| 雙版本支援 | 公司版（驗證）+ 家用版（不驗證） |

### 安全等級評估

| 項目 | 防護等級 | 說明 |
|------|:--------:|------|
| 程式碼可讀性 | ⭐⭐⭐ | 混淆後難以直接閱讀 |
| 逆向工程 | ⭐⭐ | AI 輔助下可能被理解 |
| 環境限制 | ⭐⭐⭐ | 需修改原始碼才能繞過 |
| **整體** | **提高破解成本 4-8 小時** | 對「順手帶走」有效 |

---

## 📦 雙版本打包

| 版本 | 檔名格式 | 驗證 | 使用場景 |
|------|---------|:----:|---------|
| 公司版 | `{name}-x.x.x.vsix` | ✅ | 公司內網 |
| 家用版 | `{name}-home-x.x.x.vsix` | ❌ | 家用環境 |

### 環境變數

| 變數 | 值 | 效果 |
|------|-----|------|
| `BUILD_MODE` | `company` | 啟用驗證 |
| `BUILD_MODE` | `home` | 跳過驗證 |
| `NODE_ENV` | `production` | 啟用混淆 |

---

## 🔒 驗證整合

```typescript
// ✅ 在 extension.ts 的 activate 中加入
import { requiresValidation, validateCompanyNetwork, showValidationFailedMessage } from 'vscode-extensions-shared';

export async function activate(context: vscode.ExtensionContext) {
    if (requiresValidation()) {
        const isValid = await validateCompanyNetwork();
        if (!isValid) {
            showValidationFailedMessage(vscode);  // ⚠️ 需傳入 vscode 模組
            return;
        }
    }
    // ... 正常啟動
}
```

### 驗證邏輯

```
HEAD https://cgredmine.chinesegamer.net/
├── 任何回應（200, 302, 403） → ✅ 可達（公司網路）
└── 連線逾時 / 網路錯誤       → ❌ 不可達（非公司網路）
```

---

## 🔧 混淆設定

```javascript
// webpack.config.js — 生產環境加入混淆
if (isProduction) {
    config.plugins.push(
        new WebpackObfuscator(getObfuscatorConfig({
            reservedNames: ['^vscode', '^activate', '^deactivate']
        }), [])
    );
}
```

### 混淆選項建議

| 選項 | 開啟 | 效能影響 |
|------|:----:|---------|
| `stringArray` | ✅ | 低 |
| `stringArrayEncoding` | ✅ | 低 |
| `deadCodeInjection` | ✅ | 中 |
| `controlFlowFlattening` | ✅ | 中 |
| `identifierNamesGenerator` | ✅ | 無 |
| `selfDefending` | ❌ | **高（不建議）** |

---

## 📋 build.bat 使用

```batch
build.bat company   # 打包公司版
build.bat home      # 打包家用版
build.bat all       # 打包兩個版本
```

> ⚠️ **重點**：用 `SET` 設定環境變數而非 `cross-env`，因為 `vsce package` 的 `prepublish` 會再跑一次 webpack，`SET` 的變數會被子進程繼承。

---

## 🚀 套用到新專案

1. 加入 shared 依賴 → `npm install`
2. 建立 `webpack.config.js`（引用 shared 設定）
3. 更新 `extension.ts`（加入驗證）
4. 更新 `package.json` scripts
5. 複製 `build.bat`
6. 測試兩個版本

---

## ✅ 快速檢查清單

- [ ] `webpack.config.js` 有引用 shared 的混淆設定
- [ ] `extension.ts` 的 `activate` 有驗證邏輯
- [ ] `showValidationFailedMessage` 有傳入 `vscode` 模組
- [ ] `reservedNames` 包含 `^vscode`, `^activate`, `^deactivate`
- [ ] `build.bat` 支援 company / home / all
- [ ] 家用版 VSIX 有 `-home-` 後綴
- [ ] 沒有開啟 `selfDefending`

---

## 例外情況

- 純內部工具（不會外流）可簡化只做公司版
- 開發階段不做混淆（`npm run build` 用 development mode）
- shared 本身不需要混淆（被其他專案打包時才混淆）
