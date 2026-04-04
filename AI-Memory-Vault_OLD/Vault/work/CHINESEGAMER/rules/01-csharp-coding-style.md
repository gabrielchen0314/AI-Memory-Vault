---
type: rule
domain: coding
category: csharp-coding-style
workspace: CHINESEGAMER
applies_to: [csharp, unity]
severity: must
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, csharp, unity, naming, coding-style]
source: RD-指示-CSharp Coding Style.instructions.md
ai_summary: "Unity C# 編碼規範：m_ 成員變數、i 參數、_ 區域變數、禁止 var/goto、Region 結構化、XML 註解、組件快取與事件清理。"
---

# C# Coding Style — CHINESE GAMER

> ⚠️ **絕對禁止使用 goto 語句**
> 📋 **完整 Golden Example**：`.copilot/skills/csharp-coding-style/SKILL.md`

---

## 📐 編碼原則

| 原則 | 說明 |
|------|------|
| **Readability First** | 程式碼是給人讀的，清晰的命名優於註解，保持一致的格式 |
| **KISS** | 選擇最簡單可行的方案，避免過度設計，易懂 > 花俏 |
| **DRY** | 不重複自己，抽取共用邏輯，建立可重用元件 |
| **YAGNI** | 不預先建構未需要的功能，先簡單實作，需要時再重構 |

---

## 🏷️ 命名規範速查表

| 類型 | 前綴 | 範例 |
|------|------|------|
| 成員變數 | `m_` | `m_PlayerName`, `m_IsInitialized` |
| 參數 | `i` | `iAmount`, `iPlayerData` |
| 區域變數 | `_` | `_TempValue`, `_Result` |
| 常數 | 全大寫 | `MAX_COUNT`, `DEFAULT_VALUE` |
| 靜態變數 | `s_` | `s_Instance`, `s_Config` |
| 例外變數 | `_Ex` | `catch (Exception _Ex)` |
| 布林變數 | `Is/Can/Has` | `m_IsActive`, `m_CanMove` |
| 列舉類型 | `E` 前綴 | `ECounterState`, `EItemType` |
| 介面類型 | `I` 前綴 | `IDataProvider` |

### Unity 組件命名

```csharp
// ✅ 格式：m_{型別}_{名稱}
private Button m_Button_Start;
private TMP_Text m_Text_Title;
private Image m_Image_Icon;
private Transform m_Trans_Content;
```

```csharp
// ❌ 錯誤：缺少型別前綴
private Button m_Start;
private TMP_Text m_Title;
```

### 集合命名

```csharp
// ✅ 格式：m_{容器類型}_{內容}
private List<int> m_List_ItemIds;
private Dictionary<int, string> m_Dic_NameById;
private int[] m_Arr_Scores;
```

```csharp
// ❌ 錯誤：缺少容器類型
private List<int> m_ItemIds;
private Dictionary<int, string> m_Names;
```

---

## 📝 XML 註解模板

### 類別註解

```csharp
/// <summary>
/// 類別說明
/// @author 作者
/// @telephone 分機
/// @version 1.0
/// @date YYYY.MM.DD
/// </summary>
public class MyClass
{
}
```

### 方法註解

```csharp
/// <summary>
/// 方法說明
/// </summary>
/// <param name="iParam1">參數1說明</param>
/// <returns>返回值說明</returns>
public bool DoSomething( int iParam1 )
{
}
```

---

## 🏗️ Region 結構順序

```csharp
public class Example
{
    #region 常數定義
    #endregion

    #region 靜態變數
    #endregion

    #region 私有欄位
    #endregion

    #region Unity 組件
    #endregion

    #region 公開屬性
    #endregion

    #region Unity 生命週期
    #endregion

    #region 私有方法
    #endregion

    #region 公開方法
    #endregion

    #region 事件處理
    #endregion
}
```

---

## ⚠️ 絕對禁止

| 禁止項目 | 原因 |
|---------|------|
| ❌ `goto` | 破壞結構化流程控制 |
| ❌ `var`（除非匿名類型） | 降低可讀性，隱藏型別 |
| ❌ 空的 `catch` | 吞掉錯誤，導致難以除錯 |

```csharp
// ❌ 禁止 var
var player = GetPlayer();

// ✅ 明確型別
PlayerData player = GetPlayer();
```

```csharp
// ❌ 禁止空 catch
try { DoSomething(); }
catch { }

// ✅ 正確的例外處理
try
{
    DoSomething();
}
catch( SpecificException _Ex )
{
    Debug.LogError( $"Error: {_Ex.Message}" );
}
```

---

## 🛡️ 例外處理

```csharp
try
{
    // 操作
}
catch( SpecificException _Ex )
{
    Debug.LogError( $"[{GetType().Name}] Error: {_Ex.Message}" );
}
finally
{
    // 清理資源
}
```

---

## 🎮 Unity 特定規範

### 組件快取

```csharp
// ✅ 在 Start/Awake 快取組件
void Start()
{
    m_Button_Start = transform.Find( "Button_Start" )?.GetComponent<Button>();
}
```

```csharp
// ❌ 每次使用都 GetComponent
void Update()
{
    GetComponent<Button>().interactable = true; // 每幀 GC
}
```

### 事件清理

```csharp
// ✅ 在 OnDestroy 移除事件
void OnDestroy()
{
    m_Button_Start?.onClick.RemoveAllListeners();
}
```

### GC 防護

```csharp
// ❌ Update 中產生 GC
void Update()
{
    string log = "Frame: " + Time.frameCount; // 每幀字串 GC
    List<int> temp = new List<int>();           // 每幀 new
}

// ✅ 預先快取
private StringBuilder m_StringBuilder = new StringBuilder();
private List<int> m_TempList = new List<int>();

void Update()
{
    m_StringBuilder.Clear();
    m_StringBuilder.Append("Frame: ").Append(Time.frameCount);
    m_TempList.Clear();
}
```

---

## ✅ 快速檢查清單

- [ ] 成員變數用 `m_` 前綴
- [ ] 參數用 `i` 前綴
- [ ] 區域變數用 `_` 前綴
- [ ] 沒有使用 `var`
- [ ] 沒有使用 `goto`
- [ ] 有 XML 註解（類別 + 公開方法）
- [ ] 使用 `#region` 組織程式碼
- [ ] 組件在 Start/Awake 快取
- [ ] 事件在 OnDestroy 移除（RemoveAllListeners）
- [ ] Update 中無 GC 操作

---

## 例外情況

- `var` 允許用於 LINQ 查詢的匿名類型
- 測試程式碼可適度放寬 region 要求
- Editor 腳本的命名可沿用 Unity Editor API 慣例
