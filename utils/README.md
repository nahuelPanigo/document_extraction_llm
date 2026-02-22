# Utils — Shared Utilities

Shared modules used across `fine_tune_subject/`, `fine_tune_type/`, `download_prepare_clean_normalize_sedici_dataset/`, `validation/`, and other parts of the project.

## Structure

```
utils/
├── ml_strategies/                  # Shared ML training framework
│   ├── training_strategy.py        # TrainingStrategy abstract base class + TrainingResults
│   ├── data_loader.py              # Generic load_csv_labels() + create_dataset()
│   ├── model_comparison_framework.py  # ModelComparator: charts, confusion matrices, heatmaps
│   └── strategies/                 # 7 model strategy implementations
│       ├── __init__.py             # Re-exports all strategies
│       ├── svm_strategy.py         # SVMTrainingStrategy (linear/rbf kernel)
│       ├── xgboost_strategy.py     # XGBoostTrainingStrategy
│       ├── random_forest_strategy.py  # RandomForestTrainingStrategy
│       ├── embeddings_strategy.py  # EmbeddingsTrainingStrategy (centroid similarity)
│       ├── embeddings_knn_strategy.py # EmbeddingsKNNTrainingStrategy
│       ├── neural_torch_strategy.py   # NeuralTorchTrainingStrategy (PyTorch)
│       └── minilm_strategy.py      # MiniLMTrainingStrategy (LaBSE + SVM)
├── download/                       # Shared PDF download logic
│   ├── __init__.py
│   └── pdf_downloader.py           # transform_id(), download_pdf(), download_batch()
├── text_extraction/                # Text extraction from PDFs
│   ├── pdf_reader.py               # PdfReader class (with optional OCR)
│   └── read_and_write_files.py     # File I/O helpers
├── colors/
│   └── colors_terminal.py          # Bcolors terminal color constants
├── consume_apis/                   # External API clients
│   ├── consume_llm.py              # LLM API calls (OpenAI, Gemini)
│   ├── consume_extractor.py        # Extraction service client
│   └── consume_orchestrator.py     # Orchestrator service client
└── normalization/
    └── normalice_data.py           # Data normalization utilities
```

## ml_strategies/ — Shared ML Training Framework

The core reusable framework for training and comparing ML models. Both `fine_tune_subject` and `fine_tune_type` are thin wrappers around this shared code.

### TrainingStrategy (Abstract Base Class)

All model strategies implement this interface:

```python
class TrainingStrategy(ABC):
    def train(self, documents, labels) -> float       # Train model, return accuracy
    def get_model_name(self) -> str                    # Display name
    def get_model_files(self) -> list                  # Saved file paths
    def load_model(self) -> bool                       # Load trained model
    def predict(self, X_test) -> list                  # Predict on test data
```

### Key Design: `model_dir` Parameter

Every strategy accepts a `model_dir` parameter in its constructor, defaulting to subject classification paths for backward compatibility. The type module overrides this:

```python
# Subject (default model_dir)
SVMTrainingStrategy(kernel='linear')

# Type (explicit model_dir)
SVMTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['svm_linear'], kernel='linear')
```

### Data Loader

Generic functions that work with any CSV + text folder:

- **`load_csv_labels(csv_path, label_column)`** — Load CSV into `{id: label}` mapping
- **`create_dataset(label_mapping, txt_folder, ...)`** — Read text files, filter by frequency, balance per label, return `(documents, labels, doc_ids)`

### ModelComparator

Parameterized comparison framework that generates:

- **Comparison charts** — Accuracy, Precision, Recall, F1, Load Time, Prediction Time
- **Confusion matrices** — Per-model, normalized to percentages
- **Label-model heatmap** — Per-label accuracy across all models
- **Performance summary** — Per-model metrics + timing charts
- **Text reports** — `performance_metrics.txt` per model

Usage:

```python
comparator = ModelComparator(
    strategies={"svm": SVMTrainingStrategy(...)},
    results_folder=Path("model_results/"),
    load_data_fn=my_data_loader
)
comparator.run_comparison(["svm", "xgboost"])
```

### Available Strategies

| Strategy | Description | Key Features |
|----------|-------------|--------------|
| `SVMTrainingStrategy` | Support Vector Machine | TF-IDF + SVM, `kernel` param (linear/rbf), GridSearchCV |
| `XGBoostTrainingStrategy` | Gradient Boosting | TF-IDF + XGBoost, class weighting |
| `RandomForestTrainingStrategy` | Random Forest | TF-IDF + RF ensemble |
| `EmbeddingsTrainingStrategy` | Sentence Embeddings + Centroid | Embedding similarity classification |
| `EmbeddingsKNNTrainingStrategy` | Sentence Embeddings + KNN | KNN on embedding space |
| `NeuralTorchTrainingStrategy` | PyTorch Neural Network | Feed-forward NN on embeddings |
| `MiniLMTrainingStrategy` | LaBSE + SVM | Sentence-transformers embeddings + SVM |

## download/ — Shared PDF Downloader

Shared download logic used by both subject and type modules:

- **`transform_id(doc_id)`** — Convert `10915-123` to `10915/123`
- **`download_pdf(doc_id, pdf_folder)`** — Download single PDF with rate-limit handling
- **`download_batch(ids, pdf_folder)`** — Batch download with retries, progress, and summary

## text_extraction/

Used across many folders — provides all file I/O and PDF reading functions.

**`read_and_write_files.py`** — File operations:

| Function | Description |
|----------|-------------|
| `read_data_json()` | Load JSON data from file |
| `write_to_json()` | Write data to JSON file |

**`pdf_reader.py`** — PDF text extraction used in the data pipeline.

**Used by**: data pipeline (`download_prepare_clean_normalize_sedici_dataset`), fine-tuning, validation, and others.

## normalization/

**`normalice_data.py`** — Text normalization and cleaning:

| Function | Description |
|----------|-------------|
| `normalice_text()` | Remove duplicated characters, fix numbers |
| `remove_honorifics()` | Strip titles (Dr., Dra., Lic., Ing., etc.) from names |

**Used by**: data pipeline, API (extractor/orchestrator), and others.

## consume_apis/

HTTP clients for calling each API service. Used primarily by the validation module.

| File | Target Service |
|------|----------------|
| `consume_orchestrator.py` | Orchestrator API (port 8000) |
| `consume_extractor.py` | Extractor Service (port 8001) |
| `consume_llm.py` | LLM Service (port 8002/8003) |

**Used by**: validation scripts.

## colors/

**`colors_terminal.py`** — Terminal color formatting helpers for console output (green for success, red for errors, etc.).
