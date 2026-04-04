@echo off
chcp 65001 >nul
:: AI Memory Vault v3 — 環境設定工具（雙擊啟動）
powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0setup-menu.ps1"
