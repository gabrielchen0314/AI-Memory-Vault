---
type: rule
domain: coding
category: csharp-coding-style
workspace: _global
applies_to: [csharp, unity]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, csharp, unity, naming, coding-style]
ai_summary: "C# / Unity 編碼規範補充：Unity 組件命名、Region 結構、var 禁止、組件快取、事件清理、Allman 大括號。通用命名規則見 _global/rules/01-coding-style-universal.md。"
---

# C# Coding Style

> 本規範為 `workspaces/_global/rules/01-coding-style-universal.md` 的 C# 補充。  
> 通用命名（m_/i/_ 前綴、常數、布林、集合）請見全域規則。

---

## ⛔ C# 特定禁止

| 禁止項目 | 原因 |
|---------|------|
| `var`（除匿名型別 / LINQ） | 隱藏型別，降低可讀性 |
| 空的 `catch { }` | 吞掉錯誤，難以除錯 |
| `goto` | 同全域規則 |

```csharp
// ❌ 禁止 var
var player = GetPlayer();

// ✅ 明確型別
PlayerData _Player = GetPlayer();
```

---

## 1. Unity 組件命名

格式：`m_{型別}_{名稱}`

```csharp
// ✅ 正確
private Button    m_Button_Start;
private TMP_Text  m_Text_Title;
private Image     m_Image_Icon;
private Transform m_Trans_Content;

// ❌ 錯誤：缺少型別前綴
private Button    m_Start;
private TMP_Text  m_Title;
```

---

## 2. Region 結構（標準順序）

```csharp
public class Example : MonoBehaviour
{
    #region 常數定義
    private const int MAX_COUNT = 100;
    #endregion

    #region 靜態變數
    #endregion

    #region 成員變數
    /// <summary>計數器</summary>
    private int m_Counter;

    /// <summary>是否已初始化</summary>
    private bool m_IsInitialized;
    #endregion

    #region Unity 組件
    /// <summary>開始按鈕</summary>
    private Button m_Button_Start;
    #endregion

    #region 公開屬性
    #endregion

    #region Unity 生命週期
    void Awake() { }
    void Start() { }
    void OnDestroy() { }
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

## 3. 完整類別範例

```csharp
/// <summary>
/// 範例管理器
/// @author gabrielchen
/// @version 1.0
/// @since ProjectName 1.0
/// @date 2026.04.04
/// </summary>
public class ExampleMgr : MonoBehaviour
{
    #region 常數定義
    private const int MAX_COUNT = 100;
    #endregion

    #region 成員變數
    /// <summary>計數器</summary>
    private int m_Counter;

    /// <summary>是否就緒</summary>
    private bool m_IsReady;
    #endregion

    #region Unity 組件
    /// <summary>確認按鈕</summary>
    private Button m_Button_Confirm;
    #endregion

    #region Unity 生命週期
    void Awake()
    {
        Initialize();
    }

    void OnDestroy()
    {
        if( m_Button_Confirm != null )
        {
            m_Button_Confirm.onClick.RemoveAllListeners();
        }
    }
    #endregion

    #region 私有方法
    private void Initialize()
    {
        m_Counter = 0;
        m_IsReady = true;
    }
    #endregion

    #region 公開方法
    /// <summary>增加計數</summary>
    /// <param name="iAmount">增加數量</param>
    /// <returns>是否成功</returns>
    public bool AddCount( int iAmount )
    {
        if( iAmount <= 0 || m_Counter + iAmount > MAX_COUNT )
        {
            return false;
        }

        m_Counter += iAmount;
        return true;
    }
    #endregion
}
```

---

## 4. 例外處理

```csharp
try
{
    DoSomething();
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
