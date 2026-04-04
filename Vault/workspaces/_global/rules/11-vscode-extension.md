---
type: rule
domain: coding
category: vscode-extension
workspace: _global
applies_to: [typescript, nodejs, vscode-api, webpack]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, typescript, vscode, extension, architecture]
ai_summary: "VS Code Extension 開發規範：多專案架構（shared 共用庫）、TypeScript 編碼風格（注意：不用 m_/i 前綴）、webpack 建置、activate/deactivate 生命週期、指令註冊模式。"
---

# VS Code Extension 開發

> ⚠️ Extension 的命名風格與遊戲端（C#/Lua）**不同**！不使用 `m_`、`i` 前綴。

---

## 多專案架構

```
vscode-extensions-shared/          ← 共用工具庫
vscode-extensions-synapse/
vscode-extensions-workpilot/
vscode-extensions-continuous-learning/
```

> 更新 shared 後，**必須檢查所有依賴專案是否需同步更新**

---

## TypeScript 命名規範

| 類型 | 格式 | 範例 |
|------|------|------|
| 類別 | PascalCase | `ChatSessionParser` |
| 介面 | `I` 前綴 | `IChatSession` |
| 函式 | camelCase | `validateCompanyNetwork()` |
| 變數 | camelCase | `buildMode` |
| 常數 | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| 私有成員 | `_` 前綴 | `private _isInitialized` |
| 參數 | camelCase（**不加 `i`**） | `context`, `token` |

```typescript
// ✅ 正確
export class ChatHistoryExporter {
    private _outputChannel: vscode.OutputChannel;
    public async exportHistory(sessionId: string): Promise<void> {}
}

// ❌ 不要在 Extension 中使用遊戲端風格
export class ChatHistoryExporter {
    private m_OutputChannel: vscode.OutputChannel;
    public async exportHistory(iSessionId: string) {}
}
```

---

## Extension 生命週期

```typescript
export async function activate(context: vscode.ExtensionContext) {
    const service = new MyService(context);
    context.subscriptions.push(
        vscode.commands.registerCommand('extension.myCommand', () => {
            service.execute();
        })
    );
}

export function deactivate() {}
```

### 關鍵規則

- ✅ 所有 Disposable 推入 `context.subscriptions`
- ✅ 耗時操作用 `vscode.window.withProgress`
- ✅ 錯誤用 `vscode.window.showErrorMessage`
- ❌ 不在全域作用域做初始化

---

## ✅ 快速檢查清單

- [ ] 所有 Disposable 推入 `context.subscriptions`
- [ ] 使用 TypeScript 命名風格（不是 C#/Lua 風格）
- [ ] webpack externals 包含 `vscode`
- [ ] 更新 shared 後檢查依賴專案
