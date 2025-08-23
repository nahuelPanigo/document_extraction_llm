@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: -----------------------------
:: Usage / help
:: -----------------------------
if "%~1"=="" goto :help
if "%~1"=="-h" goto :help
if "%~1"=="--help" goto :help

set "MODE=%~1"
shift

:: Defaults
set "PY_EXE="
set "REINSTALL=false"

:: -----------------------------
:: Parse optional flags
::   --python <exe>
::   --reinstall
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
  where py >nul 2>nul
  if %errorlevel%==0 (
    set "PY_EXE=py"
  ) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
      set "PY_EXE=python"
    ) else (
      echo [ERROR] No Python interpreter found on PATH. Install Python and try again.
      exit /b 1
    )
  )
)

:: -----------------------------
:: Map mode -> submodule + req
:: -----------------------------
set "SUBMODULE="
set "SUBREQ="

if /I "%MODE%"=="fine_tunning" (
  set "SUBMODULE=document_metadata_extraction.fine_tunning"
  set "SUBREQ=document_metadata_extraction\fine_tunning\requirements.txt"
) else if /I "%MODE%"=="make_dataset" (
  set "SUBMODULE=document_metadata_extraction.download_prepare_clean_normalize_sedici_dataset"
  set "SUBREQ=document_metadata_extraction\download_prepare_clean_normalize_sedici_dataset\requirements.txt"
) else if /I "%MODE%"=="validation" (
  echo future_todo
  exit /b 0
) else if /I "%MODE%"=="fine_tune_type" (
  echo future_todo
  exit /b 0
) else if /I "%MODE%"=="fine_tune_subject" (
  echo future_todo
  exit /b 0
) else (
  echo [ERROR] Unknown mode: %MODE%
  goto :help
)

:: -----------------------------
:: Sanity checks
:: -----------------------------
if not exist "document_metadata_extraction\" (
  echo [ERROR] Run this script from the repo ROOT (where "document_metadata_extraction\" exists).
  exit /b 1
)

:: -----------------------------
:: Venv per mode
:: -----------------------------
set "VENV_DIR=.venv-%MODE%"

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
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Failed to activate virtualenv.
  exit /b 1
)

:: -----------------------------
:: Install requirements
:: - upgrade pip/setuptools/wheel
:: - root requirements.txt (optional)
:: - submodule requirements (if present)
:: -----------------------------
echo Upgrading pip / setuptools / wheel ...
python -m pip install --upgrade pip setuptools wheel

if exist "requirements.txt" (
  echo Installing root requirements.txt ...
  python -m pip install -r requirements.txt
)

if exist "%SUBREQ%" (
  echo Installing %SUBREQ% ...
  python -m pip install -r "%SUBREQ%"
) else (
  echo [WARN] %SUBREQ% not found. Skipping submodule-specific requirements.
)

:: Optional: pin versions via environment variables before run
:: Example (in CMD before calling run.bat):
::   set PIN_TRANSFORMERS=4.42.3
::   set PIN_PEFT=0.12.0
::   set PIN_TORCH=2.3.1
if defined PIN_TRANSFORMERS (
  echo Pinning transformers==%PIN_TRANSFORMERS%
  python -m pip install "transformers==%PIN_TRANSFORMERS%"
)
if defined PIN_PEFT (
  echo Pinning peft==%PIN_PEFT%
  python -m pip install "peft==%PIN_PEFT%"
)
if defined PIN_TORCH (
  echo Pinning torch==%PIN_TORCH%
  python -m pip install "torch==%PIN_TORCH%"
)

:: -----------------------------
:: Run
:: -----------------------------
echo Running: python -m %SUBMODULE%.main
python -m %SUBMODULE%.main
exit /b %errorlevel%

:help
echo.
echo Usage:
echo   run.bat ^<mode^> [--python PY_EXE] [--reinstall]
echo.
echo Modes:
echo   fine_tunning        -> runs document_metadata_extraction\fine_tunning\main.py
echo   make_dataset        -> runs document_metadata_extraction\download_prepare_clean_normalize_sedici_dataset\main.py
echo   validation          -> future_todo
echo   fine_tune_type      -> future_todo
echo   fine_tune_subject   -> future_todo
echo.
echo Options:
echo   --python PY_EXE     Choose python executable (e.g. python, "C:\Python312\python.exe", py)
echo   --reinstall         Remove and recreate the mode-specific venv
echo.
echo Examples:
echo   run.bat fine_tunning
echo   run.bat make_dataset --python py
echo   run.bat fine_tunning --reinstall
echo.
exit /b 1
