#!/bin/bash
set -e

echo "==============================="
echo "Iniciando todos los servicios..."
echo "==============================="

if [ ! -f .env ]; then
    echo "[ERROR] Archivo .env no encontrado."
    exit 1
fi
export $(grep -v '^#' .env | xargs)

echo ""
echo "Iniciando extractor_service..."
cd extractor_service
echo "Carpeta actual: $(pwd)"

if [ -f requirements.txt ]; then
    echo "Instalando dependencias..."
    pip install -r requirements.txt
else
    echo "[ERROR] requirements.txt no encontrado en extractor_service"
fi

echo "Lanzando extractor_service..."
uvicorn app.main:app --port 8001 --reload &
cd ..

echo ""
echo "Iniciando llm_service_led..."
cd llm_service
echo "Carpeta actual: $(pwd)"

if [ -f requirements.txt ]; then
    echo "Instalando dependencias..."
    pip install -r requirements.txt
else
    echo "[ERROR] requirements.txt no encontrado en llm_service"
fi

echo "Lanzando llm_service_led..."
uvicorn app.main:app --port 8002 --reload &
cd ..

echo ""
echo "Iniciando orchestrator..."
cd orchestrator
echo "Carpeta actual: $(pwd)"

if [ -f requirements.txt ]; then
    echo "Instalando dependencias..."
    pip install -r requirements.txt
else
    echo "[ERROR] requirements.txt no encontrado en orchestrator"
fi

echo "Lanzando orchestrator..."
uvicorn app.main:app --port 8000 --reload &
cd ..

echo ""
echo "Esperando 10 segundos para lanzar health checks..."
sleep 10

echo "Ejecutando pruebas de integración..."
curl -s http://127.0.0.1:8000/health || echo "[ERROR] Orchestrator no responde"
curl -s http://127.0.0.1:8001/health || echo "[ERROR] Extractor no responde"
curl -s http://127.0.0.1:8002/health || echo "[ERROR] LLM Service no responde"

echo ""
echo "Ejecutando test de integración entre servicios..."

curl -s -H "Authorization: Bearer $ORCHESTRATOR_TOKEN" http://127.0.0.1:8000/test-integration || echo "[ERROR] Test de integración falló"

echo "Pruebas de integración finalizadas."
