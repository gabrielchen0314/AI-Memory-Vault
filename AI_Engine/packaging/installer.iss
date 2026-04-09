; AI Memory Vault v3.5 — Inno Setup 安裝腳本
; 需要 Inno Setup 6.x：https://jrsoftware.org/isdl.php
;
; 目錄設計：
;   程式目錄  {autopf}\AI-Memory-Vault\      (Program Files, read-only)
;   使用者資料 {userappdata}\AI-Memory-Vault\  (由 exe 自動建立，安裝程式不管)
;   知識庫     使用者 Setup Wizard 時自訂
;
; @author gabrielchen
; @version 3.4.0

#define AppName      "AI Memory Vault"
#define AppVersion   "3.5.0"
#define AppPublisher "LIFEOFDEVELOPMENT"
#define AppURL       "https://github.com/lifeofdevelopment/ai-memory-vault"
#define AppExe       "vault-cli.exe"
#define SourceDir    "..\dist\vault-ai"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; 輸出設定
OutputDir=..\dist
OutputBaseFilename=AI-Memory-Vault-Setup-v{#AppVersion}
; 壓縮（LZMA 最佳壓縮，打包 ML 套件效果顯著）
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
; 外觀
WizardStyle=modern
WizardSizePercent=120
; 需要管理員（寫入 Program Files）
PrivilegesRequired=admin
; 最低 Windows 版本：Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; 桌面捷徑
Name: "desktopicon_menu";   Description: "建立桌面捷徑（主選單）";   GroupDescription: "桌面捷徑："
Name: "desktopicon_cli";      Description: "建立桌面捷徑（CLI）";        GroupDescription: "桌面捷徑："; Flags: unchecked
Name: "desktopicon_sched";    Description: "建立桌面捷徑（排程管理）";    GroupDescription: "桌面捷徑："; Flags: unchecked

[Files]
; 打包整個 dist/vault-ai/ 目錄（含 _internal/ 所有 ML 套件）
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 捷徑用 Batch 腳本 + PowerShell 選單
Source: "shortcuts\主選單.bat";     DestDir: "{app}"; Flags: ignoreversion
Source: "shortcuts\vault-menu.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "shortcuts\環境設定.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "shortcuts\排程管理.bat";  DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 開始功能表
Name: "{group}\AI Memory Vault";             Filename: "{app}\主選單.bat";           Comment: "AI Memory Vault v3 主選單"
Name: "{group}\AI Memory Vault（CLI）";      Filename: "{app}\vault-cli.exe";       Comment: "啟動 AI Memory Vault 互動式 CLI"
Name: "{group}\環境設定";                  Filename: "{app}\環境設定.bat";         Comment: "設定 Vault 路徑、使用者、LLM"
Name: "{group}\排程管理";                  Filename: "{app}\排程管理.bat";         Comment: "管理 Windows 自動排程任務"
Name: "{group}\解除安裝 {#AppName}";       Filename: "{uninstallexe}"

; 桌面捷徑（依勾選項目建立）
Name: "{autodesktop}\AI Memory Vault";    Filename: "{app}\主選單.bat";           Tasks: desktopicon_menu
Name: "{autodesktop}\AI Memory Vault CLI"; Filename: "{app}\vault-cli.exe";       Tasks: desktopicon_cli
Name: "{autodesktop}\Vault 排程管理";     Filename: "{app}\排程管理.bat";         Tasks: desktopicon_sched

[Run]
; 安裝完成後可選擇立即開啟主選單
Filename: "{app}\主選單.bat"; Description: "立即啟動 AI Memory Vault"; \
    Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
; 解安裝時清除程式目錄（使用者資料 %APPDATA%\AI-Memory-Vault\ 保留，不刪）
Type: filesandordirs; Name: "{app}"

[Code]
// 安裝前檢查：同版本已安裝時提示升級
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

// 安裝完成頁面額外說明
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    WizardForm.FinishedLabel.Caption :=
      '安裝完成！' + #13#10 + #13#10 +
      '首次使用請執行「環境設定」設定 Vault 路徑。' + #13#10 +
      '設定完成後雙擊「AI Memory Vault」即可啟動。' + #13#10 + #13#10 +
      '使用者資料存放於：' + #13#10 +
      ExpandConstant('{userappdata}\AI-Memory-Vault\');
  end;
end;
