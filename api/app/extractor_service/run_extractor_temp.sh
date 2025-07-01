#!/bin/bash

# Ir a la raíz del proyecto (una carpeta arriba)
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Cargar el .env desde la raíz
set -a
source "$ROOT_DIR/.env"
set +a

# Asignar SERVICE_TOKEN desde EXTRACTOR_TOKEN
export SERVICE_TOKEN="$EXTRACTOR_TOKEN"

# Ejecutar el servicio en el puerto 8001
uvicorn app.main:app --port 8001 --reload
