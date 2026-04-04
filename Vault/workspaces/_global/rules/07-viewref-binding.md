---
type: rule
domain: ui
category: viewref-binding
workspace: _global
applies_to: [lua, xlua, unity, ui]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, viewref, ui, unity, lua, binding]
ai_summary: "Unity Lua ViewRef UI 物件綁定規範：Component → Dictionary 映射、Button 特殊包裝（Button.New）、&前綴命名、RemoveAllListeners 清理。"
---

# ViewRef 物件綁定

---

## Component → Dictionary 映射表

| Component Type | Dictionary |
|:---------------|:-----------|
| RectTransform | `m_Dic_Trans` |
| Image | `m_Dic_Image` |
| RawImage | `m_Dic_RawImage` |
| Toggle | `m_Dic_Toggle` |
| Slider | `m_Dic_Slider` |
| TMPText / TextMeshProUGUI | `m_Dic_TMPText` |
| TMPInputField | `m_Dic_TMPInputField` |
| GroupButtonCtrl | `m_Dic_GroupButtonCtrl` |
| Dropdown | `m_Dic_Dropdown` |
| UIAnimation | `m_Dic_UIAnimation` |
| ButtonEx | `m_Dic_ButtonEx` |

---

## Button 特殊規則

名稱以 `&Button_` 開頭 → **必須**使用 `Button.New()` 包裝：

```lua
-- ✅ Button 必須用 Button.New 包裝
private.m_Button_XXX = Button.New(private.m_ViewRef.m_Dic_Trans:Get("&Button_XXX"))

-- ❌ Button 直接用 Dictionary:Get（缺少包裝）
private.m_Button_XXX = private.m_ViewRef.m_Dic_ButtonEx:Get("&Button_XXX")
```

---

## 完整綁定範例

```lua
-- region ViewRef 綁定
private.m_Image_Background = private.m_ViewRef.m_Dic_Image:Get("&Image_Background")
private.m_TMPText_Title = private.m_ViewRef.m_Dic_TMPText:Get("&TMPText_Title")
private.m_Trans_Content = private.m_ViewRef.m_Dic_Trans:Get("&Trans_Content")
private.m_Button_Confirm = Button.New(private.m_ViewRef.m_Dic_Trans:Get("&Button_Confirm"))
private.m_Toggle_AutoPlay = private.m_ViewRef.m_Dic_Toggle:Get("&Toggle_AutoPlay")
private.m_Slider_Volume = private.m_ViewRef.m_Dic_Slider:Get("&Slider_Volume")
-- endregion
```

---

## Dispose 清理（必須）

```lua
function this.Dispose()
    if private.m_Button_Confirm then
        private.m_Button_Confirm:RemoveAllListeners()
        private.m_Button_Confirm = nil
    end
    if private.m_Toggle_AutoPlay then
        private.m_Toggle_AutoPlay.onValueChanged:RemoveAllListeners()
        private.m_Toggle_AutoPlay = nil
    end
    private.m_Image_Background = nil
    private.m_TMPText_Title = nil
end
```

---

## ✅ 快速檢查清單

- [ ] 所有 UI 物件名稱以 `&` 開頭
- [ ] Component 對應到正確的 Dictionary
- [ ] `&Button_` 開頭使用 `Button.New()` 包裝
- [ ] 變數命名：`private.m_{型別}_{名稱}`
- [ ] 所有有監聽的元件在 Dispose 中 `RemoveAllListeners()`
- [ ] Dispose 中清空所有引用為 `nil`
