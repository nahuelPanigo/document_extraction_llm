import requests
from pathlib import Path
import os
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json
from utils.consume_apis.consume_orchestrator import upload_file
from constants import URL_SERVICES_EXTRACTION,PDF_FOLDER,JSON_FOLDER,RESULT_FOLDER_VALIDATION,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
import time
from dotenv import load_dotenv



unused_fields = ["dc.uri","sedici.uri","keywords","original_text"]


def remove_unused_fields(data):
    final_data = {}
    for inner_dict in data:
        cleaned_dict = {k: v for k, v in inner_dict.items() if k not in unused_fields}
        final_data[inner_dict["id"]] = cleaned_dict
    return final_data




load_dotenv()
original_metadata = {}
final_dict_deepanalyze = {}
final_dict = {}
times_with_deepanalyze = []
times = []

metadatas =read_data_json(JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,"utf-8")
validation_original_metadata =  remove_unused_fields(metadatas["validation"][:50])
for id, metadata in validation_original_metadata.items():
    filename = PDF_FOLDER / f"{id}.pdf"
    type = metadata["type"]
    try:

        response = upload_file(filename,os.getenv("ORCHESTRATOR_TOKEN"),True,type,deepanalyze=False)
        if response["error"] is None:
            final_dict[id] = response["data"]
            write_to_json(RESULT_FOLDER_VALIDATION / "results-object-conference.json",final_dict,"utf-8")
            print(f"ok in id: {id}")
        else:
            print(f"problem in id: {id} error: {response['error']}")
    except Exception as e:
        print(f"problem in id: {id} error: {e}")
    write_to_json(RESULT_FOLDER_VALIDATION / "result_test_original_metadata-with-object-conference.json",validation_original_metadata,"utf-8")