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

To run this step:
`python -m download_prepare_clean_normalize_sedici_dataset.main`

### FINE TUNING
in the folder fine_tunning we make a process to made easyear to fine tune the data with differents models/parameters and also technics to make the process more efficient.

the process consists in:
- downloading data from huggingface (if not exists in data folder, previously created in GENERATING TRAIN DATA)
- generate tokens from the data, for this we have multiple options:
    - prompt: we use a prompt to generate the tokens, for this models we also have a differentiation between casual models and seq2seq models
    - schema: we use a schema to generate the tokens
-finally we train  the models with the generated tokens (for this step it depends on model type if we use trainer or a traditional_train)


To run this step:
`python -m fine_tunning.main`

To install prerequisites (inside fine_tunning) do: 
`pip install -r requirements.txt` (It is suggested to do it with an enviroment)


### VALIDATION
for this step we have to use the model trained in the previous step and run in fastapi (see the process RUNNING API FOR MODEL USAGE)
this step consists in:
- make request to the api to extract the metadata
- make a json with results and the original metadata


to run this step:
`python -m validation.make_json_test`


the results will be in the folder validation/result in json format (there is the original metadata and the metadata extracted by the model. The model extract 2 differents metadata for each id, general with metadata for all dc.type and one specific of the dc.type)



## RUN API FOR MODEL USAGE

- install prerequisites  (inside api folder do `pip install -r requirementes.txt` It is suggested to do it with an enviroment)
- run `fastapi run dev`

## USAGE API

make post http://localhost:5000/upload    with Multipart form:   key=file and the (doc or pdf)




## PROJECT STRUCTURE
```
document_extraction_llm
├── api
│   ├── app.py
│   │   ├── errors.py
│   │   ├── constants.py
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
- split data inside download_prepare_clean_normalize_sedici_dataset
- run new fine_tunning
- run new validation
- make configuration in finetunning for qwen and gemma models