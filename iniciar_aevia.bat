@echo off
setlocal EnableExtensions
chcp 65001 >nul
title AEVIA V1.7 - Plataforma de memoria historica
cd /d "%~dp0"
echo =============================================
echo AEVIA 1.6 - Inicializacao no Windows (nova porta 8017)
echo =============================================
echo.
where py >nul 2>&1
if not errorlevel 1 goto usar_py
where python >nul 2>&1
if not errorlevel 1 goto usar_python
echo ERRO: Python nao foi encontrado no Windows.
echo Instale o Python e reinicie o terminal.
pause
exit /b 1

:usar_py
set "PYTHON=py"
goto python_pronto

:usar_python
set "PYTHON=python"
goto python_pronto

:python_pronto
echo Verificando Python...
%PYTHON% --version
if errorlevel 1 goto erro_python
if exist ".venv\Scripts\python.exe" goto instalar_bibliotecas
echo Criando ambiente virtual do AEVIA...
%PYTHON% -m venv ".venv"
if errorlevel 1 goto erro_venv

:instalar_bibliotecas
echo.
echo Instalando ou verificando bibliotecas...
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 goto erro_bibliotecas

echo.
echo Atualizando cadastro de municipios brasileiros...
".venv\Scripts\python.exe" -m app.sync_data
if errorlevel 1 goto erro_sincronizacao

echo.
echo =============================================
echo AEVIA pronto para iniciar.
echo Quando aparecer a mensagem Uvicorn running,
echo o navegador sera aberto em: http://127.0.0.1:8017
echo Mantenha esta janela aberta enquanto usar o site.
echo =============================================
echo.
".venv\Scripts\python.exe" -m app.launcher
if errorlevel 1 goto erro_servidor
echo Servidor encerrado.
pause
exit /b 0

:erro_python
echo ERRO: O Python nao executou corretamente.
goto fim_erro
:erro_venv
echo ERRO: Nao foi possivel criar o ambiente virtual.
goto fim_erro
:erro_bibliotecas
echo ERRO: Falha ao instalar bibliotecas. Verifique sua conexao e a mensagem acima.
goto fim_erro
:erro_sincronizacao
echo ERRO: Falha ao iniciar o cadastro de municipios.
goto fim_erro
:erro_servidor
echo ERRO: Falha ao iniciar o servidor. Verifique as mensagens acima.
goto fim_erro
:fim_erro
echo.
echo Envie uma foto desta janela para identificar o erro.
pause
exit /b 1
