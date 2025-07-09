@echo off
echo Iniciando bufferbloatTCP...

set "APP_NAME=bufferbloatTCP"
set "VENV_DIR=.venv_%APP_NAME%"
setlocal enabledelayedexpansion

REM Verifica se o Vagrant está instalado
where vagrant >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Vagrant nao encontrado. Instale em: https://www.vagrantup.com/downloads
    exit /b 1
)

REM Verifica se o VirtualBox está instalado
where VBoxManage >nul 2>nul
if errorlevel 1 (
    echo [ERRO] VirtualBox nao encontrado. Baixe em: https://www.virtualbox.org/
    exit /b 1
)

REM Lista de portas (menos comuns)
set PORTAS=5210 5260 5310 5360 5410 5460 5510 5560 5610 5660

REM Cria venv se não existir
if not exist "%VENV_DIR%" (
    echo Criando ambiente virtual em %VENV_DIR%...
    python -m venv %VENV_DIR%
)

REM Ativa venv
call %VENV_DIR%\Scripts\activate.bat

REM Instala bottle se não estiver instalado
python -c "import bottle" >nul 2>nul
if errorlevel 1 (
    echo Instalando dependencia 'bottle'...
    pip install bottle >nul
)

REM Tenta rodar na primeira porta livre
for %%P in (%PORTAS%) do (
    powershell -Command "try { [System.Net.Sockets.TcpClient]::new('localhost', %%P).Close(); exit 1 } catch { exit 0 }"
    if not errorlevel 1 (
        echo Iniciando servidor na porta %%P...
        python webcontrol\app.py %%P
        exit /b
    ) else (
        echo Porta %%P ocupada. Tentando próxima...
    )
)

echo Nenhuma porta disponível. Finalize processos ou use outro script.
exit /b 1
