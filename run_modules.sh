#!/usr/bin/env bash
set -euo pipefail

# Usage help
usage() {
  cat <<'EOF'
Usage:
  ./run.sh <mode> [--python PYTHON_EXE] [--reinstall]

Modes:
  fine_tunning           -> uses document_metadata_extraction/fine_tunning
  make_dataset           -> uses document_metadata_extraction/download_prepare_clean_normalize_sedici_dataset
  validation             -> future_todo
  fine_tune_type         -> future_todo
  fine_tune_subject      -> future_todo

Options:
  --python PYTHON_EXE    Choose python executable (default: python3, fallback: python)
  --reinstall            If venv exists, wipe and recreate it

Examples:
  ./run.sh fine_tunning
  ./run.sh make_dataset --python python3.12
  ./run.sh fine_tunning --reinstall
EOF
}

# ---- parse args ----
MODE="${1:-}"
if [[ -z "${MODE}" || "${MODE}" == "-h" || "${MODE}" == "--help" ]]; then
  usage; exit 0
fi
shift || true

PY_EXE="python3"
REINSTALL="false"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) PY_EXE="${2:-}"; shift 2 ;;
    --reinstall) REINSTALL="true"; shift ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

# Fallback to 'python' if python3 isn't available
if ! command -v "${PY_EXE}" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PY_EXE="python"
  else
    echo "No python interpreter found. Install Python and try again." >&2
    exit 1
  fi
fi

# ---- map mode -> submodule + req file ----
SUBMODULE=""
SUBREQ=""
case "${MODE}" in
  fine_tunning)
    SUBMODULE="document_metadata_extraction.fine_tunning"
    SUBREQ="document_metadata_extraction/fine_tunning/requirements.txt"
    ;;
  make_dataset)
    SUBMODULE="document_metadata_extraction.download_prepare_clean_normalize_sedici_dataset"
    SUBREQ="document_metadata_extraction/download_prepare_clean_normalize_sedici_dataset/requirements.txt"
    ;;
  validation|fine_tune_type|fine_tune_subject)
    echo "future_todo"
    exit 0
    ;;
  *)
    echo "Unknown mode: ${MODE}"; usage; exit 1
    ;;
esac

# ---- sanity checks ----
if [[ ! -d "document_metadata_extraction" ]]; then
  echo "Run this script from the REPO ROOT (where 'document_metadata_extraction/' lives)." >&2
  exit 1
fi

# Ensure package structure (warn only)
for pkg in "document_metadata_extraction" \
           "document_metadata_extraction/${SUBMODULE##document_metadata_extraction.}"; do
  pkg_path="${pkg//./\/}"
  if [[ ! -f "${pkg_path}/__init__.py" ]]; then
    echo "Warning: missing ${pkg_path}/__init__.py (Python package best practice)." >&2
  fi
done

# ---- venv name per mode ----
VENV_DIR=".venv-${MODE}"

# Recreate if requested
if [[ -d "${VENV_DIR}" && "${REINSTALL}" == "true" ]]; then
  echo "Removing existing venv ${VENV_DIR} ..."
  rm -rf "${VENV_DIR}"
fi

# Create venv if missing
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Creating virtualenv: ${VENV_DIR}"
  "${PY_EXE}" -m venv "${VENV_DIR}"
fi

# Activate venv
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

# Upgrade pip
python -m pip install --upgrade pip wheel setuptools

# Install requirements: root (optional) + submodule
if [[ -f "requirements.txt" ]]; then
  echo "Installing root requirements.txt ..."
  pip install -r requirements.txt
fi

if [[ -f "${SUBREQ}" ]]; then
  echo "Installing ${SUBREQ} ..."
  pip install -r "${SUBREQ}"
else
  echo "Warning: ${SUBREQ} not found. Skipping submodule-specific requirements." >&2
fi

# Optional: pin known-compatible versions if present in env vars
# Example to force pins on CI:
#   export PIN_TRANSFORMERS=4.42.3 PIN_PEFT=0.12.0 PIN_TORCH=2.3.1
if [[ -n "${PIN_TRANSFORMERS:-}" || -n "${PIN_PEFT:-}" || -n "${PIN_TORCH:-}" ]]; then
  [[ -n "${PIN_TRANSFORMERS:-}" ]] && pip install "transformers==${PIN_TRANSFORMERS}"
  [[ -n "${PIN_PEFT:-}" ]]         && pip install "peft==${PIN_PEFT}"
  [[ -n "${PIN_TORCH:-}" ]]        && pip install "torch==${PIN_TORCH}"
fi

# ---- run the module ----
echo "Running: python -m ${SUBMODULE}.main"
exec python -m "${SUBMODULE}.main"
