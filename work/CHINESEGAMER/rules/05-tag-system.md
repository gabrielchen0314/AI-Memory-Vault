---
type: rule
domain: system
category: tag-system
workspace: CHINESEGAMER
applies_to: [lua, xlua, unity, game-system]
severity: must
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, tag, bit-array, lua, game-system, filtering]
source: RD-指示-Tag 系統開發指南.instructions.md
ai_summary: "Tag 系統開發規範：索引陣列與 Bit Array 雙表示、E{Category}Tag 枚舉（必須有 None=0 和 Max）、TagUtils API、Data.New() 結尾預處理轉換。"
---

# Tag 系統開發 — CHINESE GAMER

> 📋 **完整 Golden Example**：`.copilot/skills/tag-system/SKILL.md`

---

## 核心概念

| 概念 | 說明 | 使用時機 |
|------|------|----------|
| **索引陣列** | 存儲 Tag 索引，如 `{1, 3, 5}` | 串檔讀取、資料儲存 |
| **Bit Array** | 位元運算存儲，高效比對 | 執行期篩選、匹配 |
| **預處理** | 索引陣列 → Bit Array | `Data.New()` 結尾 |

```
串檔資料 → 索引陣列（m_CharacterTags）→ 預處理 → Bit Array（m_Tag_Characters）
                 ↑ 儲存用                              ↑ 執行期查詢用
```

---

## 📋 Tag 枚舉規範

### 命名規則

```lua
-- ✅ 命名：E{Category}Tag
EElementTag = { ... }
ERaceTag = { ... }
ECharacterTag = { ... }
ESkillTag = { ... }
```

### 枚舉格式

```lua
-- ✅ 正確格式：必須有 None = 0 和 Max
EElementTag = {
    None  = 0,       -- 必須有 None = 0
    Fire  = 1,
    Water = 2,
    Wind  = 3,
    Earth = 4,
    Light = 5,
    Dark  = 6,
    Max   = 64       -- 必須有 Max（用於 Bit Array 長度計算）
}
```

```lua
-- ❌ 缺少 None 或 Max
EElementTag = {
    Fire  = 1,       -- 缺少 None = 0
    Water = 2,
    -- 缺少 Max
}
```

---

## 🏷️ 欄位命名規範

| 類型 | 命名模式 | 範例 |
|------|---------|------|
| 索引陣列（原始資料） | `m_{Category}Tags` | `m_CharacterTags` |
| Bit Array（預處理後） | `m_Tag_{Category}` | `m_Tag_Characters` |

```lua
-- ✅ 正確的欄位命名
---@field m_CharacterTags table<number> 角色Tag索引陣列
---@field m_Tag_Characters table Bit Array（預處理）

-- ❌ 命名混淆
---@field m_CharacterBits table       -- 看不出是 Bit Array
---@field m_TagArray table            -- 看不出是哪個 Category
```

---

## 🔄 預處理（Data.New 結尾）

在 `Data.New()` 函式的**結尾**進行索引陣列到 Bit Array 的轉換：

```lua
function CharacterData.New(iReader)
    local _Data = {}

    -- ... 讀取其他欄位 ...

    -- 讀取索引陣列
    _Data.m_CharacterTags = {}
    local _TagCount = iReader:ReadByte()
    for _i = 1, _TagCount do
        table.insert(_Data.m_CharacterTags, iReader:ReadByte())
    end

    -- ✅ 預處理：索引陣列 → Bit Array（放在 New 結尾）
    _Data.m_Tag_Characters = TagUtils.IndexArrayToBitArray(
        _Data.m_CharacterTags,
        ECharacterTag.Max
    )

    return _Data
end
```

```lua
-- ❌ 在執行期才轉換（每次查詢都轉，效能差）
function this.HasTag(iData, iTagIndex)
    local _BitArray = TagUtils.IndexArrayToBitArray(iData.m_CharacterTags, ECharacterTag.Max)
    return TagUtils.HasIndex(_BitArray, iTagIndex)
end
```

---

## 🔧 TagUtils API 速查

```lua
local TagUtils = require("Logic/Utils/TagUtils")
```

### 轉換

```lua
-- 索引陣列 → Bit Array
local _BitArray = TagUtils.IndexArrayToBitArray(iIndexArray, iLength)

-- Bit Array → 索引陣列
local _IndexArray = TagUtils.BitArrayToIndexArray(iBitArray, iMax)
```

### 檢查

```lua
-- 單一索引：是否有某個 Tag
local _Has = TagUtils.HasIndex(iBitArray, iIndex)

-- 任一索引：是否有任何一個 Tag
local _HasAny = TagUtils.HasAnyIndex(iBitArray, iIndexArray)

-- 所有索引：是否有全部 Tag
local _HasAll = TagUtils.HasAllIndex(iBitArray, iIndexArray)

-- 交集：兩個 Bit Array 是否有交集
local _HasIntersection = TagUtils.HasIntersection(iBitArray1, iBitArray2)
```

### 建立

```lua
-- 空的 Bit Array
local _Empty = TagUtils.CreateEmptyBitArray(iLength)

-- 從索引陣列建立
local _BitArray = TagUtils.CreateBitArrayFromIndexArray(iArray, iLength)
```

---

## 📖 完整使用範例

### 篩選角色

```lua
---篩選符合條件的角色
---@param iRequiredTags table<number> 需求的 Tag 索引陣列
---@return table<CharacterData> 符合條件的角色列表
function this.FilterCharactersByTags(iRequiredTags)
    local _RequiredBits = TagUtils.CreateBitArrayFromIndexArray(
        iRequiredTags,
        ECharacterTag.Max
    )

    local _Result = {}
    local _AllCharacters = CharacterDataMgr.GetAll()

    for _, _CharData in ipairs(_AllCharacters) do
        -- 使用預處理好的 Bit Array 比對
        if TagUtils.HasIntersection(_CharData.m_Tag_Characters, _RequiredBits) then
            table.insert(_Result, _CharData)
        end
    end

    return _Result
end
```

### 技能目標篩選

```lua
---檢查目標是否符合技能的 Tag 條件
---@param iSkillData SkillData 技能資料
---@param iTargetData CharacterData 目標資料
---@return boolean
function this.IsValidTarget(iSkillData, iTargetData)
    -- 技能沒有 Tag 限制 → 所有目標都合法
    if not iSkillData.m_Tag_Targets or #iSkillData.m_TargetTags == 0 then
        return true
    end

    -- 用 Bit Array 交集檢查
    return TagUtils.HasIntersection(
        iTargetData.m_Tag_Characters,
        iSkillData.m_Tag_Targets
    )
end
```

---

## ⚡ 效能建議

| 資料量 | 建議 |
|--------|------|
| < 100 筆 | 可直接遍歷索引陣列 |
| 100 ~ 500 筆 | 建議用 Bit Array |
| > 500 筆 | **必須**用 Bit Array |

---

## 📁 相關檔案

| 檔案 | 說明 |
|------|------|
| `GEnums.lua` | Tag 枚舉定義（EElementTag 等） |
| `TagUtils.lua` | 工具模組（轉換 + 查詢 API） |
| `GFunction.lua` | `SetBitInArray` 等底層位元操作 |

---

## ✅ 快速檢查清單

- [ ] 枚舉命名 `E{Category}Tag`
- [ ] 枚舉必須有 `None = 0` 和 `Max`
- [ ] 索引陣列欄位：`m_{Category}Tags`
- [ ] Bit Array 欄位：`m_Tag_{Category}`
- [ ] 預處理放在 `Data.New()` 結尾
- [ ] 執行期查詢使用 Bit Array，**不**在執行期轉換
- [ ] 使用 `TagUtils` API，**不**自己寫位元操作
- [ ] 篩選結果用 `table.insert` 收集

---

## 例外情況

- 少量一次性查詢可直接用索引陣列，不需預處理
- 動態新增/移除 Tag 時需重新建立 Bit Array
- 跨模組共享 Tag 時，枚舉放在 `GEnums.lua` 統一管理
