@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title AEVIA - Administrador
if exist ".venv\Scripts\python.exe" (
 ".venv\Scripts\python.exe" "scripts\configurar_admin.py"
) else (
 py "scripts\configurar_admin.py"
)
echo.
pause
