---
type: rule
domain: ui
category: viewref-binding
workspace: CHINESEGAMER
applies_to: [lua, xlua, unity, ui]
severity: must
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, viewref, ui, unity, lua, binding]
source: RD-指示-ViewRef 抓取物件.instructions.md
ai_summary: "Unity Lua ViewRef UI 物件綁定規範：Component → Dictionary 映射、Button 特殊包裝（Button.New）、&前綴命名、RemoveAllListeners 清理。"
---

# ViewRef 物件綁定 — CHINESE GAMER

> 📋 **完整 Golden Example**：`.copilot/skills/viewref-binding/SKILL.md`

---

## 核心概念

ViewRef 是 Unity 場景中 UI 物件到 Lua 的綁定橋樑。場景中的 UI 元件透過 `&` 前綴命名，再由 ViewRef 的 Dictionary 系統提供存取。

---

## 📥 輸入格式

```
&物件名稱 (元件類型)
&物件名稱 (元件類型) -- 註解
```

---

## 📋 Component → Dictionary 映射表

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

## 📤 輸出格式

### 一般元件

```lua
-- 註解（從輸入取得或自動推斷）
private.m_物件名稱 = private.m_ViewRef.Dictionary:Get("&物件名稱")
```

### ⚡ Button 特殊規則

名稱以 `&Button_` 開頭 → **必須**使用 `Button.New()` 包裝：

```lua
-- ✅ Button 必須用 Button.New 包裝
private.m_Button_XXX = Button.New(private.m_ViewRef.m_Dic_Trans:Get("&Button_XXX"))
```

```lua
-- ❌ Button 直接用 Dictionary:Get（缺少包裝）
private.m_Button_XXX = private.m_ViewRef.m_Dic_ButtonEx:Get("&Button_XXX")
```

---

## 📖 完整範例

### 輸入

```
&Image_Background (Image)
&TMPText_Title (TextMeshProUGUI)
&Trans_Content (RectTransform)
&Button_Confirm (ButtonEx)
&Button_Cancel (ButtonEx)
&Toggle_AutoPlay (Toggle)
&Slider_Volume (Slider)
```

### 輸出

```lua
-- region ViewRef 綁定

-- 背景圖片
private.m_Image_Background = private.m_ViewRef.m_Dic_Image:Get("&Image_Background")
-- 標題文字
private.m_TMPText_Title = private.m_ViewRef.m_Dic_TMPText:Get("&TMPText_Title")
-- 內容容器
private.m_Trans_Content = private.m_ViewRef.m_Dic_Trans:Get("&Trans_Content")
-- 確認按鈕
private.m_Button_Confirm = Button.New(private.m_ViewRef.m_Dic_Trans:Get("&Button_Confirm"))
-- 取消按鈕
private.m_Button_Cancel = Button.New(private.m_ViewRef.m_Dic_Trans:Get("&Button_Cancel"))
-- 自動播放開關
private.m_Toggle_AutoPlay = private.m_ViewRef.m_Dic_Toggle:Get("&Toggle_AutoPlay")
-- 音量滑桿
private.m_Slider_Volume = private.m_ViewRef.m_Dic_Slider:Get("&Slider_Volume")

-- endregion
```

---

## 🔗 事件綁定

### Button 事件

```lua
-- ✅ 正確：綁定 Button 事件
function this.BindEvents()
    if private.m_Button_Confirm then
        private.m_Button_Confirm:AddListener(function()
            this.OnConfirmClicked()
        end)
    end

    if private.m_Button_Cancel then
        private.m_Button_Cancel:AddListener(function()
            this.OnCancelClicked()
        end)
    end
end
```

### Toggle 事件

```lua
-- ✅ Toggle 值變化監聽
if private.m_Toggle_AutoPlay then
    private.m_Toggle_AutoPlay.onValueChanged:AddListener(function(iIsOn)
        this.OnAutoPlayChanged(iIsOn)
    end)
end
```

---

## 🧹 Dispose 清理（必須）

```lua
function this.Dispose()
    -- ✅ Button 移除監聽
    if private.m_Button_Confirm then
        private.m_Button_Confirm:RemoveAllListeners()
        private.m_Button_Confirm = nil
    end
    if private.m_Button_Cancel then
        private.m_Button_Cancel:RemoveAllListeners()
        private.m_Button_Cancel = nil
    end

    -- ✅ Toggle 移除監聽
    if private.m_Toggle_AutoPlay then
        private.m_Toggle_AutoPlay.onValueChanged:RemoveAllListeners()
        private.m_Toggle_AutoPlay = nil
    end

    -- ✅ 清空一般引用
    private.m_Image_Background = nil
    private.m_TMPText_Title = nil
    private.m_Trans_Content = nil
    private.m_Slider_Volume = nil
end
```

```lua
-- ❌ 忘記 RemoveAllListeners（記憶體洩漏）
function this.Dispose()
    private.m_Button_Confirm = nil   -- 沒有先移除監聽！
end
```

---

## ✅ 快速檢查清單

- [ ] 所有 UI 物件名稱以 `&` 開頭
- [ ] Component 對應到正確的 Dictionary
- [ ] `&Button_` 開頭的物件使用 `Button.New()` 包裝
- [ ] 變數命名格式：`private.m_{型別}_{名稱}`
- [ ] 所有有監聽的元件在 Dispose 中 `RemoveAllListeners()`
- [ ] Dispose 中清空所有引用為 `nil`
- [ ] 綁定事件前檢查 `if private.m_XXX then`

---

## 例外情況

- 動態生成的 UI 元件不透過 ViewRef，而是用 `Instantiate` + `GetComponent`
- ScrollView 中的 Item 使用 ItemController 模式，各自管理 ViewRef
- 部分舊模組可能使用 `m_ViewRef.m_Dic_Button` 而非 `m_Dic_ButtonEx`，遇到時需確認
