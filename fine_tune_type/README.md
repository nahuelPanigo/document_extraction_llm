# Fine-Tune Type Classification

## Overview

This module classifies academic documents from SEDICI into 4 document types using various ML approaches. It shares the ML training framework with `fine_tune_subject` via `utils/ml_strategies/`.

**Document types** (defined in `constants.VALID_TYPES`):
- Libro
- Tesis
- Articulo
- Objeto de conferencia

## File Structure

```
fine_tune_type/
├── main.py                        # Unified entry point (dataset pipeline + training)
├── make_dataset.py                # Dataset creation pipeline (--types, --download, --extract)
├── create_types_csv.py            # Create types.csv from sedici.csv (top 500/type, newest first)
├── download_balance_pdfs.py       # Download PDFs balanced by type
├── convert_pdfs_to_txt.py         # Extract plain text via PdfReader (multiprocessing)
├── train.py                       # Model training (interactive menu / CLI)
├── model_comparison_framework.py  # TypeModelComparator (thin wrapper over shared framework)
├── requirements.txt               # Python dependencies
├── models/                        # Trained model artifacts
│   ├── svm_linear/                # SVM with linear kernel
│   ├── svm_rbf/                   # SVM with RBF kernel
│   ├── xgboost/                   # XGBoost
│   ├── random_forest/             # Random Forest
│   ├── embeddings/                # Sentence embeddings + centroid
│   ├── embeddings_knn/            # Sentence embeddings + KNN
│   ├── neural/                    # PyTorch neural network
│   └── minilm/                    # LaBSE + SVM
└── model_results/                 # Comparison charts and confusion matrices
    ├── models_comparison_detailed.png
    ├── models_summary_comparison.png
    ├── label_model_accuracy_heatmap.png
    └── <model_key>/
        ├── confusion_matrix.png
        ├── performance_summary.png
        └── performance_metrics.txt
```

## Usage

### Quick Start (via run_modules.sh)

```bash
./run_modules.sh fine_tune_type
```

This runs `main.py`, which walks through:
1. **Data pipeline** — optionally create CSV, download PDFs, extract text
2. **Model training** — interactive menu to train individual or all models

### Dataset Creation

```bash
# Interactive mode
python -m fine_tune_type.make_dataset

# Run all steps
python -m fine_tune_type.make_dataset --all

# Run specific steps
python -m fine_tune_type.make_dataset --types          # Create types.csv
python -m fine_tune_type.make_dataset --download        # Download PDFs
python -m fine_tune_type.make_dataset --extract         # Convert PDFs to text
python -m fine_tune_type.make_dataset --download --extract  # Combine steps
```

**Pipeline steps:**

| Step | Script | Description |
|------|--------|-------------|
| `--types` | `create_types_csv.py` | Parse `sedici.csv`, filter to 4 valid types, take top 500 per type (newest first), save `types.csv` |
| `--download` | `download_balance_pdfs.py` | Download PDFs balanced by type using shared `utils/download/pdf_downloader.py` |
| `--extract` | `convert_pdfs_to_txt.py` | Extract plain text (no XML/HTML tags) via `PdfReader`, uses multiprocessing |

### Model Training

```bash
# Interactive menu
python -m fine_tune_type.train

# Train a specific model
python -m fine_tune_type.train svm
python -m fine_tune_type.train minilm

# Train all models + generate comparison charts
python -m fine_tune_type.train all --compare

# Compare already-trained models (no training)
python -m fine_tune_type.train --compare-only
```

**Interactive menu:**
```
1. SVM (Linear)
2. SVM (RBF)
3. XGBoost
4. Random Forest
5. Embeddings (Centroid)
6. Embeddings + KNN
7. Neural Network (PyTorch)
8. LaBSE (SVM)
9. Train All Models
10. Compare Models (no training)
11. Exit
```

When selecting "Train All Models", the comparison framework runs automatically after training, generating all charts into `model_results/`.

### Model Comparison Only

Compare already-trained models without retraining:

```bash
# CLI
python -m fine_tune_type.train --compare-only

# Or standalone
python -m fine_tune_type.model_comparison_framework
```

This loads saved models, runs predictions on the same test split, and generates:
- Comparison bar charts (accuracy, precision, recall, F1, timing)
- Confusion matrices per model
- Label-model accuracy heatmap
- Performance summaries (charts + text files)

## Architecture

This module follows the **thin wrapper** pattern:

- **Shared strategies** live in `utils/ml_strategies/strategies/` — all 7 model implementations
- **Shared data loader** lives in `utils/ml_strategies/data_loader.py` — generic CSV + text loading
- **Shared comparator** lives in `utils/ml_strategies/model_comparison_framework.py` — parameterized charts
- **This module** provides type-specific configuration:
  - `TYPE_MODEL_FOLDERS` paths from `constants.py`
  - Type-specific data loading (`types.csv`, `texts_no_tags/` folder)
  - `TypeModelComparator` subclass wiring it all together

## Configuration (constants.py)

```python
TXT_NO_TAGS_FOLDER = DATA_FOLDER / "texts_no_tags/"     # Plain text files for type training
CSV_TYPES = "types.csv"                                   # CSV with id, year, type
SAMPLES_PER_TYPE = 500                                    # 500 per type × 4 types = 2000 total
VALID_TYPES = ["Libro", "Tesis", "Articulo", "Objeto de conferencia"]

TYPE_MODEL_FOLDER = ROOT_DIR / "fine_tune_type/models"
TYPE_MODEL_FOLDERS = {
    "svm_linear": TYPE_MODEL_FOLDER / "svm_linear",
    "svm_rbf": TYPE_MODEL_FOLDER / "svm_rbf",
    "xgboost": TYPE_MODEL_FOLDER / "xgboost",
    "random_forest": TYPE_MODEL_FOLDER / "random_forest",
    "embeddings": TYPE_MODEL_FOLDER / "embeddings",
    "embeddings_knn": TYPE_MODEL_FOLDER / "embeddings_knn",
    "neural": TYPE_MODEL_FOLDER / "neural",
    "minilm": TYPE_MODEL_FOLDER / "minilm",
}
TYPE_MODEL_RESULTS_FOLDER = ROOT_DIR / "fine_tune_type/model_results"
```

## Training Results

| Model | Accuracy | Notes |
|-------|----------|-------|
| SVM (Linear) | 94.78% | Best overall |
| XGBoost | 92.43% | |
| SVM (RBF) | 92.17% | |
| Random Forest | 87.99% | |
| LaBSE (SVM) | 86.16% | |
| Neural Network | 78.59% | |
| Embeddings + KNN | 75.46% | |
| Embeddings (Centroid) | 60.84% | |
