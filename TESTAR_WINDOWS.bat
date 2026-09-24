@echo off
setlocal
cd /d "%~dp0"
title Tradutor Talk - Teste Windows

echo ================================================================
echo TRADUTOR TALK - PREPARAR E TESTAR
echo ================================================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo Python Launcher nao encontrado.
    echo Instale Python 3.12 ou superior e marque a opcao de adicionar ao PATH.
    pause
    exit /b 1
)

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 ou superior nao foi encontrado.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente local .venv...
    py -3 -m venv .venv
    if errorlevel 1 goto :erro
)

call ".venv\Scripts\activate.bat"

echo Instalando/atualizando dependencias locais...
python -m pip install -e ".[dev,runtime]"
if errorlevel 1 goto :erro

echo.
echo Executando testes deterministas...
python -m pytest
if errorlevel 1 goto :erro

echo.
echo Abrindo assistente de teste real...
python -m tradutor_talk.app.windows_test
set EXITCODE=%ERRORLEVEL%

echo.
if "%EXITCODE%"=="0" (
    echo Teste encerrado.
) else (
    echo O teste terminou com codigo %EXITCODE%.
)
pause
exit /b %EXITCODE%

:erro
echo.
echo Falha durante a preparacao.
pause
exit /b 1
