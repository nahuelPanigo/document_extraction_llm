import requests
from pathlib import Path
import os
from ..utils.text_extraction.read_and_write_files import read_data_json,write_to_json
from ..constants import URL_SERVICES_EXTRACTION,JSON_FILENAME,PDF_FOLDER,JSON_FOLDER,RESULT_FOLDER_VALIDATION


original_metadata = {}
final_dict = {}
for filename in os.listdir(PDF_FOLDER):
    id = filename.replace(".pdf","")
    metadata =read_data_json(JSON_FOLDER / JSON_FILENAME)
    with open(str(PDF_FOLDER / filename), 'rb') as file :
        type = metadata[id]["dc.type"]
        files = {'file' : (str(filename), file,'application/pdf')}
        response = requests.post(url=URL_SERVICES_EXTRACTION,files=files, data = {"type" : "General"})
        final_dict[id] = []
        print("procesando el id :",id)
        if response.status_code == 200:
            final_dict[id].append(response.json())
        else:
            print(f"problem in id: {id} status code : {response.status_code} con el error: {response.text}")
        type = metadata[id]["dc.type"]
        file.seek(0)
        data = {'file' : (str(filename), file), 'type' : type}
        response = requests.post(url=URL_SERVICES_EXTRACTION,files=files, data = {"type" : type})
        if response.status_code == 200:
            final_dict[id].append(response.json())
        else:
            print(f"problem in id: {id} status code : {response.status_code}")
        metadata[id].pop("original_text")
        original_metadata[id] = metadata[id] 
write_to_json(RESULT_FOLDER_VALIDATION + "result_test_2048_prompt_by_type.json",final_dict,"utf-8")
write_to_json(RESULT_FOLDER_VALIDATION + "result_test_original_metadata.json",original_metadata,"utf-8")