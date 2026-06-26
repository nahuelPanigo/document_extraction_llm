# Validation

This module evaluates the whole metadata extraction pipeline by comparing predicted metadata against ground truth. There are 3 separate validation scripts, one for each extraction approach, plus a metric checker dashboard (FastAPI + React) for visualizing results.

## Validation Scripts

There is no single `main.py`. Instead, there are independent scripts, each validating a different extraction method, plus a benchmark script and a full cross-system comparison runner:

| Script | What it does |
|--------|-------------------|
| `validation_finetunning.py` | Extracts metadata with our fine-tuned model (via the Orchestrator API) |
| `validation_grobid.py` | Sends PDFs to GROBID, parses the returned TEI XML into metadata; times PDF→XML and XML→metadata separately per document |
| `validation_langsmith.py` | Extracts metadata via cloud LLMs (OpenAI, Gemini) using `PROMPT_CLOUD_LLM_VALIDATOR` |
| `benchmark_extraction.py` | Times the Extractor service's `/extract` and `/extract-with-tags` endpoints across all validation PDFs, broken down by document type, flags docs slower than 45s |
| `run_comparison.py` | Runs the metric-checker comparison (via the backend API if running, else a direct import fallback) for FINETUNNED, CLOUDLLM and GROBID against the same ground truth in one pass, and writes a combined report |

Each per-method script:

1. Takes documents from the test dataset (ground truth: `validation/result/final_to_compare_original.json`)
2. Extracts metadata using its respective method
3. Compares predictions with ground truth
4. Saves results to its own subfolder inside `result/`

## Results Structure

```
validation/result/
├── final_to_compare_original.json  # Ground truth (stays at root level)
├── full_comparison_results.json    # run_comparison.py: raw per-system metrics
├── full_comparison_report.txt      # run_comparison.py: human-readable summary
├── extraction_benchmark.json       # benchmark_extraction.py output
├── FINETUNNED/                     # Fine-tuned model results
├── GROBID/                         # GROBID results
├── CLOUDLLM/                       # Cloud LLM results (OpenAI, Gemini, etc.)
└── LEDEN/                          # LED model results
```

## Full Comparison Runner (`run_comparison.py`)

```bash
# With the metric-checker backend running (validation/backend/metric-checker, python index.py):
python validation/run_comparison.py

# Without it — falls back to importing run_metrics directly:
python validation/run_comparison.py
```

Compares `FINETUNNED`, `CLOUDLLM` and `GROBID` predictions against the same ground truth in a single run. Before comparing, `normalize_predicted()` flattens the `keywords: {real, suggested}` dict (see [Orchestrator API docs](../api/orchestrator.md) for how that shape is produced) down to the `real` list, since the metric checker expects a plain keyword list. Also flags fields where more than 80% of a system's predictions are null (`NULL_THRESHOLD`).

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
