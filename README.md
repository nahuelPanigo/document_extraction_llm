# Document Metadata Extraction with LLM

This project provides automated scripts for running different modules with isolated virtual environments and specific dependencies.

## Quick Start - Running Modules

### Using the Run Scripts

Use the provided scripts to run any module with automatic virtual environment management:

**Windows:**
```bash
run_modules.bat <mode> [--python PY_EXE] [--reinstall]
```

**Linux/Mac:**
```bash
./run_modules.sh <mode> [--python PYTHON_EXE] [--reinstall]
```

### Available Modes

| Mode | Description | Requirements |
|------|-------------|--------------|
| `make_dataset` | Download, prepare, clean and normalize SEDICI dataset | 1. `sedici.csv` in `data/sedici/csv/` folder<br>2. `GOOGLE_API_KEY` in `.env` |
| `fine_tunning` | Fine-tune models for metadata extraction | 1. JSON dataset from `make_dataset`<br>2. `TOKEN_HUGGING_FACE` in `.env` |
| `validation` | Validate trained models | 1. JSON dataset + PDFs from `make_dataset`<br>2. Running API services<br>3. `ORCHESTRATOR_TOKEN` in `.env` |
| `fine_tune_type` | Train document type classifier | 1. CSV + text files from `make_dataset`<br>2. Will be refactored |
| `fine_tune_subject` | Train subject/topic classifier | 1. CSV file from `make_dataset`<br>2. Text files from `make_dataset` |

### Examples

```bash
# Run dataset creation (first step)
run_modules.bat make_dataset

# Run with specific Python version
run_modules.bat fine_tunning --python python3.11

# Reinstall virtual environment and run
./run_modules.sh validation --reinstall
```

## Prerequisites and Dependencies

### For `make_dataset` Mode

**Required Files:**
- `sedici.csv` file in `data/sedici/csv/` folder

**Environment Variables:**
- Create `.env` file based on `.env.example` in the `download_prepare_clean_normalize_sedici_dataset/` folder
- `GOOGLE_API_KEY=your_gemini_api_key`

**Important Constants (configurable in `constants.py`):**

```python
# Gemini API Configuration
GENAI_MODEL = "gemini-2.5-flash-lite"  # Can change if you have paid access
GENAI_REQUEST_LIMIT = {
    "req_per_day": 1000,   # Free tier limit
    "req_per_min": 15,     # Free tier limit  
    "tok_per_min": 32000   # Free tier limit
}

# Dataset Creation Limits
LENGTH_DATASET = 2000              # Total dataset size
SAMPLES_PER_TYPE = 500             # Samples per document type (500×4=2000)
PERCENTAGE_DATASET_FOR_STEPS = {   # Train/validation/test split
    "training": 0.8,
    "validation": 0.1, 
    "test": 0.1
}
```

**Note:** If you have paid Gemini access, you can:
- Change `GENAI_MODEL` to more powerful models like `"gemini-2.5-pro"`
- Increase the request limits in `GENAI_REQUEST_LIMIT`

## Environment Variables Setup

Create a `.env` file in the root directory with the following variables:

```bash
# For make_dataset module
GOOGLE_API_KEY=your_gemini_api_key

# For fine_tunning module  
TOKEN_HUGGING_FACE=your_huggingface_token

# For validation module (API authentication)
ORCHESTRATOR_TOKEN=your_orchestrator_token
EXTRACTOR_TOKEN=your_extractor_token
LLM_LED_TOKEN=your_llm_led_token
```

**Note:** Use strong, unique tokens for API authentication. Examples are provided in `api/app/.env.example`.

### For `fine_tunning` Mode

**Required Files:**
- JSON dataset: `data/sedici/jsons/sedici_finetunnig_metadata.json` (created by `make_dataset`)

**Environment Variables:**
- `TOKEN_HUGGING_FACE=your_huggingface_token` (for downloading models if dataset doesn't exist locally)

**Output:**
- Trained model saved to `fine-tuned-model-With-Objeto-Conferencia/` folder

### For `validation` Mode

**Required Files:**
- JSON dataset: `data/sedici/jsons/sedici_finetunnig_metadata.json` (created by `make_dataset`)
- PDF files in `data/sedici/pdfs/` folder (downloaded in `make_dataset`)

**Required Services:**
- API services must be running (see API section below)
- Fine-tuned model must be loaded in API service

**Environment Variables:**
- `ORCHESTRATOR_TOKEN=your_orchestrator_token` (for API authentication)

### For `fine_tune_subject` Mode

**Required Files:**
- CSV file: `data/sedici/csv/sedici_filtered_2019_2024.csv` (created by `make_dataset`)  
- Text files in `data/sedici/texts/` folder (created by `make_dataset`)

**Output:**
- `subject_classifier.pkl` - trained subject classifier model
- `vectorizer.pkl` - TF-IDF vectorizer
- `label_encoder.pkl` - label encoder for subjects

### For `fine_tune_type` Mode

**Note:** This module will be refactored. Current dependencies similar to `fine_tune_subject`.

### Execution Order

1. **`make_dataset`** - Must run first to create the training data
2. **`fine_tunning`** - Train the metadata extraction model  
3. **`validation`** - Validate the trained model (requires API services)
4. **`fine_tune_type`** - Optional: train document type classifier
5. **`fine_tune_subject`** - Optional: train subject classifier

## STEPS TO MAKE FINE_TUNNING

The fine tune consists in three steps:

1. Genarting train data
2. Fine tuning
3. validation

### GENERATING TRAIN DATA
in the folder download_prepare_clean_normalize_sedici_dataset consists in all content to download, prepare, normalize  and clean the dataset.
it consists in:
- extract data from csv (it use sedici.csv inside data folder):
    in this step with pandas library we normalize the data of the csv and we made a new csv with only the metadata needed (columns in constants.py) and the oldest data (we use older than 2019)
- download pdfs:
    in this step we download the pdfs taking the ids from the csv maded in the previous step
- extract text from pdfs:
    in this step we extract the text from the pdfs to txt files after that we make a json with the metadata and the text. we also add xml tags to the text to make it more readable.
- clean metadata:
    this step consists in cleaning the metadata with a llm (we use gemini) the idea is to get only the metadata that is in the text, and also to normalize as appears in the text. for get a better performance in the fine tuning process.

**To run this step:**
```bash
# Using the automated script (recommended)
run_modules.bat make_dataset
# or on Linux/Mac: ./run_modules.sh make_dataset

# Or manually (not recommended)
python -m download_prepare_clean_normalize_sedici_dataset.main
```

### FINE TUNING
in the folder fine_tunning we make a process to made easyear to fine tune the data with differents models/parameters and also technics to make the process more efficient.

the process consists in:
- downloading data from huggingface (if not exists in data folder, previously created in GENERATING TRAIN DATA)
- generate tokens from the data, for this we have multiple options:
    - prompt: we use a prompt to generate the tokens, for this models we also have a differentiation between casual models and seq2seq models
    - schema: we use a schema to generate the tokens
-finally we train  the models with the generated tokens (for this step it depends on model type if we use trainer or a traditional_train)


**To run this step:**
```bash
# Using the automated script (recommended)
run_modules.bat fine_tunning
# or on Linux/Mac: ./run_modules.sh fine_tunning

# Or manually (not recommended)
python -m fine_tunning.main
pip install -r fine_tunning/requirements.txt
```


### VALIDATION
for this step we have to use the model trained in the previous step and run in fastapi (see the process RUNNING API FOR MODEL USAGE)
this step consists in:
- make request to the api to extract the metadata
- make a json with results and the original metadata


**To run this step:**
```bash
# Using the automated script (recommended)
run_modules.bat validation
# or on Linux/Mac: ./run_modules.sh validation

# Or manually (not recommended)
python -m validation.main
```


the results will be in the folder validation/result in json format (there is the original metadata and the metadata extracted by the model. The model extract 2 differents metadata for each id, general with metadata for all dc.type and one specific of the dc.type)



## RUN API FOR MODEL USAGE

**Prerequisites for Validation:**
1. **Fine-tuned model** must be available in `api/app/llm_service/app/models/fine-tuned-model-led/` (or update path in API configuration)
2. **Document type classifier models** must be in `api/app/orchestrator/app/models/`:
   - `modelo_tipo_documento.pkl` (generated by `fine_tune_type`)
   - `vectorizador_tfidf.pkl` (generated by `fine_tune_type`)

**Setup:**
- Install prerequisites (inside api folder): `pip install -r requirements.txt` (use virtual environment)
- Configure environment variables based on `api/app/.env.example`
- Copy your fine-tuned model to the correct location in the API service

**Running:**
```bash
# Start all API services
cd api/app
./run_all_services.sh
# or on Windows: run_all_services.bat
```

## USAGE API

make post http://localhost:5000/upload    with Multipart form:   key=file and the (doc or pdf)




## PROJECT STRUCTURE
```
document_extraction_llm
├── api
│   ├── app.py
│   │   ├── extractor_service
│   │   │   ├── app
│   │   │   │   ├── main.py
│   │   │   │   ├── logging_config.py
│   │   │   │   ├── routers
│   │   │   │   │   └── routers.py
│   │   │   │   ├── errors
│   │   │   │   │   └── errors.py
│   │   │   │   ├── constants
│   │   │   │   │   └── constants.py
│   │   │   │   ├── middlewares
│   │   │   │   │   └── security.py
│   │   │   │   └── services
│   │   │   │          ├── strategies
│   │   │   │          │   ├── pdf_reader_strategy.py
│   │   │   │          │   ├── reader_strategy.py
│   │   │   │          │   └── word_reader_strategy.py
│   │   │   │          ├── utils
│   │   │   │              └──normalization_and_parse.py
│   │   ├── llm_service
│   │   │   ├── app
│   │   │   │   ├── main.py
│   │   │   │   ├── logging_config.py
│   │   │   │   ├── routers
│   │   │   │   │   └── routers.py
│   │   │   │   ├── errors
│   │   │   │   │   └── errors.py
│   │   │   │   ├── constants
│   │   │   │   │   └── constants.py
│   │   │   │   ├── middlewares
│   │   │   │   │   └── security.py
│   │   │   │   └── services
│   │   │   │          ├── llms_extraction.py
│   │   │   │          └── model_managment.py
│   │   ├── orchestrator
│   │   │   ├── app
│   │   │   │   ├── main.py
│   │   │   │   ├── logging_config.py
│   │   │   │   ├── routers
│   │   │   │   │   └── routers.py
│   │   │   │   ├── errors
│   │   │   │   │   └── errors.py
│   │   │   │   ├── constants
│   │   │   │   │   └── constants.py
│   │   │   │   ├── middlewares
│   │   │   │   │   └── security.py
│   │   │   │   └── services
│   │   │   │          ├── strategies
│   │   │   │          │   ├── type_strategy.py
│   │   │   │          ├── identifier.py
│   │   │   │          └── orchestrator.py
│   │   ├── fine-tuned-model
│   │   ├── main.py
│   │   ├── run.py
│   │   ├── router.py
│   │   └── utils
│   │       ├── extraction
│   │       │    └── text_extraction.py
│   │       └── model_manipulation
│   │           └──llms_extraction.py
│   └── requirements.txt
├── download_prepare_clean_normalize_sedici_dataset
│   ├── download_data.py
│   ├── extract_data_from_csv_sedici.py
│   ├── extract_text_make_dataset.py
│   ├── genai_consumer.py
│   ├── main.py
│   ├── requirements.txt
├── fine_tunning
│   ├── constant.py
│   ├── generate_tokens.py
│   ├── hugging_face_connection.py
│   ├── main.py
│   ├── model_managment.py
│   ├── peft_configuration.py
│   ├── requirements.txt
│   ├── trainer.py
├── validation
│   ├── make_json_test.py
│   ├── remove_unused_fields.py
│   └── result
├──Utils
│   ├── colors
│   │   ├── colors_terminal.py
│   │   └── __init__.py
│   ├── text_extraction
│   │   ├── read_and_write_files.py
│   │   └── __init__.py
│   └── text_normalization
│       ├── normalice_data.py
│       └── __init__.py
├── data
│   ├── sedici
│   │   ├── jsons
│   │   ├── pdfs
│   │   ├── texts
│   │   └── csv
├── constants.py
├── README.md
└── .gitignore
```

## TODO
- vovler a sacar y fijarse porque no sale obj conferencia
- chequear las uri en el excel que hicimos
- run new fine_tunning
- run new validation
- make configuration in finetunning for qwen and gemma models