@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  AI Memory Vault v3 - 環境設定
echo ============================================
echo.
vault-cli.exe --setup
pause
