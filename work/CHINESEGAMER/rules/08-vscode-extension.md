---
type: rule
domain: coding
category: vscode-extension
workspace: CHINESEGAMER
applies_to: [typescript, nodejs, vscode-api, webpack]
severity: must
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, typescript, vscode, extension, architecture]
source: RD-Agent-系統架構設計專家.agent.md (vscode-extension-architecture), RD-指示-Editor Tool 開發指南.instructions.md
ai_summary: "VS Code Extension 開發規範：多專案架構（shared 共用庫）、TypeScript 編碼風格、webpack 建置、activate/deactivate 生命週期、指令註冊模式。"
---

# VS Code Extension 開發 — CHINESE GAMER

> 📋 **完整指南**：`.copilot/skills/vscode-extension-architecture/SKILL.md`
> 🏢 **適用專案**：WorkPilot、Synapse、Continuous Learning、Shared Library

---

## 📐 多專案架構

```
E:\WorkSpace\
├── vscode-extensions-shared/          ← 共用工具庫（被其他專案依賴）
│   ├── src/auth/authService.ts        ← 驗證邏輯
│   └── webpack/obfuscatorConfig.js    ← 混淆設定
│
├── vscode-extensions-synapse/         ← AI 對話同步
├── vscode-extensions-workpilot/       ← 工作管理擴充
└── vscode-extensions-continuous-learning/ ← 持續學習擴充
```

### 依賴關係

```
vscode-extensions-shared
    ↓ (被依賴)
├── vscode-extensions-synapse
├── vscode-extensions-workpilot
└── vscode-extensions-continuous-learning
```

> ⚠️ **更新 shared 後，必須檢查所有依賴專案是否需同步更新**

### 引用 shared

```json
// package.json
{
  "dependencies": {
    "vscode-extensions-shared": "file:../../vscode-extensions-shared"
  }
}
```

---

## 🏷️ TypeScript 命名規範

| 類型 | 格式 | 範例 |
|------|------|------|
| 類別 | PascalCase | `ChatSessionParser` |
| 介面 | `I` 前綴 + PascalCase | `IChatSession` |
| 型別 | PascalCase | `BuildMode` |
| 列舉 | PascalCase（成員也是） | `EventType.FileChanged` |
| 函式 | camelCase | `validateCompanyNetwork()` |
| 變數 | camelCase | `buildMode` |
| 常數 | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| 私有成員 | `_` 前綴 | `private _isInitialized` |
| 參數 | camelCase（不加 `i`） | `context`, `token` |

```typescript
// ✅ VS Code Extension 命名風格
export class ChatHistoryExporter {
    private _outputChannel: vscode.OutputChannel;
    private _isExporting: boolean = false;
    
    constructor(private readonly _context: vscode.ExtensionContext) {}
    
    public async exportHistory(sessionId: string): Promise<void> {}
}
```

```typescript
// ❌ 不要在 Extension 中使用遊戲端的 i 前綴、m_ 前綴
export class ChatHistoryExporter {
    private m_OutputChannel: vscode.OutputChannel;  // 錯
    public async exportHistory(iSessionId: string) {}  // 錯
}
```

> ⚠️ **注意**：Extension 的命名風格與遊戲端（C#/Lua）不同！不使用 `m_`、`i` 前綴。

---

## 🏗️ Extension 生命週期

```typescript
// ✅ 標準的 activate / deactivate
import * as vscode from 'vscode';

export async function activate(context: vscode.ExtensionContext) {
    // 1. 驗證（如需要）
    // 2. 初始化服務
    // 3. 註冊指令
    // 4. 註冊事件
    
    const service = new MyService(context);
    
    context.subscriptions.push(
        vscode.commands.registerCommand('extension.myCommand', () => {
            service.execute();
        })
    );
}

export function deactivate() {
    // 清理資源
}
```

### 關鍵規則

- ✅ 所有 Disposable 都要推入 `context.subscriptions`
- ✅ 耗時操作要用 `vscode.window.withProgress` 顯示進度
- ✅ 錯誤用 `vscode.window.showErrorMessage` 回報
- ❌ 不要在全域作用域做初始化

---

## 📦 webpack 建置

### package.json scripts

```json
{
  "scripts": {
    "vscode:prepublish": "npm run build:prod",
    "build": "webpack --mode development",
    "build:prod": "cross-env NODE_ENV=production webpack --mode production",
    "build:company": "cross-env BUILD_MODE=company NODE_ENV=production webpack --mode production",
    "build:home": "cross-env BUILD_MODE=home NODE_ENV=production webpack --mode production"
  }
}
```

### webpack externals

```javascript
externals: {
    vscode: 'commonjs vscode',
    ws: 'commonjs ws'    // 有 native bindings 的模組要外部化
}
```

---

## ✅ 快速檢查清單

- [ ] 所有 Disposable 推入 `context.subscriptions`
- [ ] 使用 TypeScript 命名風格（不是 C#/Lua 風格）
- [ ] activate 中先驗證再初始化
- [ ] 錯誤有 `showErrorMessage` 回報
- [ ] webpack externals 包含 `vscode`
- [ ] 更新 shared 後檢查依賴專案

---

## 例外情況

- Extension 的命名風格不遵循遊戲端 C#/Lua 規範，使用標準 TypeScript 慣例
- 測試檔案可不做混淆
- 家用版可跳過公司驗證
