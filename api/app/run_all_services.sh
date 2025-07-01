#!/bin/bash
set -e # Salir inmediatamente si un comando falla

echo "==============================="
echo "Iniciando todos los servicios..."
echo "==============================="

# --- VERIFICACIÓN Y CARGA DE .env ---
if [ ! -f .env ]; then
    echo "[ERROR] Archivo .env no encontrado."
    exit 1
fi

# Carga todas las variables del .env al entorno del script Bash principal.
# Esto las hace disponibles para ser pasadas individualmente a cada servicio.
set -a # Habilita la exportación automática para todas las asignaciones
source ./.env # Lee y ejecuta el contenido del archivo .env
set +a # Deshabilita la exportación automática

# --- DEBUG: Verifica que las variables principales se cargaron ---
echo "DEBUG: Valor de EXTRACTOR_TOKEN: '$EXTRACTOR_TOKEN'"
echo "DEBUG: Valor de LLM_LED_TOKEN: '$LLM_LED_TOKEN'"
echo "DEBUG: Valor de ORCHESTRATOR_TOKEN: '$ORCHESTRATOR_TOKEN'"
echo "DEBUG: Valor de IS_LOCAL_MODEL: '$IS_LOCAL_MODEL'"
echo "DEBUG: Valor de MODEL_SELECTED_SERVICE1: '$MODEL_SELECTED_SERVICE1'"
# Agrega aquí cualquier otra variable global del .env que quieras verificar


# --- Función para iniciar un servicio de Uvicorn con variables específicas ---
# Cada servicio recibe su propio conjunto de variables de entorno.
start_uvicorn_service() {
    SERVICE_DIR=$1
    PORT=$2
    shift 2 # Elimina SERVICE_DIR y PORT de los argumentos, el resto son VAR=VAL

    echo ""
    echo "Iniciando ${SERVICE_DIR}..."
    if [ ! -d "$SERVICE_DIR" ]; then
        echo "[ERROR] Directorio '$SERVICE_DIR' no encontrado."
        exit 1
    fi

    cd "$SERVICE_DIR"
    echo "Carpeta actual: $(pwd)"

    if [ -f requirements.txt ]; then
        echo "Instalando dependencias..."
        pip install -r requirements.txt || { echo "[ERROR] Fallo al instalar dependencias para $SERVICE_DIR"; exit 1; }
    else
        echo "[ADVERTENCIA] requirements.txt no encontrado en $SERVICE_DIR. Continuando..."
    fi

    echo "Lanzando ${SERVICE_DIR} en segundo plano. Logs en ${SERVICE_DIR}.log..."
    # ¡LA SOLUCIÓN! Usar 'env' para pasar las variables a uvicorn
    nohup env "$@" uvicorn app.main:app --port "$PORT" --reload > "../${SERVICE_DIR}.log" 2>&1 &
    
    cd ..
}

# --- Iniciar Extractor Service ---
# Pasar EXTRACTOR_TOKEN como SERVICE_TOKEN para este proceso de uvicorn
start_uvicorn_service extractor_service 8001 \
    SERVICE_TOKEN="$EXTRACTOR_TOKEN"

# --- Iniciar LLM Service LED ---
# Pasar las variables específicas del LLM Service, incluyendo LLM_LED_TOKEN como SERVICE_TOKEN
start_uvicorn_service llm_service 8002 \
    IS_LOCAL_MODEL="$IS_LOCAL_MODEL" \
    SERVICE_TOKEN="$LLM_LED_TOKEN" \
    MODEL_SELECTED="$MODEL_SELECTED_SERVICE1" \
    MODEL_PATH="$MODEL_PATH_SERVICE1" \
    MAX_TOKENS_INPUT="$MAX_TOKENS_INPUT_SERVICE1" \
    MAX_TOKENS_OUTPUT="$MAX_TOKENS_OUTPUT_SERVICE1" \
    TRUNACTION="$TRUNACTION_SERVICE1" \
    SPECIAL_TOKENS_TREATMENT="$SPECIAL_TOKENS_TREATMENT_SERVICE1" \
    ERRORS_TREATMENT="$ERRORS_TREATMENT_SERVICE1" \
    QUANTIZATION="$QUANTIZATION_SERVICE1"

# --- Iniciar Orchestrator ---
# Pasar todas las variables que el Orchestrator necesita, incluyendo su propio SERVICE_TOKEN
start_uvicorn_service orchestrator 8000 \
    SERVICE_TOKEN="$ORCHESTRATOR_TOKEN" \
    EXTRACTOR_TOKEN="$EXTRACTOR_TOKEN" \
    LLM_LED_TOKEN="$LLM_LED_TOKEN" \
    EXTRACTOR_URL="$EXTRACTOR_URL" \
    LLM_LED_URL="$LLM_LED_URL" \
    IDENTIFIER_PATH_MODEL="$IDENTIFIER_PATH_MODEL" \
    IDENTIFIER_PATH_VECTORIZER="$IDENTIFIER_PATH_VECTORIZER"

echo ""
echo "Todos los servicios han sido lanzados en segundo plano."
echo "Puedes revisar sus logs en los archivos *.log en el directorio principal."
echo "Esperando 10 segundos para lanzar health checks..."
sleep 10

# --- Health Checks ---
echo "Ejecutando pruebas de integración..."
sleep 1
curl -s http://127.0.0.1:8000/health || echo "[ERROR] Orchestrator no responde"
sleep 1
curl -s http://127.0.0.1:8001/health || echo "[ERROR] Extractor no responde"
sleep 1
curl -s http://127.0.0.1:8002/health || echo "[ERROR] LLM Service no responde"

echo "DEBUG (Bash - curl): Sending Authorization: Bearer '$ORCHESTRATOR_TOKEN'"
echo ""
echo "Ejecutando test de integración entre servicios..."
sleep 1
# Este curl usa $ORCHESTRATOR_TOKEN del entorno principal del script
curl -s -H "Authorization: Bearer $ORCHESTRATOR_TOKEN" http://127.0.0.1:8000/test-integration || echo "[ERROR] Test de integración falló"

echo ""
echo "Pruebas de integración finalizadas."
echo "Para detener los servicios, usa 'pkill -f uvicorn' o 'kill' los PIDs específicos (ver logs)."