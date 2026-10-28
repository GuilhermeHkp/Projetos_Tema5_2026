@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call DIAGNOSTICAR.cmd
if errorlevel 1 exit /b %errorlevel%
set "VPY=%CD%\.venv\Scripts\python.exe"
pushd Back-End
"%VPY%" -m unittest tests.test_decision_brain -v
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" exit /b %RC%
echo [OK] Testes locais passaram.
endlocal
