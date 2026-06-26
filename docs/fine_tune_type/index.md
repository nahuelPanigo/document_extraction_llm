# Document Type Classifier

Trains a classifier to identify the type of an academic document from its text content. The trained model is used by the Orchestrator API to select the correct type-specific prompt.

Mirrors [`fine_tune_subject`](../fine_tune_subject/index.md) — both share the same training strategies (`utils/ml_strategies/`); this module only supplies the type-specific dataset pipeline and model directories.

Run with:

```bash
./run_modules.sh fine_tune_type
```

## Classification Target

| Type | Spanish |
|------|---------|
| Thesis | Tesis |
| Book | Libro |
| Article | Articulo |
| Conference Object | Objeto de conferencia |

## Module Structure

| File | Responsibility |
|------|----------------|
| `main.py` | Backward-compatible entry point: runs `make_dataset` then `train` then `test` (interactive) |
| `make_dataset.py` | Data pipeline: create types CSV, download balanced PDFs (target 500/type), extract plain text (no tags) |
| `create_types_csv.py` | Builds the id→type CSV from SEDICI metadata |
| `download_balance_pdfs.py` | Downloads PDFs balanced across types |
| `convert_pdfs_to_txt.py` | Extracts plain text from downloaded PDFs (untagged, unlike the subject module which also cleans tags) |
| `train.py` | Training entry point — interactive menu or CLI (`svm`, `xgboost`, `random_forest`, `embeddings`, `embeddings_knn`, `neural`, `minilm`, `all`) |
| `model_comparison_framework.py` | Thin type-specific wrapper around the shared comparison framework |
| `test.py` | Test trained model(s) against a single PDF file |

## Dataset & Training

```bash
python -m fine_tune_type.make_dataset --all     # build dataset
python -m fine_tune_type.train all --compare    # train all strategies + comparison
python -m fine_tune_type.test /path/to/file.pdf # test on a single PDF
```

Data loading uses `utils.ml_strategies.data_loader.load_csv_labels` / `create_dataset` against `CSV_FOLDER / CSV_TYPES` and `TXT_NO_TAGS_FOLDER`, capping each label at `SAMPLES_PER_TYPE` (from `constants.py`, default 500) with `min_frequency=5`.

Each strategy is instantiated with an explicit `model_dir=TYPE_MODEL_FOLDERS[...]` (from `constants.py`) so it saves to a type-specific folder instead of the subject module's default — this is what lets the same `SVMTrainingStrategy`/`XGBoostTrainingStrategy`/etc. classes in `utils/ml_strategies/strategies/` serve both classifiers. See [Subject Classifier](../fine_tune_subject/index.md) for the full strategy table.

## Deployed Model

The TF-IDF + sklearn classifier (`modelo_tipo_documento.pkl` + `vectorizador_tfidf.pkl`) is the one loaded by the Orchestrator at runtime — see [Orchestrator: Models Required](../api/orchestrator.md#models-required).
