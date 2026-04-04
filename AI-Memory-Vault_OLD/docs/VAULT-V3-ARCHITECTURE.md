---
type: architecture
domain: vault-next
created: 2026.04.01
last_updated: 2026.04.01
ai_summary: "AI Memory Vault v3 — 完整重構方案：雙模式執行檔（UI + MCP）、技術棧評估、Vault 結構優化"
tags: [architecture, v3, refactor, proposal]
---

# AI Memory Vault v3 — 架構重構方案

> **目標**：從「開發者工具」進化為「獨立產品」—— 有 UI、有執行檔、有初始化流程，任何人都能使用。

---

## 一、技術棧評估

### 1.1 語言選型比較

| 語言 | 執行檔打包 | UI 框架 | Python 生態整合 | MCP SDK | 學習成本 | 綜合評分 |
|------|-----------|---------|----------------|---------|---------|---------|
| **Python** | PyInstaller/Nuitka | Tauri (WebView) / PySide6 | ✅ 原生 | ✅ mcp[cli] | 零（現有） | ⭐⭐⭐⭐ |
| **TypeScript** | Electron / Tauri | React / Vue | ❌ 需重寫核心 | ✅ @modelcontextprotocol/sdk | 中 | ⭐⭐⭐ |
| **Rust** | 原生 .exe | Tauri (原生後端) | ❌ 需重寫核心 | 🔶 社群 SDK | 高 | ⭐⭐ |
| **Go** | 原生 .exe | Wails (WebView) | ❌ 需重寫核心 | 🔶 社群 SDK | 中 | ⭐⭐ |
| **.NET (C#)** | 原生 .exe | MAUI / Avalonia | ❌ 需重寫核心 | 🔶 Copilot SDK | 中 | ⭐⭐⭐ |

### 1.2 推薦方案：Python 後端 + Tauri 殼層

```
┌──────────────────────────────────────────────────┐
│                   Tauri Shell                     │
│  ┌──────────────────────────────────────────────┐ │
│  │           Web UI (React / Vue)               │ │
│  │     聊天介面 ─ 設定頁 ─ 筆記管理 ─ 搜尋      │ │
│  └──────────────────────────────────────────────┘ │
│                     ↕ HTTP / IPC                  │
│  ┌──────────────────────────────────────────────┐ │
│  │          Python Backend (FastAPI)            │ │
│  │  VaultService ─ Retriever ─ Indexer ─ LLM   │ │
│  └──────────────────────────────────────────────┘ │
│                     ↕ stdio                       │
│  ┌──────────────────────────────────────────────┐ │
│  │            MCP Server (FastMCP)              │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

**為什麼選這個組合：**

| 優勢 | 說明 |
|------|------|
| **零重寫成本** | Python 核心（VaultService, Retriever, Indexer）100% 保留 |
| **執行檔體積小** | Tauri 產出 ~10MB（vs Electron ~150MB） |
| **跨平台** | Windows / macOS / Linux 一次打包 |
| **MCP 原生支援** | Python mcp[cli] 已驗證，直接復用 |
| **GitHub Copilot SDK** | Python SDK 已在 Technical Preview，可直接整合 |

### 1.3 替代方案：純 Python（快速出 MVP）

如果先求速度，不需要精美 UI：

```
Python + Textual (TUI)  →  終端內精美 UI，可打包為單一 .exe
Python + Gradio         →  Web 聊天介面，一行程式碼啟動
Python + NiceGUI        →  桌面級 Web UI，支援打包
```

| 方案 | 打包方式 | UI 品質 | 開發速度 |
|------|---------|---------|---------|
| Textual (TUI) | PyInstaller → .exe | 終端美化 | ⚡ 最快 |
| Gradio | PyInstaller → .exe | Web 聊天風 | ⚡ 很快 |
| NiceGUI | PyInstaller → .exe | 桌面 Web | ⚡ 快 |
| **Tauri + React** | Tauri CLI → .msi | **原生桌面** | 🔧 中等 |

---

## 二、新架構設計

### 2.1 專案結構

```
AI-Memory-Vault/
├── app/                        → 桌面應用（Tauri Shell）
│   ├── src/                    → Web UI（React + TypeScript）
│   │   ├── pages/
│   │   │   ├── Chat.tsx        → 聊天主介面
│   │   │   ├── Notes.tsx       → 筆記管理（瀏覽/編輯）
│   │   │   ├── Search.tsx      → 搜尋介面
│   │   │   └── Settings.tsx    → 設定頁（LLM/Vault路徑/使用者資訊）
│   │   ├── components/
│   │   └── App.tsx
│   ├── src-tauri/              → Tauri 後端（Rust，薄殼）
│   └── package.json
│
├── engine/                     → Python 核心引擎（原 AI_Engine 重構）
│   ├── core/                   → 核心模組
│   │   ├── embeddings.py       → 嵌入模型
│   │   ├── vectorstore.py      → 向量資料庫
│   │   ├── indexer.py          → 文件索引
│   │   ├── retriever.py        → 混合搜尋
│   │   └── llm.py              → LLM 工廠（整合 Copilot SDK）
│   ├── services/
│   │   ├── vault.py            → VaultService（核心 Facade）
│   │   ├── setup.py            → 初始化引導服務 ⭐ 新增
│   │   └── chat.py             → 聊天服務
│   ├── mcp/
│   │   ├── server.py           → MCP Server（獨立進程）
│   │   └── tools.py            → MCP 工具定義
│   ├── api/
│   │   ├── app.py              → FastAPI 應用
│   │   └── routes.py           → REST 路由
│   ├── config.py               → 設定管理
│   ├── main.py                 → 入口點
│   └── requirements.txt
│
├── vault/                      → 知識庫（使用者資料）
│   └── （見第四節 Vault 結構）
│
├── scripts/                    → 工具腳本
├── docs/                       → 專案文件
└── README.md
```

### 2.2 雙模式運行

```
                ┌─────────────────────┐
                │    main.py          │
                │  ┌───────────────┐  │
                │  │  setup.py     │  │  ← 首次執行時自動觸發
                │  │  初始化引導    │  │
                │  └───────┬───────┘  │
                │          │          │
                │    ┌─────┴─────┐    │
                │    │           │    │
                │  --mode ui   --mode mcp
                │    │           │    │
                │    ▼           ▼    │
                │  FastAPI    FastMCP  │
                │  + Tauri    stdio    │
                └─────────────────────┘
```

**模式一：UI 模式** (`--mode ui`)
- 啟動 FastAPI 後端
- 開啟 Tauri/瀏覽器視窗
- 提供完整聊天、搜尋、筆記管理介面

**模式二：MCP 模式** (`--mode mcp`)
- 啟動 FastMCP stdio server
- 供 VS Code / Claude Desktop / Cursor 等編輯器使用
- 與現有功能 100% 相容

### 2.3 初始化引導流程 ⭐

```
啟動 main.py
    │
    ▼
┌─ 檢查 config.json ─┐
│   存在？            │
│   ├── Yes → 載入    │
│   └── No  ──────────┼──→ 進入初始化引導
│                     │
│   ┌─────────────────▼─────────────────┐
│   │        Setup Wizard               │
│   │                                   │
│   │  Step 1: 選擇 Vault 路徑          │
│   │    □ 使用預設 (~/AI-Memory-Vault)  │
│   │    □ 自訂路徑                      │
│   │                                   │
│   │  Step 2: 使用者資訊               │
│   │    ▸ 名稱 (author)               │
│   │    ▸ 組織/公司名稱（可選）        │
│   │    ▸ Email（可選）                │
│   │                                   │
│   │  Step 3: LLM 設定                │
│   │    □ GitHub Copilot (推薦)        │
│   │    □ Google Gemini                │
│   │    □ Ollama (本地)                │
│   │                                   │
│   │  Step 4: 建立 Vault 結構          │
│   │    → 自動產生目錄 + 核心檔案       │
│   │    → 索引初始檔案                  │
│   └───────────────────────────────────┘
│                     │
│                     ▼
│             config.json 寫入
│                     │
└─────────────────────┘
          │
          ▼
    正常啟動（UI / MCP）
```

**config.json 結構：**

```json
{
    "version": "3.0",
    "vault_path": "D:/AI-Memory-Vault/vault",
    "user": {
        "name": "gabrielchen",
        "organization": "LIFEOFDEVELOPMENT",
        "email": ""
    },
    "llm": {
        "provider": "copilot",
        "model": "gpt-4o",
        "api_key_env": "GITHUB_TOKEN"
    },
    "embedding": {
        "model": "paraphrase-multilingual-MiniLM-L12-v2",
        "device": "cpu"
    },
    "search": {
        "top_k": 5,
        "bm25_weight": 0.4,
        "vector_weight": 0.6
    }
}
```

---

## 三、GitHub Copilot 整合方案

### 3.1 三種整合路徑

```
方案 A：Copilot SDK（推薦）
┌─────────────────────────────────────────┐
│  你的 App （UI / CLI）                   │
│     │                                   │
│     ▼                                   │
│  Copilot SDK (Python)                   │
│     ├── GitHub OAuth 認證               │
│     ├── 自動選擇最佳模型                 │
│     └── MCP Client → 你的 MCP Server    │
│            │                            │
│            ▼                            │
│     VaultService (搜尋/讀取/寫入)        │
└─────────────────────────────────────────┘

方案 B：Copilot CLI + MCP
┌─────────────────────────────────────────┐
│  gh copilot chat                        │
│     └── --mcp-config vault-mcp.yml      │
│            │                            │
│            ▼                            │
│     你的 MCP Server (stdio)              │
│            │                            │
│            ▼                            │
│     VaultService                        │
└─────────────────────────────────────────┘

方案 C：自建 LLM + 你的 MCP Server
┌─────────────────────────────────────────┐
│  你的 App                                │
│     │                                   │
│     ▼                                   │
│  LLM API (Gemini / GPT-4o / Ollama)    │
│     │                                   │
│     ▼                                   │
│  Tool-call Loop                         │
│     └── 呼叫 VaultService 工具           │
└─────────────────────────────────────────┘
```

### 3.2 engine/core/llm.py 架構

```python
class LLMProvider( ABC ):
    """LLM 提供者抽象介面"""
    def chat( self, messages, tools ) -> Response: ...
    def stream( self, messages, tools ) -> Iterator: ...

class CopilotProvider( LLMProvider ):
    """GitHub Copilot SDK 整合"""
    # 使用 GitHub OAuth + Copilot SDK
    # 最接近 VS Code Copilot Chat 體驗

class GeminiProvider( LLMProvider ):
    """Google Gemini API"""

class OllamaProvider( LLMProvider ):
    """本地 Ollama"""
```

---

## 四、Vault 結構優化

### 4.1 問題分析（現有結構）

```
work/
├── _shared/          → 「共用」概念模糊：跨公司？跨專案？
├── CHINESEGAMER/     → 公司名當頂層，但子目錄太多層
│   ├── rules/        → 10 條規則全放一起（遊戲 + Extension 混雜）
│   ├── projects/
│   ├── meetings/
│   ├── people/
│   └── working-context/
└── LIFEOFDEVELOPMENT/
```

**主要問題：**
1. `_shared` 與 `rules` 重疊 — 共用編碼規範應該在哪？
2. `rules/` 內混雜不同技術棧的規則
3. `working-context/` 概念不清 — 是暫存？是筆記？
4. 新使用者不知道該建什麼目錄

### 4.2 新 Vault 結構

```
vault/
├── .config/                    → ⭐ 系統設定（取代 _system 中的 AI 專用部分）
│   ├── nav.md                  → 導航地圖
│   ├── handoff.md              → Session 交接
│   ├── todos.md                → 待辦事項
│   └── agents.md               → 架構文件（供 AI 理解）
│
├── workspaces/                 → ⭐ 工作空間（取代 work/）
│   │
│   ├── _global/                → 全域共用（取代 _shared，語意更明確）
│   │   ├── index.md
│   │   ├── snippets/           → 程式碼片段（依語言分）
│   │   │   ├── csharp/
│   │   │   ├── lua/
│   │   │   ├── typescript/
│   │   │   └── python/
│   │   └── tech-notes/         → 技術筆記（取代 tech-stack，更通用）
│   │
│   └── {workspace-name}/       → 每個工作空間（公司/組織/個人專案群）
│       ├── index.md            → 工作空間入口
│       ├── standards/          → ⭐ 編碼與流程規範（取代 rules/，語意更清晰）
│       │   ├── index.md
│       │   ├── coding/         → 程式碼規範
│       │   │   ├── csharp.md
│       │   │   ├── lua.md
│       │   │   └── python.md
│       │   ├── workflow/       → 工作流程規範
│       │   │   ├── git.md
│       │   │   └── review.md
│       │   └── security/       → 安全規範
│       │       └── game.md
│       ├── projects/           → 專案
│       │   └── {project-name}/
│       │       ├── overview.md
│       │       ├── progress.md
│       │       └── api-map.md
│       ├── meetings/           → 會議紀錄
│       └── notes/              → ⭐ 工作筆記（取代 working-context，更直覺）
│
├── personal/                   → ⭐ 個人空間（取代 life/，更通用）
│   ├── index.md
│   ├── journal/                → 日記
│   ├── learning/               → 學習筆記
│   ├── goals/                  → 目標管理
│   └── ideas/                  → 靈感收集
│
├── knowledge/                  → 永久知識卡片（保持不變）
│   └── index.md
│
├── templates/                  → 模板系統（保持不變）
│   ├── index.md
│   ├── agents/
│   ├── projects/
│   └── sections/
│
└── attachments/                → 附件
```

### 4.3 重點改動說明

| 舊結構 | 新結構 | 為什麼 |
|--------|--------|--------|
| `_system/` | `.config/` | 更標準的命名，所有工具都認識 |
| `work/` | `workspaces/` | 語意更明確 — 這是「工作空間」 |
| `work/_shared/` | `workspaces/_global/` | 「全域」比「共用」更精準 |
| `rules/` | `standards/coding/` + `standards/workflow/` | 按類型分類，不再混雜 |
| `working-context/` | `notes/` | 簡潔直覺，降低認知負擔 |
| `life/` | `personal/` | 更中性，不限於「生活」，也可放學習 |
| `tech-stack/` | `tech-notes/` | 更通用，不只是技術棧 |

### 4.4 範例：使用者 gabrielchen 的 Vault

```
vault/
├── .config/
├── workspaces/
│   ├── _global/
│   │   ├── snippets/
│   │   └── tech-notes/
│   │
│   ├── chinesegamer/                    → 上班的公司
│   │   ├── standards/
│   │   │   ├── coding/
│   │   │   │   ├── csharp.md            → C# 編碼規範
│   │   │   │   └── lua.md               → Lua 編碼規範
│   │   │   ├── workflow/
│   │   │   │   ├── git.md               → Git 規範
│   │   │   │   └── protocol.md          → 封包實作規範
│   │   │   └── security/
│   │   │       └── game.md              → 遊戲安全規範
│   │   ├── projects/
│   │   │   └── spin-with-friends/
│   │   ├── meetings/
│   │   └── notes/
│   │
│   └── lifeofdevelopment/               → 自己的公司
│       ├── standards/
│       │   └── coding/
│       │       └── python.md
│       └── projects/
│           └── ai-memory-vault/
│
├── personal/
│   ├── journal/
│   ├── learning/
│   └── goals/
│
├── knowledge/
└── templates/
```

---

## 五、功能保留清單

### 5.1 必須保留（核心功能）

| 功能 | 現有模組 | 新位置 |
|------|---------|--------|
| 混合搜尋（BM25 + 向量） | `core/retriever.py` | `engine/core/retriever.py` |
| 增量索引 | `core/indexer.py` | `engine/core/indexer.py` |
| Markdown + Frontmatter 解析 | `core/indexer.py` | `engine/core/indexer.py` |
| 多語言嵌入模型 | `core/embeddings.py` | `engine/core/embeddings.py` |
| ChromaDB 向量庫 | `core/vectorstore.py` | `engine/core/vectorstore.py` |
| VaultService Facade | `services/vault_service.py` | `engine/services/vault.py` |
| MCP Server（5 個工具） | `mcp_server.py` | `engine/mcp/server.py` |
| 路徑安全防護 | `VaultService` | `engine/services/vault.py` |
| Recency Bias 排序 | `core/retriever.py` | `engine/core/retriever.py` |

### 5.2 強化功能

| 功能 | 說明 |
|------|------|
| **初始化引導** ⭐ | 首次執行自動建立 Vault + 設定 |
| **UI 聊天介面** ⭐ | 類似 Copilot Chat 的聊天體驗（獨立桌面） |
| **GitHub Copilot SDK 整合** ⭐ | 使用 Copilot 作為 LLM 後端 |
| **設定檔 GUI** | 在 UI 中管理 LLM/Vault/使用者設定 |
| **筆記瀏覽器** | 在 UI 中直接瀏覽/編輯筆記 |

### 5.3 移除/簡化

| 功能 | 原因 |
|------|------|
| Discord Channel | 低使用率，可作為外掛 |
| LINE Channel | 低使用率，可作為外掛 |
| WorkspaceSetupService | 被新的 Setup Wizard 取代 |
| InteractiveRepl | 被 UI 取代（或保留為 --mode cli） |

---

## 六、開發路線圖

### Phase 1：核心重構（1-2 週）

```
[ ] engine/ 目錄重構（從 AI_Engine 搬移 + 清理）
[ ] config.json 取代 .env（保留 .env 相容）
[ ] Setup Wizard（CLI 版本先行）
[ ] Vault 新結構 scaffold 腳本
[ ] MCP Server 驗證（確保向後相容）
```

### Phase 2：UI 原型（2-3 週）

```
[ ] Tauri 專案初始化
[ ] 聊天頁面（基礎對話 + 流式輸出）
[ ] 搜尋頁面（即時搜尋 + 結果預覽）
[ ] 設定頁面（LLM / Vault / User）
[ ] FastAPI ↔ Tauri IPC 整合
```

### Phase 3：Copilot 整合（1-2 週）

```
[ ] GitHub Copilot SDK 整合
[ ] OAuth 流程（GitHub 登入）
[ ] Tool-call loop（讓 Copilot 呼叫 Vault 工具）
[ ] 模型選擇（Copilot / Gemini / Ollama 切換）
```

### Phase 4：打包發布（1 週）

```
[ ] Tauri 打包 → .msi (Windows) / .dmg (macOS)
[ ] 自動更新機制
[ ] 安裝引導（首次啟動 = Setup Wizard）
[ ] README + 使用文件
```

---

## 七、技術決策記錄 (ADR)

### ADR-001：為何保留 Python 而非全部重寫

**結論**：保留 Python 核心，僅 UI 層使用 TypeScript。

- LangChain + ChromaDB + sentence-transformers 生態系在 Python 最成熟
- MCP 官方 SDK (mcp[cli]) 以 Python 為主
- 重寫成本 >> 整合成本
- Tauri 的 sidecar 機制可以完美包裝 Python 後端

### ADR-002：為何選 Tauri 而非 Electron

**結論**：Tauri。

- 打包體積 ~10MB vs ~150MB
- 記憶體佔用 ~30MB vs ~200MB
- Tauri v2 支援 sidecar（內嵌 Python 執行檔）
- 前端自由（React / Vue / Svelte）

### ADR-003：為何 Vault 結構用 `workspaces/` 取代 `work/`

**結論**：`workspaces/` 更通用。

- `work/` 暗示「工作」，但使用者也可能放個人專案
- IDE 概念中 workspace 是獨立工作環境的標準術語
- `_global/` 比 `_shared/` 更精準表達「跨所有 workspace」

### ADR-004：為何 `standards/` 取代 `rules/`

**結論**：`standards/` + 子分類。

- `rules/` 太扁平，10 條規則混在一起
- `standards/coding/` + `standards/workflow/` + `standards/security/` 按職責分類
- 新使用者立刻知道規範該放哪個子目錄
