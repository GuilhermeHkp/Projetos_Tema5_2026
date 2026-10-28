@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERRO] Rode INSTALAR_WINDOWS.cmd primeiro.
  exit /b 1
)
set "VPY=%CD%\.venv\Scripts\python.exe"

"%VPY%" -c "import clip" >nul 2>nul
if errorlevel 1 (
  echo Instalando pacote oficial OpenAI CLIP...
  "%VPY%" -m pip install -r requirements-open.txt
  if errorlevel 1 (
    echo [ERRO] Nao foi possivel instalar o pacote CLIP pelo GitHub.
    exit /b 2
  )
)

"%VPY%" tools\download_clip.py
if errorlevel 1 exit /b %errorlevel%
echo [OK] CLIP instalado e validado.
endlocal
