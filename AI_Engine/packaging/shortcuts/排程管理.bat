@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  AI Memory Vault v3 - 排程管理
echo ============================================
echo.
vault-scheduler.exe
pause
