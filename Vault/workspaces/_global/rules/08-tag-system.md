---
type: rule
domain: system
category: tag-system
workspace: _global
applies_to: [lua, xlua, unity, game-system]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, tag, bit-array, lua, game-system, filtering]
ai_summary: "Tag 系統開發規範：索引陣列與 Bit Array 雙表示、E{Category}Tag 枚舉（必須有 None=0 和 Max）、TagUtils API、Data.New() 結尾預處理轉換。"
---

# Tag 系統開發

---

## 核心概念

| 概念 | 說明 | 使用時機 |
|------|------|----------|
| **索引陣列** | 存儲 Tag 索引，如 `{1, 3, 5}` | 串檔讀取、資料儲存 |
| **Bit Array** | 位元運算存儲，高效比對 | 執行期篩選、匹配 |
| **預處理** | 索引陣列 → Bit Array | `Data.New()` 結尾 |

---

## Tag 枚舉規範

```lua
-- ✅ 命名：E{Category}Tag，必須有 None = 0 和 Max
EElementTag = {
    None  = 0,
    Fire  = 1,
    Water = 2,
    Wind  = 3,
    Max   = 64
}
```

---

## 欄位命名規範

| 類型 | 命名模式 | 範例 |
|------|---------|------|
| 索引陣列（原始資料） | `m_{Category}Tags` | `m_CharacterTags` |
| Bit Array（預處理後） | `m_Tag_{Category}` | `m_Tag_Characters` |

---

## 預處理（Data.New 結尾）

```lua
function CharacterData.New(iReader)
    local _Data = {}
    -- 讀取索引陣列
    _Data.m_CharacterTags = {}
    local _TagCount = iReader:ReadByte()
    for _i = 1, _TagCount do
        table.insert(_Data.m_CharacterTags, iReader:ReadByte())
    end
    -- ✅ 預處理放在 New 結尾
    _Data.m_Tag_Characters = TagUtils.IndexArrayToBitArray(
        _Data.m_CharacterTags, ECharacterTag.Max
    )
    return _Data
end
```

---

## TagUtils API 速查

```lua
-- 轉換
TagUtils.IndexArrayToBitArray(iIndexArray, iLength)
TagUtils.BitArrayToIndexArray(iBitArray, iMax)

-- 檢查
TagUtils.HasIndex(iBitArray, iIndex)
TagUtils.HasAnyIndex(iBitArray, iIndexArray)
TagUtils.HasAllIndex(iBitArray, iIndexArray)
TagUtils.HasIntersection(iBitArray1, iBitArray2)
```

---

## ✅ 快速檢查清單

- [ ] 枚舉命名 `E{Category}Tag`
- [ ] 枚舉必須有 `None = 0` 和 `Max`
- [ ] 索引陣列欄位：`m_{Category}Tags`
- [ ] Bit Array 欄位：`m_Tag_{Category}`
- [ ] 預處理放在 `Data.New()` 結尾
- [ ] 執行期查詢使用 Bit Array，不在執行期轉換
