---
type: rule
domain: security
category: game-security
workspace: CHINESEGAMER
applies_to: [csharp, lua, unity, networking]
severity: critical
created: 2026-03-27
last_updated: 2026-03-27
tags: [rule, security, anti-cheat, game, server-validation]
source: RD-Agent-遊戲安全審查專家.agent.md
ai_summary: "遊戲安全審查規範：Client 永遠不可信、Server-Side 驗證、禁止硬編碼敏感資訊、數值範圍檢查、封包簽章、xLua 白名單命令、安全審查報告格式。"
---

# 遊戲安全審查 — CHINESE GAMER

> 🔒 **黃金法則：Client 永遠不可信！**
> 🤖 **對應 Agent**：`@SecurityReviewer`

---

## 🎯 核心原則

| # | 原則 | 說明 |
|---|------|------|
| 1 | **永遠不信任 Client** | 所有重要邏輯 Server 驗證 |
| 2 | **最小權限** | 只給必要的存取權限 |
| 3 | **深度防禦** | 多層驗證比單點防護更安全 |
| 4 | **記錄一切** | 異常行為要有 Log 可追溯 |

---

## 🔴 1. 敏感資訊保護（CRITICAL）

### 絕對禁止

```csharp
// ❌ CRITICAL: 硬編碼密鑰
private const string ApiKey = "sk-xxxxx";
private const string Password = "admin123";
private const string Token = "eyJhbGciOiJIUzI1NiJ9...";

// ✅ CORRECT: 使用設定或環境變數
private string ApiKey => Config.GetApiKey();
private string Token => AuthService.GetToken();
```

```lua
-- ❌ CRITICAL: Lua 中硬編碼
local API_KEY = "sk-xxxxx"

-- ✅ CORRECT: 從 Server 取得或設定檔讀取
local _ApiKey = ConfigMgr.Get("ApiKey")
```

### 檢查清單

- [ ] 沒有硬編碼的 API Key
- [ ] 沒有硬編碼的密碼
- [ ] 沒有硬編碼的 Token
- [ ] Log 中沒有敏感資訊
- [ ] 錯誤訊息不洩漏內部架構

```csharp
// ❌ Log 洩漏敏感資訊
Debug.Log($"Login failed for user {username} with password {password}");

// ✅ 安全的 Log
Debug.Log($"Login failed for user {username}");
```

---

## 🔴 2. Server-Side 驗證（CRITICAL）

### Client-Side 風險等級

| 風險等級 | 類型 | 防護方式 |
|:--------:|------|---------|
| 🔴 高 | 數值修改（金幣、HP、經驗） | Server 計算 + 驗證 |
| 🔴 高 | 時間加速 | Server 時間戳驗證 |
| 🟡 中 | 自動化腳本 | 行為分析 |
| 🟡 中 | 封包竄改 | 簽章驗證 |

### 獎勵計算

```csharp
// ❌ VULNERABLE: Client-Side 計算獎勵
public void OnBattleEnd(int score)
{
    int reward = score * 10;       // Client 計算
    PlayerData.Gold += reward;      // Client 直接加
    SendToServer(reward);           // 發送結果
}

// ✅ SECURE: Server-Side 驗證
public void OnBattleEnd(int score)
{
    BattleResult _Result = new BattleResult
    {
        BattleId  = m_CurrentBattleId,
        Score     = score,
        Timestamp = ServerTime.Now,
        Hash      = CalculateHash(m_CurrentBattleId, score)
    };
    SendToServer(_Result);
    // 等待 Server 回傳正確獎勵，不在 Client 計算
}
```

### 數值範圍檢查

```csharp
// ❌ VULNERABLE: 沒有範圍檢查
public void AddGold(int amount)
{
    PlayerData.Gold += amount;
}

// ✅ SECURE: 範圍驗證 + 溢位保護 + 交易記錄
public void AddGold(int iAmount)
{
    if (iAmount < 0 || iAmount > MAX_SINGLE_REWARD)
        throw new SecurityException($"異常金幣數量: {iAmount}");

    long _NewTotal = (long)PlayerData.Gold + iAmount;
    if (_NewTotal > MAX_GOLD || _NewTotal < 0)
        throw new SecurityException("金幣溢位");

    PlayerData.Gold = (int)_NewTotal;
    LogTransaction(iAmount, "AddGold");
}
```

---

## 🟡 3. 輸入驗證

### 字串輸入

```csharp
// ❌ VULNERABLE: 直接使用玩家輸入
public void SetNickname(string input)
{
    PlayerData.Nickname = input;
}

// ✅ SECURE: 驗證 + 清理
public void SetNickname(string iInput)
{
    if (string.IsNullOrWhiteSpace(iInput))
        throw new ArgumentException("暱稱不能為空");

    if (iInput.Length > 20)
        throw new ArgumentException("暱稱過長");

    // 過濾特殊字元（保留中文、英文、數字）
    string _Sanitized = Regex.Replace(iInput, @"[^\w\u4e00-\u9fff]", "");

    PlayerData.Nickname = _Sanitized;
}
```

---

## 🟡 4. Lua / xLua 安全

### 動態執行防護

```lua
-- ❌ CRITICAL: 動態執行玩家輸入
function ExecuteCommand(input)
    loadstring(input)()   -- 超級危險！
end

-- ✅ SECURE: 白名單命令
local ALLOWED_COMMANDS = {
    ["help"]   = ShowHelp,
    ["status"] = ShowStatus,
    ["info"]   = ShowInfo,
}

function ExecuteCommand(iInput)
    local _Handler = ALLOWED_COMMANDS[iInput]
    if _Handler then
        _Handler()
    else
        D.LogWarning("未知命令: " .. tostring(iInput))
    end
end
```

### 資料反序列化

```lua
-- ❌ VULNERABLE: 直接使用未驗證資料
local _Data = json.decode(iServerResponse)
PlayerData.Gold = _Data.gold

-- ✅ SECURE: 驗證後再使用
local _Data = json.decode(iServerResponse)
if not _Data or type(_Data.gold) ~= "number" then
    D.LogError("資料驗證失敗")
    return
end
if _Data.gold < 0 or _Data.gold > MAX_GOLD then
    D.LogError("金幣數值異常: " .. _Data.gold)
    return
end
PlayerData.Gold = _Data.gold
```

---

## 📊 5. 安全審查報告格式

當使用 `@SecurityReviewer` 進行審查時，輸出格式：

```
🔒 安全審查報告

📅 審查日期: YYYY-MM-DD
📁 審查範圍: [檔案/模組列表]

═══════════════════════════════════════

🔴 嚴重問題 (必須立即修正)
──────────────────────────────────────
1. [問題描述]
   位置: path/to/file.cs:123
   風險: [具體風險說明]
   建議: [修正方案]

🟡 中等問題 (應儘快修正)
──────────────────────────────────────
1. [問題描述]
   ...

🟢 輕微問題 (建議改進)
──────────────────────────────────────
1. [問題描述]
   ...

✅ 優良實踐
──────────────────────────────────────
- [做得好的地方]

═══════════════════════════════════════

📊 總結
- 嚴重問題: X 個
- 中等問題: X 個
- 輕微問題: X 個
- 整體評級: [通過/需改進/不通過]
```

---

## ⚡ 觸發安全審查的情境

| 情境 | 必須審查 |
|------|:--------:|
| 新增涉及金幣/道具/鑽石的功能 | ✅ |
| 新增玩家輸入處理 | ✅ |
| 新增/修改 Client↔Server 協定 | ✅ |
| 修改排名/積分系統 | ✅ |
| 上線前最終審查 | ✅ |
| 純 UI 調整（不涉及邏輯） | ❌ |
| 文件/註解更新 | ❌ |

---

## ✅ 快速檢查清單

### 敏感資訊
- [ ] 無硬編碼 API Key / 密碼 / Token
- [ ] Log 中無敏感資料
- [ ] 錯誤訊息不洩漏內部架構

### 資料驗證
- [ ] 所有外部輸入都經過驗證
- [ ] 字串有長度限制 + 特殊字元過濾
- [ ] 數值有範圍檢查 + 溢位保護
- [ ] Server 回傳資料有型別和範圍驗證

### 遊戲邏輯
- [ ] 獎勵/金幣由 Server 計算
- [ ] 排名/積分由 Server 驗證
- [ ] 時間相關邏輯用 Server 時間戳
- [ ] 重要交易有記錄可追溯

### 通訊安全
- [ ] 敏感封包加密傳輸
- [ ] 封包有簽章驗證
- [ ] 有重放攻擊防護

### Lua 特定
- [ ] 沒有 `loadstring` 執行外部輸入
- [ ] 命令系統使用白名單
- [ ] 反序列化資料有型別檢查

---

## 例外情況

- 開發/Debug 模式下的 GM 命令可放寬，但**必須**在正式版完全移除
- 純展示用數值（如 UI 特效數字）不需 Server 驗證
- 單機模式的邏輯不適用 Server 驗證規則，但仍需本地防護
