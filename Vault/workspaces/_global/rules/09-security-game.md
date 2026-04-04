---
type: rule
domain: security
category: game-security
workspace: _global
applies_to: [csharp, lua, unity, networking]
severity: critical
created: 2026.04.04
last_updated: 2026.04.04
tags: [rule, security, anti-cheat, game, server-validation]
ai_summary: "遊戲安全審查規範：Client 永遠不可信、Server-Side 驗證、禁止硬編碼敏感資訊、數值範圍檢查、封包簽章、xLua 白名單命令、安全審查報告格式。"
---

# 遊戲安全審查

> 🔒 **黃金法則：Client 永遠不可信！**

---

## 核心原則

| # | 原則 | 說明 |
|---|------|------|
| 1 | **永遠不信任 Client** | 所有重要邏輯 Server 驗證 |
| 2 | **最小權限** | 只給必要的存取權限 |
| 3 | **深度防禦** | 多層驗證比單點防護更安全 |
| 4 | **記錄一切** | 異常行為要有 Log 可追溯 |

---

## 敏感資訊保護（CRITICAL）

```csharp
// ❌ 硬編碼密鑰
private const string ApiKey = "sk-xxxxx";

// ✅ 使用設定或環境變數
private string ApiKey => Config.GetApiKey();
```

```lua
-- ❌ Lua 中硬編碼
local API_KEY = "sk-xxxxx"

-- ✅ 從設定檔讀取
local _ApiKey = ConfigMgr.Get("ApiKey")
```

---

## Server-Side 驗證（CRITICAL）

```csharp
// ❌ Client-Side 計算獎勵
public void OnBattleEnd(int score)
{
    int reward = score * 10;
    PlayerData.Gold += reward;
    SendToServer(reward);
}

// ✅ Server-Side 驗證
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
}
```

---

## Lua / xLua 安全（白名單命令）

```lua
-- ❌ 動態執行玩家輸入
function ExecuteCommand(input)
    loadstring(input)()
end

-- ✅ 白名單命令
local ALLOWED_COMMANDS = {
    ["help"] = ShowHelp,
    ["status"] = ShowStatus,
}
function ExecuteCommand(iInput)
    local _Handler = ALLOWED_COMMANDS[iInput]
    if _Handler then _Handler()
    else D.LogWarning("未知命令: " .. tostring(iInput))
    end
end
```

---

## ✅ 快速檢查清單

- [ ] 無硬編碼 API Key / 密碼 / Token
- [ ] Log 中無敏感資料
- [ ] 獎勵/金幣由 Server 計算
- [ ] 所有外部輸入都經過驗證
- [ ] 數值有範圍檢查 + 溢位保護
- [ ] 沒有 `loadstring` 執行外部輸入
- [ ] 命令系統使用白名單
