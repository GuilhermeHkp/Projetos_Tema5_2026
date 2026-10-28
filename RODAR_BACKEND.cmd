@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call DIAGNOSTICAR.cmd
if errorlevel 1 (
  echo.
  echo Backend NAO iniciado. Corrija o erro mostrado acima.
  exit /b %errorlevel%
)
set "VPY=%CD%\.venv\Scripts\python.exe"
pushd Back-End
"%VPY%" api.py
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
