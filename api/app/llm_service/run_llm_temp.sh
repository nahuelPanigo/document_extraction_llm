#!/bin/bash

# Navega a la raíz del proyecto donde está el .env
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Cargar variables del .env raíz
set -a
source "$ROOT_DIR/.env"
set +a

# Asignar SERVICE_TOKEN desde variable general
export SERVICE_TOKEN="$LLM_LED_TOKEN"

# Asignar las variables específicas del servicio LED
export MODEL_SELECTED="$MODEL_SELECTED_SERVICE1"
export MODEL_PATH="$MODEL_PATH_SERVICE1"
export MAX_TOKENS_INPUT="$MAX_TOKENS_INPUT_SERVICE1"
export MAX_TOKENS_OUTPUT="$MAX_TOKENS_OUTPUT_SERVICE1"
export TRUNACTION="$TRUNACTION_SERVICE1"
export SPECIAL_TOKENS_TREATMENT="$SPECIAL_TOKENS_TREATMENT_SERVICE1"
export ERRORS_TREATMENT="$ERRORS_TREATMENT_SERVICE1"
export QUANTIZATION="$QUANTIZATION_SERVICE1"

# Después (ajusta al path real desde el script)
if [ ! -d "./app/$MODEL_PATH" ]; then
  echo "❌ Error: El modelo no existe en la ruta ./app/$MODEL_PATH"
  exit 1
fi

# Ejecutar el servicio
uvicorn app.main:app --port 8002 --reload