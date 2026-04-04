---
type: knowledge
tags: [powershell, encoding, utf8, bom, windows]
created: 2026-04-04
---

# PowerShell 5.1 與 UTF-8 BOM

## 核心知識

PowerShell 5.1（Windows 內建版本）讀取 `.ps1` 腳本時：
- **無 BOM** → 使用系統預設編碼（繁體中文 Windows = CP950）
- **有 UTF-8 BOM** → 正確以 UTF-8 解碼

## 問題表現

UTF-8 多位元組中文字被 CP950 截斷 → 引號不配對 → 大括號解析連鎖錯誤
報錯：`MissingEndCurlyBrace`、`UnexpectedToken`

## 解法

```powershell
# 重新儲存為 UTF-8 with BOM
$c = Get-Content "script.ps1" -Raw -Encoding UTF8
[System.IO.File]::WriteAllText("script.ps1", $c, [System.Text.UTF8Encoding]::new($true))
```

搭配 `.bat` 入口加 `chcp 65001 >nul` 確保 cmd 層也是 UTF-8。

## 注意

- PowerShell 7+ 預設 UTF-8（無 BOM 也行）
- VS Code 預設存 UTF-8 **無 BOM**，手動存或用腳本補 BOM
