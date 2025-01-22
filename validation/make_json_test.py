import requests
from pathlib import Path
import json

def write_to_json(json_filename,data,enc):
  with open(json_filename, 'w', encoding=enc) as jsonfile:
        json.dump(data, jsonfile, indent=4)


url_sevices_extraction = "http://localhost:8000/upload"
ROOT_DIR = Path(__file__).resolve().parents[1]  / "fine_tunning" 
PDF_FOLDER = ROOT_DIR  / "data/sedici/pdfs/"

final_dict = {}
for id in test_keys:
    filename= PDF_FOLDER  / f"{id}.pdf"
    with open(str(filename), 'rb') as file :
        data = {'file' : (str(filename), file)}
        response = requests.post(url=url_sevices_extraction,files=data)
        if response.status_code == 200:
            final_dict[id] =  response.json()
        else:
            print(f"problem in id: {id} status code : {response.status_code}")

write_to_json("result_finetunnig_4096_prompt1.json",final_dict,"utf-8")
