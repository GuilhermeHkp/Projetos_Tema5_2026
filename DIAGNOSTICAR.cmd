@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VPY=%CD%\.venv\Scripts\python.exe"
echo === GHCE - diagnostico ===
if not exist "%VPY%" (
  echo [ERRO] .venv ausente. Rode INSTALAR_WINDOWS.cmd.
  exit /b 1
)
"%VPY%" --version || exit /b 1
"%VPY%" -c "import sys; print('[OK] Python:', sys.executable)" || exit /b 1
"%VPY%" -c "import dotenv, cv2, torch, ultralytics; import mysql.connector; print('[OK] Dependencias principais carregadas')" || (
  echo [ERRO] Dependencia principal ausente. Rode INSTALAR_WINDOWS.cmd.
  exit /b 2
)

"%VPY%" Back-End\diagnose_env.py
if errorlevel 1 exit /b 3

"%VPY%" Back-End\validate_setup.py
if errorlevel 1 exit /b 4

echo [OK] Projeto validado.
exit /b 0
