@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "DEST=%USERPROFILE%\Downloads\python-3.12.10-amd64.exe"
echo Baixando Python 3.12.10 x64 da fonte oficial...
curl.exe -fL "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe" -o "%DEST%"
if errorlevel 1 exit /b 1
echo Instalando apenas para o usuario atual...
"%DEST%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 InstallLauncherAllUsers=0 Include_pip=1
echo [OK] Instalacao solicitada. Feche e abra o CMD antes de continuar.
endlocal
