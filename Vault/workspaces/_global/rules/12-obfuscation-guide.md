---
type: rule
domain: security
category: obfuscation-validation
workspace: _global
applies_to: [typescript, webpack, vscode-api]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, security, obfuscation, webpack, vscode, extension]
ai_summary: "VS Code Extension 混淆與公司網路驗證：webpack-obfuscator 設定、雙版本打包（公司版/家用版）、authService 整合、build.bat 流程。"
---

# Extension 混淆與驗證

> 🔐 安全原則：「安全是提高破解成本，不是絕對防禦」

---

## 雙版本打包

| 版本 | 檔名格式 | 驗證 |
|------|---------|:----:|
| 公司版 | `{name}-x.x.x.vsix` | ✅ |
| 家用版 | `{name}-home-x.x.x.vsix` | ❌ |

---

## 驗證整合

```typescript
export async function activate(context: vscode.ExtensionContext) {
    if (requiresValidation()) {
        const isValid = await validateCompanyNetwork();
        if (!isValid) {
            showValidationFailedMessage(vscode);
            return;
        }
    }
}
```

```
HEAD https://cgredmine.chinesegamer.net/
├── 任何回應 → ✅ 公司網路
└── 連線逾時 → ❌ 非公司網路
```

---

## 混淆選項建議

| 選項 | 開啟 | 效能影響 |
|------|:----:|---------|
| `stringArray` | ✅ | 低 |
| `deadCodeInjection` | ✅ | 中 |
| `controlFlowFlattening` | ✅ | 中 |
| `selfDefending` | ❌ | **高（不建議）** |

---

## build.bat 使用

```batch
build.bat company   # 打包公司版
build.bat home      # 打包家用版
build.bat all       # 打包兩個版本
```

---

## ✅ 快速檢查清單

- [ ] `activate` 有驗證邏輯
- [ ] `showValidationFailedMessage` 有傳入 `vscode` 模組
- [ ] `reservedNames` 包含 `^vscode`, `^activate`, `^deactivate`
- [ ] 家用版 VSIX 有 `-home-` 後綴
- [ ] 沒有開啟 `selfDefending`
