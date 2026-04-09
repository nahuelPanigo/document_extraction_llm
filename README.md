# Document Metadata Extraction with LLM

Automatic extraction of bibliographic metadata from academic documents (theses, articles, books, conference objects) using fine-tuned language models. Built around the **SEDICI** repository at Universidad Nacional de La Plata.

Given an academic PDF, the system extracts structured metadata (title, authors, date, language, type-specific fields) by combining a fine-tuned LLM with ML classifiers for document type and subject.

```
SEDICI CSV → Dataset (2000 docs) → Fine-Tuned LLM + Classifiers → API → Metadata JSON
```

> Full documentation: **[nahuelPanigo.github.io/document_extraction_llm](https://nahuelPanigo.github.io/document_extraction_llm/)** — or run `mkdocs serve` locally (requires `pip install mkdocs-material`).

---

## Project Layout

| Folder | Description |
|--------|-------------|
| `api/` | FastAPI microservices: Orchestrator, Extractor, LLM Service |
| `download_prepare_clean_normalize_sedici_dataset/` | Data pipeline: download, extract text, clean metadata with LLM |
| `fine_tunning/` | LLM fine-tuning (LED, LLAMA, GEMMA, Mistral, etc.) |
| `fine_tune_type/` | Document type classifier (Libro, Tesis, Articulo, Objeto de conferencia) |
| `fine_tune_subject/` | Subject classifier (SVM, XGBoost, etc.) |
| `validation/` | Model evaluation against ground truth |
| `utils/` | Shared utilities: text extraction, normalization, ML strategies |
| `data/` | CSVs, PDFs, extracted texts, JSONs |
| `constants.py` | Global config: prompts, model paths, field mappings, API limits |

---

## Running Modules

Use the provided scripts to run any module with automatic virtual environment management:

```bash
# Linux/Mac
./run_modules.sh <mode> [--python PYTHON_EXE] [--reinstall]

# Windows
run_modules.bat <mode> [--python PY_EXE] [--reinstall]
```

### Modes (run in order)

| Step | Mode | What it does |
|------|------|-------------|
| 1 | `make_dataset` | Download PDFs, extract text, clean metadata with Gemini/OpenAI |
| 2 | `fine_tunning` | Fine-tune the LLM on the prepared dataset |
| 3 | `validation` | Evaluate the model via the running API |
| — | `fine_tune_type` | Train document type classifier (independent) |
| — | `fine_tune_subject` | Train subject classifier (independent) |

```bash
./run_modules.sh make_dataset
./run_modules.sh fine_tunning
./run_modules.sh validation

# Optional classifiers
./run_modules.sh fine_tune_type
./run_modules.sh fine_tune_subject

# Use a specific Python version and force reinstall
./run_modules.sh fine_tunning --python python3.10 --reinstall
```

> Details on each module: [docs/scripts.md](docs/scripts.md)

---

## Environment Variables

Create a `.env` file at the root (see `.env.example` files in each module folder):

| Variable | Required by |
|----------|-------------|
| `GOOGLE_API_KEY` | `make_dataset` (Gemini API) |
| `TOKEN_HUGGING_FACE` | `fine_tunning` (model download) |
| `ORCHESTRATOR_TOKEN` | `validation` + API auth |
| `EXTRACTOR_TOKEN` | API — Extractor service |
| `LLM_LED_TOKEN` | API — LLM service |

---

## Running the API

The API has three services: **Orchestrator** (port 8000), **Extractor** (8001), and **LLM Service** (8002). An optional fourth service (DeepAnalyze, 8003) can validate results using a larger model.

### With Docker Compose (recommended)

```bash
cd api/app

# Standard (3 services)
docker compose up

# With optional DeepAnalyze service
ENABLE_QWEN_SERVICE=true docker compose --profile qwen up
```

### Without Docker

```bash
cd api/app
./run_all_services.sh    # Linux/Mac
run_all_services.bat     # Windows
```

### Uploading a Document

```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer $ORCHESTRATOR_TOKEN" \
  -F "file=@document.pdf"
```

Returns a structured metadata JSON with title, authors, date, type, subject, and type-specific fields.

> Full API reference: [docs/api/index.md](docs/api/index.md)
