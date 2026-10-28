@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERRO] Rode INSTALAR_WINDOWS.cmd primeiro.
  exit /b 1
)
set "VPY=%CD%\.venv\Scripts\python.exe"
"%VPY%" Back-End\diagnose_env.py --connect
if errorlevel 1 exit /b 2
pushd Back-End
"%VPY%" -m database.create_tables
if errorlevel 1 (
  popd
  exit /b 3
)
"%VPY%" -m database.seed
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" exit /b 4
echo [OK] Banco pronto. Login: 1 / 2 / 123456
endlocal
