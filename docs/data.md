# Data & Constants

## Data Folder Structure

```
data/sedici/
├── csv/
│   ├── sedici.csv                                    # Original SEDICI export
│   └── sedici_filtered_2019_2024.csv                 # Filtered & processed (2000 docs)
├── pdfs/                                             # Downloaded PDF documents
├── texts/                                            # Extracted text with XML tags
└── jsons/
    ├── metadata_sedici.json                          # Initial metadata only
    ├── metadata_sedici_and_text_with_ocr.json        # Metadata + extracted text
    ├── metadata_sedici_and_text_cleaned_with_ocr.json # After cleaning
    └── sedici_finetuning_dataset.json                 # Final training dataset (uploaded to HuggingFace as sedici-ml-models)
```

## Dataset Stats

| Parameter | Value |
|-----------|-------|
| Total documents | 2000 |
| Per type | 500 (balanced) |
| Training split | 80% (1600) |
| Validation split | 10% (200) |
| Test split | 10% (200) |

## Constants (`constants.py`)

The root-level `constants.py` file contains all global configuration. Key sections:

### Cloud LLM Provider Selection

```python
CLEAN_PROVIDER_TO_USE = "openai"  # "genai" or "openai"
```

### Gemini API Configuration

```python
GENAI_MODEL = "gemini-2.5-flash"
GENAI_REQUEST_LIMIT = {
    "req_per_day": 1000,
    "req_per_min": 15,
    "tok_per_min": 250000
}
```

### OpenAI API Configuration

```python
OPENAI_MODEL = "gpt-5-mini"
OPENAI_REQUEST_LIMIT = {
    "req_per_day": 10000,
    "req_per_min": 60,
    "tok_per_min": 200000
}
```

### Subject & Type Classifier Folders

```python
SUBJECT_MODEL_FOLDER = ROOT_DIR / "fine_tune_subject/models"
SUBJECT_MODEL_FOLDERS = {"svm": ..., "svm_linear": ..., "svm_rbf": ..., "xgboost": ...,
                          "random_forest": ..., "embeddings": ..., "embeddings_knn": ...,
                          "neural": ..., "minilm": ...}
SUBJECT_MODEL_RESULTS_FOLDER = ROOT_DIR / "fine_tune_subject/model_results"

TXT_NO_TAGS_FOLDER = DATA_FOLDER / "texts_no_tags/"
CSV_TYPES = "types.csv"
TYPE_MODEL_FOLDER = ROOT_DIR / "fine_tune_type/models"
TYPE_MODEL_FOLDERS = {...}  # same keys as SUBJECT_MODEL_FOLDERS, no plain "svm" key
TYPE_MODEL_RESULTS_FOLDER = ROOT_DIR / "fine_tune_type/model_results"
```

Each strategy in `utils/ml_strategies/strategies/` is given the matching `*_MODEL_FOLDERS[key]` as its `model_dir`, so the same strategy classes save to separate locations depending on whether they're trained from `fine_tune_subject` or `fine_tune_type`. See [Subject Classifier](fine_tune_subject/index.md) and [Type Classifier](fine_tune_type/index.md).

### Dataset Configuration

```python
LENGTH_DATASET = 2000
SAMPLES_PER_TYPE = 500
PERCENTAGE_DATASET_FOR_STEPS = {
    "training": 0.8,
    "validation": 0.1,
    "test": 0.1
}
```

### Base Model Definitions

| Key | Model |
|-----|-------|
| `LED` | `allenai/led-base-16384` (default) |
| `LED_LARGE` | `allenai/led-large-16384` |
| `LED_SPANISH` | `vgaraujov/led-base-16384-spanish` |
| `LLAMA` | Meta LLAMA |
| `GEMMA` | Google GEMMA |
| `Mistral` | Mistral AI |
| `NuExtract` | Schema-based extraction |
| `T5` | Google T5 |

### FORD Subject Mapping (`FORD_SEDICI_MATERIAS`)

Dictionary that maps SEDICI subject categories to FORD (Frascati) classification codes. Used by the data pipeline and subject classifier.

### Metadata Field Mappings (`COLUMNS_TYPES`)

Maps 30+ fields from Dublin Core, MODS, and SEDICI standards:

- **Common fields**: id, dc.type, title, creator, date, language, rights, description
- **Thesis fields**: director, codirector, degree.grantor, degree.name, institucionDesarrollo (research lab/institute, can be a list)
- **Book fields**: publisher, ISBN
- **Article fields**: ISSN, journal
- **Conference Object fields**: ISSN, event

### Type-Specific Prompts

| Prompt | Used For |
|--------|----------|
| `PROMPT_GENERAL` | Common metadata fields |
| `PROMPT_TESIS` | Thesis-specific fields |
| `PROMPT_LIBRO` | Book-specific fields |
| `PROMPT_ARTICULO` | Article-specific fields |
| `PROMPT_OBJECTO_CONFERENCIA` | Conference object-specific fields |
| `PROMPT_CLEANER_METADATA` | Cloud LLM data-cleaning prompt for the SEDICI pipeline, used by both Gemini and OpenAI consumers (`download_prepare_clean_normalize_sedici_dataset/cloud_llm_cleaner_consumer/`) |
| `PROMPT_CLOUD_LLM_VALIDATOR` | Separate metadata-extraction prompt used only by `validation/validation_langsmith.py` (cloud LLM validation benchmark) |

`PROMPT_CLEANER_METADATA` normalizes the `date` field to ISO-like `"yyyy/mm/dd"` / `"yyyy/mm"` / `"yyyy"` (previously `"dd-mm-yyyy"` / `"mm-yyyy"`), canonicalizes institution names (expanding UNLP/UBA/UTN/UNC, keeping `CONICET` as-is, "Facultad de Artes" instead of "Facultad de Bellas Artes"), normalizes `degree.name` to person form (e.g. "Licenciatura en X" → "Licenciado en X"), strips honorifics from name fields, and allows `institucionDesarrollo` to be a JSON array when a thesis has multiple research units.
