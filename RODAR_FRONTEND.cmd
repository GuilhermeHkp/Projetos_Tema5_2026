@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERRO] Rode INSTALAR_WINDOWS.cmd primeiro.
  exit /b 1
)
set "VPY=%CD%\.venv\Scripts\python.exe"
pushd Front-End
echo Abra no navegador: http://localhost:5500/Login/index1_pag_Login.html
"%VPY%" -m http.server 5500
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
