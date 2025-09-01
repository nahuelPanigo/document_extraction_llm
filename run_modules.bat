@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: -----------------------------
:: Usage / help
:: -----------------------------
set "MODE=%~1"
if /I "%MODE%"=="" goto :help
if /I "%MODE%"=="-h" goto :help
if /I "%MODE%"=="--help" goto :help

:: Shift the mode argument out
shift

set "PY_EXE="
set "REINSTALL=false"

:: -----------------------------
:: Parse optional flags
:: -----------------------------
:parse
if "%~1"=="" goto :post_parse

if /I "%~1"=="--python" (
  if "%~2"=="" (
    echo [ERROR] --python requires an argument (e.g. --python python.exe)
    exit /b 1
  )
  set "PY_EXE=%~2"
  shift
  shift
  goto :parse
) else if /I "%~1"=="--reinstall" (
  set "REINSTALL=true"
  shift
  goto :parse
) else (
  echo [ERROR] Unknown option: %~1
  goto :help
)

:post_parse

:: -----------------------------
:: Pick a Python interpreter
:: -----------------------------
if not defined PY_EXE (
  for %%P in (py python python3) do (
    where "%%P" >nul 2>nul
    if not errorlevel 1 (
      set "PY_EXE=%%P"
      goto :found_python
    )
  )
  echo [ERROR] No Python interpreter found on PATH. Install Python and try again.
  exit /b 1
) else (
  where "%PY_EXE%" >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python executable not found: "%PY_EXE%".
    echo Check your Python installation or provide a valid path.
    exit /b 1
  )
)

:found_python
echo Using Python executable: "%PY_EXE%"

:: -----------------------------
:: Map mode -> submodule + req
:: -----------------------------
set "SUBMODULE="
set "SUBREQ="

if /I "%MODE%"=="fine_tunning" (
  set "SUBMODULE=fine_tunning"
  set "SUBREQ=fine_tunning\requirements.txt"
  goto :after_mode
)

if /I "%MODE%"=="make_dataset" (
  set "SUBMODULE=download_prepare_clean_normalize_sedici_dataset"
  set "SUBREQ=download_prepare_clean_normalize_sedici_dataset\requirements.txt"
  goto :after_mode
)

if /I "%MODE%"=="validation" (
  set "SUBMODULE=validation"
  set "SUBREQ=validation\requirements.txt"
  goto :after_mode
)

if /I "%MODE%"=="fine_tune_type" (
  set "SUBMODULE=fine_tune_type"
  set "SUBREQ=fine_tune_type\requirements.txt"
  goto :after_mode
)

if /I "%MODE%"=="fine_tune_subject" (
  set "SUBMODULE=fine_tune_subject"
  set "SUBREQ=fine_tune_subject\requirements.txt"
  goto :after_mode
)

echo [ERROR] Unknown mode: %MODE%
goto :help

:after_mode

:: -----------------------------
:: Sanity checks
:: -----------------------------
if not exist "%SUBMODULE%\" (
  echo [ERROR] Run this script from the repo ROOT. The "%SUBMODULE%" directory was not found.
  exit /b 1
)

:: -----------------------------
:: Venv per mode
:: -----------------------------
set "VENV_DIR=.venv-%MODE%"
set "VENV_ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat"
set "PYTHON_IN_VENV=%VENV_DIR%\Scripts\python.exe"
set "PIP_IN_VENV=%VENV_DIR%\Scripts\pip.exe"

if /I "%REINSTALL%"=="true" (
  if exist "%VENV_DIR%\" (
    echo Removing existing venv "%VENV_DIR%" ...
    rmdir /s /q "%VENV_DIR%"
  )
)

if not exist "%VENV_DIR%\" (
  echo Creating virtualenv: %VENV_DIR%
  "%PY_EXE%" -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] Failed to create virtualenv. Check your Python installation.
    exit /b 1
  )
)

:: -----------------------------
:: Activate venv
:: -----------------------------
call "%VENV_ACTIVATE_SCRIPT%"
if errorlevel 1 (
  echo [ERROR] Failed to activate virtualenv.
  exit /b 1
)

:: -----------------------------
:: Install requirements
:: -----------------------------
echo Upgrading pip / setuptools / wheel ...
"%PYTHON_IN_VENV%" -m pip install --upgrade pip setuptools wheel

if exist "requirements.txt" (
  echo Installing root requirements.txt ...
  "%PIP_IN_VENV%" install -r requirements.txt
)

if exist "%SUBREQ%" (
  echo Installing %SUBREQ% ...
  "%PIP_IN_VENV%" install -r "%SUBREQ%"
) else (
  echo [WARN] %SUBREQ% not found. Skipping submodule-specific requirements.
)

:: Optional: pin versions via environment variables before run
if defined PIN_TRANSFORMERS (
  echo Pinning transformers==%PIN_TRANSFORMERS%
  "%PIP_IN_VENV%" install "transformers==%PIN_TRANSFORMERS%"
)
if defined PIN_PEFT (
  echo Pinning peft==%PIN_PEFT%
  "%PIP_IN_VENV%" install "peft==%PIN_PEFT%"
)
if defined PIN_TORCH (
  echo Pinning torch==%PIN_TORCH%
  "%PIP_IN_VENV%" install "torch==%PIN_TORCH%"
)

:: -----------------------------
:: Run
:: -----------------------------
echo Running: "%PYTHON_IN_VENV%" "%SUBMODULE%\main.py"
set "PYTHONPATH=%CD%;%PYTHONPATH%"
"%PYTHON_IN_VENV%" "%SUBMODULE%\main.py"
exit /b %errorlevel%

:help
echo.
echo Usage:
echo   run_modules.bat ^<mode^> [--python PY_EXE] [--reinstall]
echo.
echo Modes:
echo   fine_tunning        -> runs fine_tunning\main.py
echo   make_dataset        -> runs download_prepare_clean_normalize_sedici_dataset\main.py
echo   validation          -> runs validation\main.py
echo   fine_tune_type      -> runs fine_tune_type\main.py
echo   fine_tune_subject   -> runs fine_tune_subject\main.py
echo.
echo Options:
echo   --python PY_EXE     Choose python executable (e.g. python, "C:\Python312\python.exe", py)
echo   --reinstall         Remove and recreate the mode-specific venv
echo.
echo Examples:
echo   run_modules.bat fine_tunning
echo   run_modules.bat make_dataset --python py
echo   run_modules.bat fine_tunning --reinstall
echo.
exit /b 1