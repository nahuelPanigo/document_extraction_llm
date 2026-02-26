# Utilities

Shared utility modules used across multiple folders in the project.

## Module Overview

```
utils/
├── colors/
│   └── colors_terminal.py        # Terminal color formatting
├── text_extraction/
│   ├── read_and_write_files.py   # JSON/TXT I/O, file operations
│   └── pdf_reader.py             # PDF text extraction
├── normalization/
│   └── normalice_data.py         # Text cleaning, accent removal
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
`