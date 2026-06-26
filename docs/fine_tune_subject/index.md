# Subject Classifier

Trains and compares multiple ML models to classify documents by academic subject/discipline, mapped to FORD (Frascati) categories (`FORD_SEDICI_MATERIAS` in `constants.py`). The best-performing model (currently SVM, linear kernel) is the one deployed in the Orchestrator API.

The training strategies (SVM, XGBoost, Random Forest, embeddings, neural net) are **shared** with [`fine_tune_type`](../fine_tune_type/index.md) via `utils/ml_strategies/` — this module only supplies the subject-specific dataset pipeline and wiring.

Run with:

```bash
./run_modules.sh fine_tune_subject
```

## Module Structure

| File | Responsibility |
|------|----------------|
| `main.py` | Backward-compatible entry point: runs `make_dataset` (interactive) then `train` (interactive) then `test` (interactive) |
| `make_dataset.py` | Data pipeline: create subjects CSV, download balanced PDFs, extract text, clean tags |
| `create_subjects_csv.py` | Builds the id→subject CSV from SEDICI metadata |
| `download_balance_pdfs.py` | Downloads PDFs balanced across subjects (target: 200 per subject) |
| `convert_pdfs_to_txt.py` | Extracts plain text from downloaded PDFs |
| `check_and_clean_xml_tags.py` | Strips leftover XML/HTML tags from extracted text |
| `train.py` | Training entry point — interactive menu or CLI (`svm`, `xgboost`, `random_forest`, `embeddings`, `embeddings_knn`, `neural`, `minilm`, `all`) |
| `model_comparison_framework.py` | Thin subject-specific wrapper around the shared comparison framework |
| `test.py` | Test trained model(s) against a single PDF file |

## Dataset Pipeline (`make_dataset.py`)

```bash
python -m fine_tune_subject.make_dataset                       # interactive
python -m fine_tune_subject.make_dataset --all                 # run all steps
python -m fine_tune_subject.make_dataset --subjects --download # specific steps
```

Steps (each optional, run only if needed): `subjects` → `download` → `extract` → `clean`.

## Training (`train.py`)

```bash
python -m fine_tune_subject.train                  # interactive model selection
python -m fine_tune_subject.train svm               # train a single model
python -m fine_tune_subject.train all --compare     # train all + comparison charts
python -m fine_tune_subject.train --compare-only    # compare already-trained models
```

Data loading (`utils.ml_strategies.data_loader`) builds `(documents, labels, ids)` from the subjects CSV and the `.txt` folder, filtering labels with `min_frequency >= 5` documents and capping each label at `max_per_label = 200` (random sample, seed 42).

## Shared Training Strategies (`utils/ml_strategies/`)

Both `fine_tune_subject` and `fine_tune_type` train against the same `TrainingStrategy` interface (`train`, `get_model_name`, `get_model_files`, `load_model`, `predict`), implemented in `utils/ml_strategies/strategies/`:

| Key | Strategy | File | Notes |
|-----|----------|------|-------|
| `svm` / `svm_rbf` | `SVMTrainingStrategy` | `svm_strategy.py` | TF-IDF (up to 60k features, 1-3 grams) + `SVC`, optional GridSearch. Spanish stop-word list. **Deployed model.** |
| `xgboost` | `XGBoostTrainingStrategy` | `xgboost_strategy.py` | TF-IDF + gradient boosting |
| `random_forest` | `RandomForestTrainingStrategy` | `random_forest_strategy.py` | TF-IDF + Random Forest |
| `embeddings` | `EmbeddingsTrainingStrategy` | `embeddings_strategy.py` | Sentence embeddings + nearest-centroid classification |
| `embeddings_knn` | `EmbeddingsKNNTrainingStrategy` | `embeddings_knn_strategy.py` | Sentence embeddings + KNN |
| `neural` | `NeuralTorchTrainingStrategy` | `neural_torch_strategy.py` | PyTorch feed-forward classifier over embeddings |
| `minilm` | `MiniLMTrainingStrategy` | `minilm_strategy.py` | `all-MiniLM-L6-v2` embeddings + SVM |

Each strategy saves its own model files to a subject-specific or type-specific folder (e.g. `svm_classifier.pkl`, `svm_vectorizer.pkl`, `svm_label_encoder.pkl` for SVM), resolved from `constants.py` (`SUBJECT_MODEL_FOLDERS`) unless an explicit `model_dir` is passed to the constructor — that's what lets the same class serve both modules.

## Model Comparison

`model_comparison_framework.ModelComparator` (subject-specific) wraps `utils.ml_strategies.model_comparison_framework.ModelComparator` with the subject dataset loader and `SUBJECT_MODEL_RESULTS_FOLDER`. Running `train all --compare` or `train --compare-only` trains/loads each strategy, evaluates them on the same test split, and writes comparison charts/metrics to that results folder.

## Testing a Single File (`test.py`)

```bash
python -m fine_tune_subject.test                              # interactive
python -m fine_tune_subject.test /path/to/file.pdf            # test all trained models
python -m fine_tune_subject.test /path/to/file.pdf --model svm
```

Extracts text from the given PDF with `utils.text_extraction.pdf_reader.PdfReader`, then runs it through one or all previously trained strategies (loaded via `load_model()`) and prints the predicted subject per model.
