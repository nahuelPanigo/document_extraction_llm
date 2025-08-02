import requests
from pathlib import Path
import os
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json
from utils.consume_apis.consume_orchestrator import upload_file
from constants import URL_SERVICES_EXTRACTION,PDF_FOLDER,JSON_FOLDER,RESULT_FOLDER_VALIDATION,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
import time
from dotenv import load_dotenv

load_dotenv()
original_metadata = {}
final_dict_deepanalyze = {}
final_dict = {}
times_with_deepanalyze = []
times = []

metadatas =read_data_json(JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,"utf-8")
for metadata in metadatas["validation"][:5]:
    id = metadata["id"]
    filename = PDF_FOLDER / f"{id}.pdf"
    print("procesando el id :",id)
    #response without deepanalyze
    try:
        start_time = time.time()    
        response = upload_file(filename,os.getenv("ORCHESTRATOR_TOKEN"),True,"None",deepanalyze=False)
        if response["error"] is None:
            final_dict[id] = response["data"]
            times.append(time.time() - start_time)
            write_to_json(RESULT_FOLDER_VALIDATION / "results.json",final_dict,"utf-8")
            write_to_json(RESULT_FOLDER_VALIDATION / "times.json",times,"utf-8")
    except Exception as e:
        print(f"problem in id: {id} error: {e}")
    #response with deepanalyze
    try:
        start_time = time.time()
        response_deepanalyze = upload_file(filename,os.getenv("ORCHESTRATOR_TOKEN"),True,"None",deepanalyze=True)
        if response_deepanalyze["error"] is None:
            final_dict_deepanalyze[id] = response_deepanalyze["data"]
            times_with_deepanalyze.append(time.time() - start_time)
            write_to_json(RESULT_FOLDER_VALIDATION / "results_deepanalyze.json",final_dict_deepanalyze,"utf-8")
            write_to_json(RESULT_FOLDER_VALIDATION / "times_with_deepanalyze.json",times_with_deepanalyze,"utf-8")
    except Exception as e:
        print(f"problem in id: {id} with deepanalyze error: {e}")

    original_metadata[id] = {x: k for x, k in metadata.items() if x not in ["id","dc.type","original_text"]}
    write_to_json(RESULT_FOLDER_VALIDATION / "result_test_original_metadata.json",original_metadata,"utf-8")