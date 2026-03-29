---
type: rule
domain: networking
category: protocol-implementation
workspace: CHINESEGAMER
applies_to: [lua, xlua, networking]
severity: must
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, protocol, networking, lua, client-server]
source: RD-指示-Protocol 協定實作.instructions.md
ai_summary: "Client↔Server 協定 Lua 實作規範：SendProtocol 補 0 編號、ProtocolMgr 不補 0、資料型別對照、封包讀寫順序必須一致。"
---

# Protocol 協定實作 — CHINESE GAMER

> 📋 **完整 Golden Example**：`.copilot/skills/protocol-implementation/SKILL.md`

---

## 核心概念

| 方向 | 檔案命名 | 說明 |
|------|----------|------|
| Client → Server | `SendProtocol_XXX.lua` | 發送協定（打包封包） |
| Server → Client | `Protocol_XXX.lua` | 接收協定（解析封包） |

---

## 📌 編號規則（最容易出錯）

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

```lua
-- ❌ SendProtocol 子編號沒補 0
function SendProtocol_030._1(iShopType)    -- 應該是 ._001

-- ❌ ProtocolMgr 主編號補了 0
ProtocolMgr[030] = {}                      -- 應該是 [30]
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

## 📤 SendProtocol 模板

```lua
SendProtocol_030 = {}

---[30-1]請求商品列表 + 商城類型(1)
---@param iShopType number 商城類型
function SendProtocol_030._001(iShopType)
    local _Packet = Network.Packet.GetTempPacket()
    _Packet:WriteByte(iShopType)
    D.Log("發送協定30-1  商城類型: " .. iShopType)
    NetworkMgr.Send(30, 1, _Packet)
end

---[30-2]購買商品 + 商品ID(4) + 數量(2)
---@param iItemId number 商品ID
---@param iCount number 購買數量
function SendProtocol_030._002(iItemId, iCount)
    local _Packet = Network.Packet.GetTempPacket()
    _Packet:WriteUInt32(iItemId)
    _Packet:WriteUInt16(iCount)
    D.Log("發送協定30-2  商品ID: " .. iItemId .. " 數量: " .. iCount)
    NetworkMgr.Send(30, 2, _Packet)
end
```

---

## 📥 ProtocolMgr 模板

```lua
ProtocolMgr[30] = {}

---[30-1]商品列表 + 數量(2) + <<商品ID(4) + 價格(4) + 名稱(?)>>
ProtocolMgr[30][1] = function(iPacket)
    local _Count = iPacket:ReadUInt16()

    local _List = {}
    for i = 1, _Count do
        _List[i] = {
            ItemId = iPacket:ReadUInt32(),
            Price  = iPacket:ReadUInt32(),
            Name   = iPacket:ReadString()
        }
    end

    Shop_Controller.UpdateList(_List)
end

---[30-2]購買結果 + 結果碼(1) + Kind(1) + <<根據 Kind>>
ProtocolMgr[30][2] = function(iPacket)
    local _Result = iPacket:ReadByte()
    local _Kind = iPacket:ReadByte()

    if _Kind == 1 then
        -- 成功
        local _ItemId = iPacket:ReadUInt32()
        local _Count = iPacket:ReadUInt16()
        Shop_Controller.OnPurchaseSuccess(_ItemId, _Count)
    elseif _Kind == 2 then
        -- 失敗：金幣不足
        Shop_Controller.OnPurchaseFailed("金幣不足")
    else
        D.LogWarning("未知的購買結果 Kind: " .. _Kind)
    end
end
```

---

## 📐 協定註解格式

```
---[主編號-子編號]描述 + 欄位說明(型別大小) + <<重複區塊>>
```

| 符號 | 意義 |
|------|------|
| `(1)` | 1 byte = WriteByte/ReadByte |
| `(2)` | 2 bytes = WriteUInt16/ReadUInt16 |
| `(4)` | 4 bytes = WriteUInt32/ReadUInt32 |
| `(8)` | 8 bytes = WriteUInt64/ReadUInt64 |
| `(?)` | 動態 = WriteString/ReadString |
| `<<...>>` | 重複區塊，用 `for` 迴圈 |
| `Kind(1)` | 條件分支，用 `if-elseif-else` |

---

## ⚡ 關鍵規則

### 1. 讀寫順序必須一致

```lua
-- ❌ 順序錯誤 = 資料錯亂（最危險的 bug）
-- SendProtocol 寫入：ItemId(4) + Count(2)
-- ProtocolMgr 讀取：Count(2) + ItemId(4)  ← 順序反了！
```

### 2. 重複區塊用 for 迴圈

```lua
-- 協定格式：數量(2) + <<商品ID(4) + 價格(4)>>
local _Count = iPacket:ReadUInt16()
for i = 1, _Count do
    _List[i] = {
        ItemId = iPacket:ReadUInt32(),
        Price  = iPacket:ReadUInt32()
    }
end
```

### 3. Kind 分支用 if-elseif-else

```lua
local _Kind = iPacket:ReadByte()
if _Kind == 1 then
    -- 處理 Kind 1
elseif _Kind == 2 then
    -- 處理 Kind 2
else
    D.LogWarning("未知 Kind: " .. _Kind)
end
```

### 4. SendProtocol 必須加 D.Log

```lua
-- ✅ 每個 Send 函式都要加 debug log
D.Log("發送協定30-1  商城類型: " .. iShopType)
NetworkMgr.Send(30, 1, _Packet)
```

---

## ✅ 快速檢查清單

### SendProtocol
- [ ] 函式/子編號**補 0**：`SendProtocol_030._001`
- [ ] 參數使用 `i` 前綴
- [ ] 寫入順序與協定文件一致
- [ ] 每個函式都有 `D.Log` 除錯
- [ ] 型別大小與標記一致（(4) → WriteUInt32）

### ProtocolMgr
- [ ] 函式/子編號**不補 0**：`ProtocolMgr[30][1]`
- [ ] 固定參數名 `iPacket`
- [ ] 讀取順序與協定文件一致
- [ ] `<< >>` 重複區塊用 `for i = 1, _Count do`
- [ ] Kind 條件用 `if-elseif-else`
- [ ] 有處理未知 Kind 的 else 分支

---

## 例外情況

- 超大封包（>1MB）需分批發送，協定設計時需預留分頁機制
- UINT64 在 Lua 中可能有精度問題，需注意 C# `long` 與 Lua `number` 的轉換
