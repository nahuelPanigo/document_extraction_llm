# Validation

This module evaluates the whole metadata extraction pipeline by comparing predicted metadata against ground truth. There are 3 separate validation scripts, one for each extraction approach, plus a metric checker dashboard (FastAPI + React) for visualizing results.

## Validation Scripts

There is no single `main.py`. Instead, there are 3 independent scripts, each validating a different extraction method:

| Script | What it validates |
|--------|-------------------|
| `validation_finetunning.py` | Our fine-tuned model (via the API) |
| `validation_grobid.py` | GROBID-based extraction |
| `validation_langsmith.py` | Cloud LLM extraction (OpenAI, Gemini, etc.) |

Each script:

1. Takes documents from the test dataset
2. Extracts metadata using its respective method
3. Compares predictions with ground truth
4. Saves results to its own subfolder inside `result/`

## Results Structure

```
validation/result/
├── original_metadata.json          # Ground truth (stays at root level)
├── extracted_metadata.json         # General extracted results
├── FINETUNNED/                     # Fine-tuned model results
├── GROBID/                         # GROBID results
├── CLOUDLLM/                       # Cloud LLM results (OpenAI, Gemini, etc.)
└── LEDEN/                          # LED model results
```

## Metric Checker Dashboard

A **FastAPI** backend + **React** frontend application for visualizing and comparing validation results.

### How to Run

```bash
# Backend (FastAPI)
cd validation/backend/metric-checker
python index.py   # Starts on port 8000

# Frontend (React)
cd validation/frontend/metric-checker
npm start          # Starts on port 3000
```

### How it Works

1. Upload two JSON files via the frontend: **original** (ground truth) and **predicted** (model output)
2. The backend compares them using the `MetricChecker` class
3. Results are displayed as interactive charts

### Metrics Computed

The `MetricChecker` runs three types of checks:

**Exact Equality**

- Compares each field value directly (with text normalization: lowercase, accent removal, whitespace cleanup)
- Special handling for name fields (creator, director, codirector): word-by-word comparison regardless of order (e.g. "Andrea Orsatti" matches "Orsatti, Andrea")
- Reports: accuracy, total matches, mismatches per field

**F1 Score**

- TP: Model extracted a value AND it matches ground truth
- FN: Ground truth has a value BUT model extracted nothing
- FP: Model extracted an incorrect value or hallucinated
- Reports: precision, recall, F1 score per field

**List Percentage Match**

- For list-type fields (creator, subject, keywords, etc.)
- Calculates Jaccard similarity between predicted and real lists
- Reports: average match percentage, perfect matches, missing/extra elements

### Results Breakdown

All metrics are computed at two levels:

- **General**: Across all documents regardless of type
- **Per document type**: Separate metrics for Tesis, Libro, Articulo, Objeto de conferencia

Type-specific fields (e.g. `director` for Tesis, `isbn` for Libro) are only evaluated against documents of the relevant type.

### Frontend Components

| Component | Description |
|-----------|-------------|
| `FileUpload.tsx` | Upload original and predicted JSON files |
| `MetricsVisualization.tsx` | Main dashboard displaying all metrics |
| `MetadataBarChart.tsx` | Bar charts for per-field accuracy/F1 |
| `ComprehensiveChart.tsx` | Comprehensive comparison view across all metrics |

## Requirements

- `requirements.txt` for validation scripts
- Running API services for `validation_finetunning.py`
- `ORCHESTRATOR_TOKEN` in `.env`
- Node.js for the frontend dashboard
