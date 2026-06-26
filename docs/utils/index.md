# Utilities

Shared utility modules used across multiple folders in the project.

## Module Overview

```
utils/
├── colors/
│   └── colors_terminal.py        # Terminal color formatting
├── text_extraction/
│   ├── read_and_write_files.py   # JSON/TXT I/O, file operations
│   └── pdf_reader.py             # PDF text extraction (OCR + max_words, no multi-column)
├── normalization/
│   └── normalice_data.py         # Text cleaning, unicode/OCR accent fixes
├── ml_strategies/
│   ├── data_loader.py            # CSV label loading + balanced dataset creation
│   ├── training_strategy.py      # Abstract TrainingStrategy interface
│   ├── model_comparison_framework.py  # Shared model comparison/benchmarking
│   └── strategies/                # SVM, XGBoost, Random Forest, embeddings, embeddings_knn, neural, minilm
└── consume_apis/
    ├── consume_orchestrator.py   # HTTP client for Orchestrator API
    ├── consume_extractor.py      # HTTP client for Extractor API
    └── consume_llm.py            # HTTP client for LLM Service API
```

## text_extraction/

Used across many folders — provides all file I/O and PDF reading functions.

**`read_and_write_files.py`** — File operations:

| Function | Description |
|----------|-------------|
| `read_data_json()` | Load JSON data from file |
| `write_to_json()` | Write data to JSON file |

**`pdf_reader.py`** — PDF text extraction used in the data pipeline and by `fine_tune_subject`/`fine_tune_type` `test.py` scripts. Supports optional EasyOCR (full-page) and `max_words` truncation. Simpler sibling of the Extractor service's `pdf_reader_strategy.py` — no multi-column detection/reordering here.

**Used by**: data pipeline (`download_prepare_clean_normalize_sedici_dataset`), fine-tuning, validation, and others.

## normalization/

**`normalice_data.py`** — Text normalization and cleaning:

| Function | Description |
|----------|-------------|
| `normalice_text()` | Fixes `\uXXXX` unicode escapes and OCR-mangled accents, then removes duplicated characters and fixes repeated numbers |
| `fix_unicode_escapes()` | Converts literal `\uXXXX` escape sequences to real Unicode characters — safe alternative to `bytes().decode("unicode_escape")` since it only touches `\uXXXX` patterns |
| `fix_ocr_accents()` | Fixes the OCR artifact where an acute accent (´) is extracted as a standalone character next to a vowel (e.g. "Astrono´mica" → "Astronómica"), including dotless-ı |
| `remove_accents()` | Strips diacritics via NFD/NFC unicode normalization — destructive, used only where accent-insensitive comparison is needed (not part of `normalice_text`) |
| `remove_honorifics()` | Strip titles (Dr., Dra., Lic., Ing., etc.) and parenthesised institutional suffixes from names |

The same `fix_unicode_escapes`/`fix_ocr_accents` logic is duplicated in the Extractor service's `app/service/utils/normalization_and_parse.py`, since the API can't import the root-level `utils/` package directly.

**Used by**: data pipeline, API (extractor/orchestrator), and others.

## ml_strategies/

Shared ML training infrastructure used by both [`fine_tune_subject`](../fine_tune_subject/index.md) and [`fine_tune_type`](../fine_tune_type/index.md) — see those pages for the strategy table and usage. Each strategy accepts an explicit `model_dir` so the same classes can save models for either classifier independently.

**Used by**: `fine_tune_subject`, `fine_tune_type`.

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
`