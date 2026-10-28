@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo === GHCE - teste da API ===
curl.exe -fsS http://127.0.0.1:5000/api/ping
if errorlevel 1 (
  echo.
  echo [ERRO] A API nao respondeu em 127.0.0.1:5000.
  exit /b 1
)
echo.
echo.
echo Estado do detector:
curl.exe -sS http://127.0.0.1:5000/api/modelo
echo.
endlocal
