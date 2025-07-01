@echo off
setlocal enabledelayedexpansion

:: Ir a la raíz del proyecto (asume que el .bat está en la carpeta del servicio)
cd /d "%~dp0\.."

:: Cargar el archivo .env manualmente línea por línea
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "line=%%A"
    if not "!line!"=="" (
        set "value=%%B"
        set "!line!=!value!"
    )
)

:: Volver a la carpeta del servicio
cd /d "%~dp0"

:: Asignar SERVICE_TOKEN desde LLM_LED_TOKEN
set SERVICE_TOKEN=%LLM_LED_TOKEN%

:: Asignar variables específicas del servicio
set MODEL_SELECTED=%MODEL_SELECTED_SERVICE1%
set MODEL_PATH=%MODEL_PATH_SERVICE1%
set MAX_TOKENS_INPUT=%MAX_TOKENS_INPUT_SERVICE1%
set MAX_TOKENS_OUTPUT=%MAX_TOKENS_OUTPUT_SERVICE1%
set TRUNACTION=%TRUNACTION_SERVICE1%
set SPECIAL_TOKENS_TREATMENT=%SPECIAL_TOKENS_TREATMENT_SERVICE1%
set ERRORS_TREATMENT=%ERRORS_TREATMENT_SERVICE1%
set QUANTIZATION=%QUANTIZATION_SERVICE1%

:: Verificar existencia del modelo
if not exist "%MODEL_PATH%" (
    echo ❌ Error: El modelo no existe en la ruta %MODEL_PATH%
    exit /b 1
)

:: Ejecutar el servicio
uvicorn app.main:app --port 8002 --reload

endlocal
