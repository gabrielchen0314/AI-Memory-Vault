@echo off
:: AI Memory Vault v3 — 排程管理工具（雙擊啟動）
:: 以系統管理員身分重新啟動（必要，才能寫入 Windows 工作排程器）
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0scheduler-menu.ps1"
