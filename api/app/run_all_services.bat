@echo off
setlocal enabledelayedexpansion

echo ===============================
echo Iniciando todos los servicios...
echo ===============================

REM Cargar variables de entorno desde .env
if exist .env (
    for /f "usebackq tokens=* delims=" %%i in (".env") do set "%%i"
) else (
    echo [ERROR] Archivo .env no encontrado.
    exit /b 1
)

REM -------- Extractor Service --------
echo.
echo Iniciando extractor_service...
cd extractor_service
echo Carpeta actual: %cd%

if exist requirements.txt (
    echo Instalando dependencias...
    pip install -r requirements.txt
) else (
    echo [ERROR] requirements.txt no encontrado en extractor_service
)

REM Crear script temporal para lanzar el servicio
echo set SERVICE_TOKEN=%EXTRACTOR_TOKEN%> run_extractor_temp.bat
echo uvicorn app.main:app --port 8001 --reload>> run_extractor_temp.bat
start run_extractor_temp.bat
cd ..

REM -------- LLM Service LED --------
echo.
echo Iniciando llm_service_led...
cd llm_service
echo Carpeta actual: %cd%

if exist requirements.txt (
    echo Instalando dependencias...
    pip install -r requirements.txt
) else (
    echo [ERROR] requirements.txt no encontrado en llm_service
)
echo set IS_LOCAL_MODEL=%IS_LOCAL_MODEL%> run_llm_temp.bat
echo set SERVICE_TOKEN=%LLM_LED_TOKEN%> run_llm_temp.bat
echo set MODEL_SELECTED=%MODEL_SELECTED_SERVICE1%>> run_llm_temp.bat
echo set MODEL_PATH=%MODEL_PATH_SERVICE1%>> run_llm_temp.bat
echo set MAX_TOKENS_INPUT=%MAX_TOKENS_INPUT_SERVICE1%>> run_llm_temp.bat
echo set MAX_TOKENS_OUTPUT=%MAX_TOKENS_OUTPUT_SERVICE1%>> run_llm_temp.bat
echo set TRUNACTION=%TRUNACTION_SERVICE1%>> run_llm_temp.bat
echo set SPECIAL_TOKENS_TREATMENT=%SPECIAL_TOKENS_TREATMENT_SERVICE1%>> run_llm_temp.bat
echo set ERRORS_TREATMENT=%ERRORS_TREATMENT_SERVICE1%>> run_llm_temp.bat
echo set QUANTIZATION=%QUANTIZATION_SERVICE1%>> run_llm_temp.bat
echo uvicorn app.main:app --port 8002 --reload>> run_llm_temp.bat
start run_llm_temp.bat
cd ..

REM -------- Orchestrator --------
echo.
echo Iniciando orchestrator...
cd orchestrator
echo Carpeta actual: %cd%

if exist requirements.txt (
    echo Instalando dependencias...
    pip install -r requirements.txt
) else (
    echo [ERROR] requirements.txt no encontrado en orchestrator
)

echo set SERVICE_TOKEN=%ORCHESTRATOR_TOKEN%> run_orchestrator_temp.bat
echo set EXTRACTOR_TOKEN=%EXTRACTOR_TOKEN%>> run_orchestrator_temp.bat
echo set LLM_LED_TOKEN=%LLM_LED_TOKEN%>> run_orchestrator_temp.bat
echo set EXTRACTOR_URL=%EXTRACTOR_URL%>> run_orchestrator_temp.bat
echo set LLM_LED_URL=%LLM_LED_URL%>> run_orchestrator_temp.bat
echo set IDENTIFIER_PATH_MODEL=%IDENTIFIER_PATH_MODEL%>> run_orchestrator_temp.bat
echo set IDENTIFIER_PATH_VECTORIZER=%IDENTIFIER_PATH_VECTORIZER%>> run_orchestrator_temp.bat
echo uvicorn app.main:app --port 8000 --reload>> run_orchestrator_temp.bat
start run_orchestrator_temp.bat
cd ..

REM ---------- Health Checks ----------
echo.
echo Todos los servicios fueron lanzados (ver ventanas individuales).
echo Esperando 10 segundos para lanzar health checks...
timeout /t 10 >nul

echo Ejecutando pruebas de integración...
curl -s http://127.0.0.1:8000/health || echo [ERROR] Orchestrator no responde
curl -s http://127.0.0.1:8001/health || echo [ERROR] Extractor no responde
curl -s http://127.0.0.1:8002/health || echo [ERROR] LLM Service no responde

echo.
echo Ejecutando test de integración entre servicios...
curl -s -H "Authorization: Bearer %ORCHESTRATOR_TOKEN%" http://127.0.0.1:8000/test-integration || echo [ERROR] Test de integración falló

echo.
echo Pruebas de integración finalizadas.
pause
