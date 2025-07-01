#!/bin/bash

# Ir a la raíz del proyecto (una carpeta arriba)
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Cargar el .env desde la raíz
set -a
source "$ROOT_DIR/.env"
set +a

# Asignar SERVICE_TOKEN desde EXTRACTOR_TOKEN
export SERVICE_TOKEN="$ORCHESTRATOR_TOKEN"
export EXTRACTOR_TOKEN="$EXTRACTOR_TOKEN"
export LLM_LED_TOKEN="$LLM_LED_TOKEN"
export EXTRACTOR_URL="$EXTRACTOR_URL"
export LLM_LED_URL="$LLM_LED_URL"
export IDENTIFIER_PATH_MODEL="$IDENTIFIER_PATH_MODEL"
export IDENTIFIER_PATH_VECTORIZER="$IDENTIFIER_PATH_VECTORIZER"

# Ejecutar el servicio
uvicorn app.main:app --port 8000 --reload
