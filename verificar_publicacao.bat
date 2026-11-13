@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
 ".venv\Scripts\python.exe" "scripts\verificar_publicacao.py"
) else (
 py "scripts\verificar_publicacao.py"
)
echo.
pause
