# Fine-Tune Subject Classification

## Overview

This module classifies academic documents from SEDICI into FORD (Fields of Research and Development) subject categories using various ML approaches. It shares the ML training framework with `fine_tune_type` via `utils/ml_strategies/`.

**35+ FORD categories** mapped from SEDICI subject terms (see `constants.FORD_SEDICI_MATERIAS`), including:
- Ciencias físicas, Ciencias químicas, Ciencias biológicas
- Ciencias de la computación e información
- Ingeniería civil, Ingeniería mecánica, Ingeniería eléctrica
- Economía y negocios, Derecho, Educación, Sociología
- Artes, Historia y arqueología, Lenguas y literatura
- And more...

## File Structure

```
fine_tune_subject/
├── main.py                        # Unified entry point (dataset pipeline + training)
├── make_dataset.py                # Dataset creation pipeline
├── create_subjects_csv.py         # Create subjects.csv from sedici.csv
├── download_balance_pdfs.py       # Download PDFs balanced by subject
├── convert_pdfs_to_txt.py         # PDF to text conversion
├── check_and_clean_xml_tags.py    # Remove XML/HTML tags from extracted texts
├── train.py                       # Model training (interactive menu / CLI)
├── model_comparison_framework.py  # ModelComparator subclass with subject config
├── strategies/                    # Re-exports from utils/ml_strategies/strategies
│   ├── __init__.py                # Thin re-export layer
│   ├── svm_strategy.py            # (legacy, shared version used)
│   ├── xgboost_strategy.py
│   ├── random_forest_strategy.py
│   ├── embeddings_strategy.py
│   ├── embeddings_knn_strategy.py
│   ├── neural_torch_strategy.py
│   └── minilm_strategy.py
├── utils/                         # Subject-specific utilities
│   ├── dataset/
│   │   ├── __init__.py
│   │   └── data_loader.py         # Thin wrapper: load_csv_subjects() + create_dataset()
│   └── models/
│       ├── __init__.py
│       ├── base_strategy.py
│       ├── evaluation.py
│       └── training_strategy.py
├── models/                        # Trained model artifacts
│   ├── svm_linear/
│   ├── svm_rbf/
│   ├── xgboost/
│   ├── random_forest/
│   ├── embeddings/
│   ├── embeddings_knn/
│   ├── neural/
│   └── minilm/
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
./run_modules.sh fine_tune_subject
```

This runs `main.py`, which walks through:
1. **Data pipeline** — optionally create CSV, download PDFs, extract text, clean tags
2. **Model training** — interactive menu to train individual or all models

### Model Training

```bash
# Interactive menu
python -m fine_tune_subject.train

# Train a specific model
python -m fine_tune_subject.train svm
python -m fine_tune_subject.train minilm

# Train all models + generate comparison charts
python -m fine_tune_subject.train all --compare

# Compare already-trained models (no training)
python -m fine_tune_subject.train --compare-only
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

When selecting "Train All Models", the comparison framework runs automatically after training.

### Model Comparison Only

Compare already-trained models without retraining:

```bash
# CLI
python -m fine_tune_subject.train --compare-only

# Or standalone (interactive model selection)
python -m fine_tune_subject.model_comparison_framework
```

### Dataset Management

```bash
# Create/expand subjects CSV
python -m fine_tune_subject.create_subjects_csv

# Clean extracted text (remove HTML/XML tags)
python -m fine_tune_subject.check_and_clean_xml_tags
```

## Architecture

This module follows the **thin wrapper** pattern:

- **Shared strategies** live in `utils/ml_strategies/strategies/` — all 7 model implementations
- **Shared data loader** lives in `utils/ml_strategies/data_loader.py` — generic CSV + text loading
- **Shared comparator** lives in `utils/ml_strategies/model_comparison_framework.py` — parameterized charts
- **This module** provides subject-specific configuration:
  - `SUBJECT_MODEL_FOLDERS` paths from `constants.py`
  - Subject-specific data loading (`subjects.csv`, FORD mapping, `texts/` folder)
  - `ModelComparator` subclass wiring it all together
- **`strategies/__init__.py`** re-exports from `utils.ml_strategies.strategies` (old per-file strategies still exist but shared versions are used)

## Configuration (constants.py)

```python
CSV_SUBJECTS = "subjects.csv"
SUBJECT_MAPPING = FORD_SEDICI_MATERIAS    # SEDICI term -> FORD category mapping

SUBJECT_MODEL_FOLDER = ROOT_DIR / "fine_tune_subject/models"
SUBJECT_MODEL_FOLDERS = {
    "svm": SUBJECT_MODEL_FOLDER / "svm",
    "svm_linear": SUBJECT_MODEL_FOLDER / "svm_linear",
    "svm_rbf": SUBJECT_MODEL_FOLDER / "svm_rbf",
    "xgboost": SUBJECT_MODEL_FOLDER / "xgboost",
    "random_forest": SUBJECT_MODEL_FOLDER / "random_forest",
    "embeddings": SUBJECT_MODEL_FOLDER / "embeddings",
    "embeddings_knn": SUBJECT_MODEL_FOLDER / "embeddings_knn",
    "neural": SUBJECT_MODEL_FOLDER / "neural",
    "minilm": SUBJECT_MODEL_FOLDER / "minilm",
}
SUBJECT_MODEL_RESULTS_FOLDER = ROOT_DIR / "fine_tune_subject/model_results"
```

## Key Patterns & Decisions

- **FORD classification** — SEDICI's local subject terms are mapped to standardized FORD categories via `FORD_SEDICI_MATERIAS` in `constants.py`
- **Balanced dataset** — Up to 200 samples per subject, with year-based filtering (post-2019)
- **Enhanced TF-IDF** — SVM uses 50k features, 4-grams, custom Spanish stop words (305 words) for better science class separation
- **Separate SVM kernels** — Linear and RBF use dedicated model folders to prevent collisions

## Known Challenges

- **Science class confusion** — Related subjects like "Ciencias físicas", "Ciencias químicas", and "Ciencias biológicas" can be confused due to overlapping vocabulary
- **Class imbalance** — Some FORD categories have significantly fewer documents than others
- **35+ classes** — High number of categories makes classification harder than type (4 classes)
