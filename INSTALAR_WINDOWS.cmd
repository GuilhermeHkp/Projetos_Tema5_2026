@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo === GHCE - preparar ambiente Python ===
set "PYEXE="
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 --version >nul 2>nul
  if not errorlevel 1 set "PYEXE=py -3.12"
)
if not defined PYEXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYEXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYEXE (
  echo [ERRO] Python 3.12 x64 nao encontrado.
  echo Instale Python 3.12.10 x64 para o seu usuario e execute novamente.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando .venv...
  %PYEXE% -m venv .venv || exit /b 2
)

set "VPY=%CD%\.venv\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip setuptools wheel || exit /b 3
echo Instalando dependencias principais...
"%VPY%" -m pip install -r requirements.txt || exit /b 4

if not exist "Back-End\.env" (
  copy "Back-End\.env.example" "Back-End\.env" >nul || exit /b 5
  echo [INFO] Back-End\.env criado. Configure o MySQL antes de CRIAR_TABELAS.cmd.
) else (
  echo [OK] Back-End\.env existente preservado.
)

echo.
echo Validando o modo de deteccao disponivel...
"%VPY%" Back-End\validate_setup.py
if errorlevel 1 (
  echo.
  echo [ERRO] Ambiente instalado, mas a validacao do detector falhou.
  echo Veja a mensagem acima. Se quiser usar YOLO-World, rode INSTALAR_CLIP.cmd
  echo e coloque o peso yolov8s-worldv2.pt em Back-End\models.
  exit /b 6
)

echo.
echo [OK] Instalacao principal concluida.
echo Proximo passo: CRIAR_TABELAS.cmd
endlocal
