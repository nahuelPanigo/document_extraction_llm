@echo off
setlocal enabledelayedexpansion

:: Ir a la raíz del proyecto
cd /d "%~dp0\.."

:: Cargar variables desde el archivo .env
if not exist .env (
    echo [ERROR] Archivo .env no encontrado en la raíz del proyecto.
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "line=%%A"
    if not "!line!"=="" (
        set "value=%%B"
        set "!line!=!value!"
    )
)

:: Volver al directorio del servicio orchestrator
cd /d "%~dp0"

:: Asignar variables de entorno requeridas
set SERVICE_TOKEN=%ORCHESTRATOR_TOKEN%
set EXTRACTOR_TOKEN=%EXTRACTOR_TOKEN%
set LLM_LED_TOKEN=%LLM_LED_TOKEN%
set EXTRACTOR_URL=%EXTRACTOR_URL%
set LLM_LED_URL=%LLM_LED_URL%
set IDENTIFIER_PATH_MODEL=%IDENTIFIER_PATH_MODEL%
set IDENTIFIER_PATH_VECTORIZER=%IDENTIFIER_PATH_VECTORIZER%

:: Ejecutar el servicio
uvicorn app.main:app --port 8000 --reload

endlocal
