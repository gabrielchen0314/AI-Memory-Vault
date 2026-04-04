---
type: rule
domain: networking
category: protocol-implementation
workspace: _global
applies_to: [lua, xlua, networking]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, protocol, networking, lua, client-server]
ai_summary: "Client↔Server 協定 Lua 實作規範：SendProtocol 補 0 編號、ProtocolMgr 不補 0、資料型別對照、封包讀寫順序必須一致。"
---

# Protocol 協定實作

---

## 核心概念

| 方向 | 檔案命名 | 說明 |
|------|----------|------|
| Client → Server | `SendProtocol_XXX.lua` | 發送協定（打包封包） |
| Server → Client | `Protocol_XXX.lua` | 接收協定（解析封包） |

---

## 📌 編號規則

| 元素 | SendProtocol | ProtocolMgr |
|------|:------------:|:-----------:|
| 檔案/模組 | **補 0**：`SendProtocol_030` | **補 0**：`Protocol_030` |
| 函式主編號 | **補 0**：`SendProtocol_030` | **不補 0**：`ProtocolMgr[30]` |
| 函式子編號 | **補 0**：`._001` | **不補 0**：`[1]` |

```lua
-- ✅ SendProtocol：全部補 0
SendProtocol_030 = {}
function SendProtocol_030._001(iShopType)
end

-- ✅ ProtocolMgr：主/子編號不補 0
ProtocolMgr[30] = {}
ProtocolMgr[30][1] = function(iPacket)
end
```

---

## 📊 資料型別速查

| 標記 | Write API | Read API | 範圍 |
|:----:|-----------|----------|------|
| (1) | `WriteByte()` | `ReadByte()` | 0 ~ 255 |
| (2) | `WriteUInt16()` | `ReadUInt16()` | 0 ~ 65,535 |
| (4) | `WriteUInt32()` | `ReadUInt32()` | 0 ~ 4,294,967,295 |
| (8) | `WriteUInt64()` | `ReadUInt64()` | 0 ~ 18,446,744,073,709,551,615 |
| (?) | `WriteString()` | `ReadString()` | 動態長度 |

---

## ⚡ 關鍵規則

1. **讀寫順序必須一致** — SendProtocol 寫入順序 = ProtocolMgr 讀取順序
2. **重複區塊用 for 迴圈** — `<<...>>` 標記的區塊
3. **Kind 分支用 if-elseif-else** — 必須有 else 處理未知 Kind
4. **SendProtocol 必須加 D.Log** — 每個 Send 函式

---

## 協定註解格式

```
---[主編號-子編號]描述 + 欄位說明(型別大小) + <<重複區塊>>
```

| 符號 | 意義 |
|------|------|
| `(1)` ~ `(8)` | 位元組大小 |
| `(?)` | 動態字串 |
| `<<...>>` | 重複區塊，用 `for` 迴圈 |
| `Kind(1)` | 條件分支，用 `if-elseif-else` |

---

## ✅ 快速檢查清單

### SendProtocol
- [ ] 函式/子編號**補 0**：`SendProtocol_030._001`
- [ ] 寫入順序與協定文件一致
- [ ] 每個函式都有 `D.Log`

### ProtocolMgr
- [ ] 函式/子編號**不補 0**：`ProtocolMgr[30][1]`
- [ ] 讀取順序與協定文件一致
- [ ] `<<>>` 重複區塊用 `for i = 1, _Count do`
- [ ] Kind 條件用 `if-elseif-else`（含 else）
