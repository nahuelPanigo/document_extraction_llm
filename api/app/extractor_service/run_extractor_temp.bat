@echo off
setlocal enabledelayedexpansion

:: Ir a la raíz del proyecto
cd /d "%~dp0\.."

:: Cargar el .env desde la raíz del proyecto
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "line=%%A"
    if not "!line!"=="" (
        set "value=%%B"
        set "!line!=!value!"
    )
)

:: Volver a la carpeta del servicio extractor
cd /d "%~dp0"

:: Asignar SERVICE_TOKEN desde EXTRACTOR_TOKEN
set SERVICE_TOKEN=%EXTRACTOR_TOKEN%

:: Ejecutar el servicio
uvicorn app.main:app --port 8001 --reload

endlocal
