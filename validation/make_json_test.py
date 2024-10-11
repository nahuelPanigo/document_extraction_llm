import requests
from pathlib import Path
import json

def write_to_json(json_filename,data,enc):
  with open(json_filename, 'w', encoding=enc) as jsonfile:
        json.dump(data, jsonfile, indent=4)


test_keys= {'ARG-UNLP-TDG-0000000204', 'ARG-UNLP-TDG-0000000173', 'ARG-UNLP-ART-0000007903', 'ARG-UNLP-TPG-0000000120', 'ARG-UNLP-TPG-0000000141',
             'ARG-UNLP-DIS-0000001679', 'ARG-UNLP-ART-0000006126', 'ARG-UNLP-ART-0000007441', 'ARG-UNLP-ART-0000006875', 'ARG-UNLP-TPG-0000000108', 
             'ARG-UNLP-TPG-0000000326', 'ARG-UNLP-ART-0000007663', 'ARG-UNLP-ART-0000007439', 'ARG-UNLP-TPG-0000000100', 'ARG-UNLP-ART-0000006926', 
             'ARG-UNLP-TDG-0000000175', 'ARG-UNLP-DIS-0000001659', 'ARG-UNLP-TDG-0000000162', 'ARG-UNLP-ART-0000007431', 'ARG-UNLP-ART-0000007982',
             'ARG-UNLP-TPG-0000000322', 'ARG-UNLP-TDG-0000000174', 'ARG-UNLP-ART-0000006880', 'ARG-UNLP-TDG-0000000184', 'ARG-UNLP-TDG-0000000337',
             'ARG-UNLP-TPG-0000000122', 'ARG-UNLP-TDG-0000000925', 'ARG-UNLP-TDG-0000000922', 'ARG-UNLP-TPG-0000000107', 'ARG-UNLP-TPG-0000000130',
             'ARG-UNLP-DIS-0000001638', 'ARG-UNLP-TDG-0000000130', 'ARG-UNLP-TDG-0000000132', 'ARG-UNLP-ART-0000007909', 'ARG-UNLP-TDG-0000000145',
             'ARG-UNLP-TPG-0000000124', 'ARG-UNLP-TPG-0000000131', 'ARG-UNLP-DIS-0000001642', 'ARG-UNLP-ART-0000006925', 'ARG-UNLP-TDG-0000000112',
             'ARG-UNLP-TDG-0000000350', 'ARG-UNLP-TDG-0000000354', 'ARG-UNLP-DIS-0000001681', 'ARG-UNLP-TDG-0000000125', 'ARG-UNLP-ART-0000006881',
             'ARG-UNLP-ART-0000006130', 'ARG-UNLP-ART-0000007665', 'ARG-UNLP-DIS-0000001641', 'ARG-UNLP-TDG-0000000187', 'ARG-UNLP-ART-0000007443',
             'ARG-UNLP-ART-0000006486', 'ARG-UNLP-DIS-0000001683', 'ARG-UNLP-TDG-0000000178', 'ARG-UNLP-TDG-0000000369', 'ARG-UNLP-TPG-0000000111',
             'ARG-UNLP-ART-0000006877', 'ARG-UNLP-TPG-0000000115', 'ARG-UNLP-TPG-0000000119', 'ARG-UNLP-TDG-0000000164', 'ARG-UNLP-ART-0000007904',
             'ARG-UNLP-TDG-0000000153', 'ARG-UNLP-TDG-0000000381', 'ARG-UNLP-ART-0000007908', 'ARG-UNLP-TPG-0000000321', 'ARG-UNLP-TDG-0000000207', 
             'ARG-UNLP-ART-0000006154', 'ARG-UNLP-TDG-0000000209', 'ARG-UNLP-TDG-0000000342', 'ARG-UNLP-ART-0000007438', 'ARG-UNLP-DIS-0000001678',
             'ARG-UNLP-TPG-0000000118'}

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
