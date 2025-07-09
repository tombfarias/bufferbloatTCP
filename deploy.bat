@echo off
setlocal enabledelayedexpansion

echo Iniciando bufferbloatTCP...

set "APP_NAME=bufferbloatTCP"
set "VENV_DIR=.venv_%APP_NAME%"
set "SCRIPT=webcontrol\app.py"
set "PORTAS=5210 5260 5310 5360 5410"
set "PIDFILE=.bufferbloattcp-pids"

REM Verifica Vagrant
where vagrant >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Vagrant não encontrado. Instale em: https://www.vagrantup.com/downloads
    exit /b 1
)

REM Verifica VirtualBox
where VBoxManage >nul 2>nul
if errorlevel 1 (
    echo [ERRO] VirtualBox não encontrado. Baixe em: https://www.virtualbox.org/
    exit /b 1
)

REM Cria ambiente virtual se necessário
if not exist "%VENV_DIR%" (
    echo Criando ambiente virtual em %VENV_DIR%...
    python -m venv %VENV_DIR%
)

REM Ativa o ambiente virtual
call "%VENV_DIR%\Scripts\activate.bat"

REM Instala bottle se necessário
python -c "import bottle" >nul 2>nul
if errorlevel 1 (
    echo Instalando dependência 'bottle'...
    pip install bottle
)

REM Cria arquivo de PIDs se necessário
if not exist "%PIDFILE%" (
    type nul > "%PIDFILE%"
)

REM Remove entradas de processos mortos
(for /f "tokens=1,2 delims=:" %%G in (%PIDFILE%) do (
    tasklist /FI "PID eq %%H" | findstr /R /C:" %%H " >nul
    if errorlevel 1 (
        rem processo não existe mais, não escreve de volta
    ) else (
        echo %%G:%%H
    )
)) > "%PIDFILE%.tmp"
move /Y "%PIDFILE%.tmp" "%PIDFILE%" >nul

REM Verifica se o par PORT:PID está registrado como nosso
set "foi_criado_por_mim="
call :check_pidfile

REM Loop de portas
for %%P in (%PORTAS%) do (
    set "PORTA=%%P"
    for /f "tokens=5" %%A in ('netstat -aon ^| findstr :%%P ^| findstr LISTENING') do (
        set "PID=%%A"

        set "ENCONTRADO=0"
        for /f "tokens=1,2 delims=:" %%X in (%PIDFILE%) do (
            if "%%X"=="%%P" if "%%Y"=="%%A" (
                set "ENCONTRADO=1"
            )
        )

        if "!ENCONTRADO!"=="1" (
            for /f "tokens=* delims=" %%B in ('wmic process where "ProcessId=%%A" get CommandLine ^| findstr /I "%SCRIPT%"') do (
                echo.
                echo >>> A porta %%P está ocupada pelo processo %%A
                echo Comando: %%B
                set /p RES=Deseja finalizar esse processo? [y/N] 
                if /i "!RES!"=="y" (
                    taskkill /PID %%A /T /F >nul 2>&1
                    echo Processo %%A finalizado.
                    call :remove_pid %%P %%A
                    goto iniciar
                ) else (
                    echo Ignorando porta %%P...
                    goto proxima
                )
            )
        ) else (
            echo Porta %%P ocupada por processo que não foi iniciado por este script. Pulando...
            goto proxima
        )
    )
    goto iniciar

    :proxima
)

echo Nenhuma porta disponível. Finalize processos manualmente ou libere portas.
exit /b 1

:iniciar
echo Iniciando servidor na porta %PORTA%...
start /B python %SCRIPT% %PORTA%
set /A "pid=%ERRORLEVEL%"
echo %PORTA%:%pid%>> "%PIDFILE%"
echo Servidor iniciado com PID %pid% (http://localhost:%PORTA%)
exit /b 0

:remove_pid
(for /f "tokens=1,2 delims=:" %%P in (%PIDFILE%) do (
    if not "%%P:%%Q"=="%1:%2" echo %%P:%%Q
)) > "%PIDFILE%.tmp"
move /Y "%PIDFILE%.tmp" "%PIDFILE%" >nul
exit /b 0
