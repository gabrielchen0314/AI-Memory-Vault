---
type: rule
domain: coding
category: coding-style-universal
workspace: _global
applies_to: [all-languages, all-projects]
severity: must
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, coding-style, naming, universal, git, security]
ai_summary: "全語言共用編碼規範：命名前綴系統（m_/i/_）、結構順序、Region 分區、XML/LuaDoc/docstring 三語言註解格式、Git commit 規範、安全原則。語言專屬補充見各組織 rules/。"
---

# Coding Style — 通用規範（全語言）

> 本規範適用於 **所有語言、所有組織**。  
> 語言特定規則見 `workspaces/{org}/rules/`，組織規則可覆蓋本規範。

---

## ⛔ 絕對禁止（所有語言）

| 禁止項目 | 原因 |
|---------|------|
| `goto` | 破壞結構化流程控制 |
| 魔術數字 | 降低可讀性，改用常數或 Enum |
| 空的 catch/except | 吞掉錯誤，導致難以除錯 |
| 硬編碼密鑰/Token | 安全漏洞，改用環境變數/設定檔 |

---

## 1. 命名規則（全語言共通）

| 類型 | 前綴 | C# 範例 | Lua 範例 | Python 範例 |
|------|------|---------|---------|------------|
| 成員變數 | `m_` | `m_Counter` | `private.m_Counter` | `self.m_Counter` |
| 參數 | `i` | `iAmount` | `iAmount` | `iAmount` |
| 區域變數 | `_` | `_Result` | `local _Result` | `_Result` |
| 靜態變數 | `s_`（可選） | `s_Instance` | — | `s_Instance` |
| 常數 | 全大寫 | `MAX_COUNT` | `MAX_COUNT` | `MAX_COUNT` |
| 列舉/介面 | `E`/`I` | `EState`, `IProvider` | `EState` | `EState` |
| 例外變數 | `_Ex` | `catch(Exception _Ex)` | — | `except Exception as _Ex:` |

### 布林命名

使用 `Is`/`Can`/`Has`/`Have` 開頭：

```
m_IsInitialized, m_CanMove, m_HasError
```

### 集合命名

標示容器型別：

```
m_List_Items, m_Dic_Cache, m_Arr_Scores
```

### 管理器/資料類別

```
EnemySpawnMgr, BattleMgr     ← Mgr 後綴
MonsterData, PlayerData       ← Data 後綴
```

---

## 2. 類別/模組結構順序

```
常數定義
→ 靜態變數 / 類別變數
→ 成員變數（instance fields）
→ Unity 組件 / 外部依賴（C# 適用）
→ 屬性 / 公開存取器
→ 初始化 / 建構子 (Awake / Start / __init__)
→ 私有方法
→ 公開方法
→ 事件處理
→ 解構 / 清理 (OnDestroy / Dispose / __del__)
```

使用 `#region / #endregion`（C#）、`-- region / -- endregion`（Lua）、`# region / # endregion`（Python）分區。

---

## 3. 格式規範

| 規則 | 說明 |
|------|------|
| 縮排 | Tab（C#/Lua）/ 4 空格（Python） |
| 大括號 | Allman style（獨立一行對齊）— C#/Lua |
| 括號內側 | 加空格 → `if( condition )` / `func( arg )` |
| 每行長度 | 120 字以內 |
| 每個變數 | 單獨一行宣告，不合併 |
| 方法之間 | 空一行分隔 |

```csharp
// ✅ C# 正確
if( m_Counter > MAX_COUNT )
{
    ResetCounter();
}
```

```lua
-- ✅ Lua 正確
if( private.m_Counter > MAX_COUNT ) then
    this.ResetCounter()
end
```

```python
# ✅ Python 正確
if( self.m_Counter > MAX_COUNT ):
    self._reset_counter()
```

---

## 4. 註解規範

### 類別/模組（必填）

**C#**
```csharp
/// <summary>
/// 類別說明
/// @author gabrielchen
/// @version 1.0
/// @since [ProjectName] 1.0
/// @date YYYY.MM.DD
/// </summary>
public class MyClass { }
```

**Lua**
```lua
---@class ModuleName
---@author gabrielchen
---@version 1.0
---@date YYYY.MM.DD
ModuleName = {}
```

**Python**
```python
"""
模組說明。

@author gabrielchen
@version 1.0
@since [ProjectName] 1.0
@date YYYY.MM.DD
"""
```

### 方法/函式（有參數或回傳值時必填）

**C#**
```csharp
/// <summary>驗證玩家名稱</summary>
/// <param name="iPlayerName">玩家名稱</param>
/// <returns>是否有效</returns>
private bool ValidatePlayerName( string iPlayerName ) { }
```

**Lua**
```lua
---驗證玩家名稱
---@param iPlayerName string 玩家名稱
---@return boolean 是否有效
function this.ValidatePlayerName( iPlayerName )
end
```

**Python**
```python
def validate_player_name( self, iPlayerName: str ) -> bool:
    """
    驗證玩家名稱。
    :param iPlayerName: 玩家名稱
    :return: 是否有效
    """
```

### 成員變數（必填）

```csharp
/// <summary>玩家當前分數</summary>
private int m_Score;
```

```lua
---@type number 玩家當前分數
private.m_Score = 0
```

```python
self.m_Score: int = 0  # 玩家當前分數
```

---

## 5. 例外處理原則

不得靜默吞掉錯誤，至少記錄或回傳錯誤訊息：

```csharp
// ✅ C#
catch( SpecificException _Ex )
{
    Debug.LogError( $"[{GetType().Name}] {_Ex.Message}" );
}
```

```python
# ✅ Python
except Exception as _Ex:
    return { "error": str( _Ex ) }
```

---

## 6. Git Commit 規範

### Commit Type

| 前綴 | 用途 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | Bug 修正 |
| `refactor:` | 重構 |
| `docs:` | 文件更新 |
| `style:` | 格式調整（不影響邏輯） |
| `chore:` | 雜項維護 |
| `test:` | 測試相關 |
| `perf:` | 效能優化 |

### 原則

- **原子性**：一個 commit 做一件事
- **可追溯**：說明「為什麼」改，不只說「改了什麼」
- **可回溯**：每個 commit 應能獨立 revert
- Commit message 使用繁體中文描述

### 格式

```
<type>: <簡短描述>

- 變更項目 1
- 變更項目 2
```

---

## 7. 安全規範

| 規則 | 說明 |
|------|------|
| 禁止硬編碼密鑰 | 改用 `.env` / 設定檔 / 環境變數 |
| 路徑穿越防護 | 寫入前驗證路徑在允許範圍內 |
| Log 不洩漏敏感資訊 | Token/密碼/個資不進 log |
| Client 不可信 | 重要邏輯在 Server / 後端驗證 |
| 只允許合法副檔名 | 寫入 Vault 只允許 `.md` |

---

## 8. 語言/領域專屬補充索引

| 規則 | 路徑 |
|------|------|
| 專案 API Map 同步規範 | `workspaces/_global/rules/02-project-api-map-sync.md` |
| C# Coding Style | `workspaces/CHINESEGAMER/rules/01-csharp-coding-style.md` |
| Lua Coding Style | `workspaces/CHINESEGAMER/rules/02-lua-coding-style.md` |
| Python Coding Style | `workspaces/LIFEOFDEVELOPMENT/rules/01-python-coding-style.md` |
