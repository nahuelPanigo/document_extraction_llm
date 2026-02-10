# Scripts & Run Modules

All scripts live at the **root level** of the repository.

## Main Entry Point

### `run_modules.sh` / `run_modules.bat`

Unified runner to execute any module of the project. Each module runs in its own isolated virtual environment (`.venv-{mode}`).

```bash
./run_modules.sh <mode> [--python PYTHON_EXE] [--reinstall]
```

### Available Modes

| Mode | Module | Description |
|------|--------|-------------|
| `make_dataset` | `download_prepare_clean_normalize_sedici_dataset/` | Full data preparation pipeline |
| `fine_tunning` | `fine_tunning/` | Fine-tune the LLM model |
| `fine_tune_type` | `fine_tune_type/` | Train document type classifier |
| `fine_tune_subject` | `fine_tune_subject/` | Train subject classifier |
| `validation` | `validation/` | Run validation against test dataset |

### Options

| Flag | Description |
|------|-------------|
| `--python` | Specify Python executable (default: `python3`) |
| `--reinstall` | Recreate virtual environment and reinstall dependencies |

### Example Usage

```bash
# Prepare the dataset
./run_modules.sh make_dataset

# Fine-tune the model
./run_modules.sh fine_tunning

# Train subject classifier
./run_modules.sh fine_tune_subject

# Use specific Python version and force reinstall
./run_modules.sh fine_tunning --python python3.10 --reinstall
```

### What Each Mode Does

1. Creates a virtual environment `.venv-{mode}` if it doesn't exist
2. Installs dependencies from the module's `requirements.txt`
3. Runs the module's `main.py`

## API Scripts

### `api/app/run_all_services.sh` / `.bat`

Starts all API microservices **locally without Docker** using uvicorn:

```bash
cd api/app
./run_all_services.sh
```

See [API documentation](api/index.md) for details on Docker vs local execution.

## Environment Variables

All scripts read from the root `.env` file:

| Variable | Used By |
|----------|---------|
| `GOOGLE_API_KEY` | `make_dataset` (Gemini API) |
| `TOKEN_HUGGING_FACE` | `fine_tunning` (model download) |
| `ORCHESTRATOR_TOKEN` | `validation` (API authentication) |
| `EXTRACTOR_TOKEN` | API (service auth) |
| `LLM_LED_TOKEN` | API (service auth) |
| `MODEL_SELECTED` | API (which LLM to load) |
| `MODEL_PATH` | API (fine-tuned model path) |
