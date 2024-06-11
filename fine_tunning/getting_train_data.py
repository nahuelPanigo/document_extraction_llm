import pandas as pd
import  json
from constant import DATA_FOLDER,COLUMNS_DATA,ORIGINAL_FILENAME,DATASET_URL_BASE,DATASET_FILENAME
import requests
import re
import os
from pdf_reader import PdfReader


def parse_json():
    data = []
    with open(DATA_FOLDER+ORIGINAL_FILENAME, encoding='latin-1') as f:
        for line in f:
            doc = json.loads(line)
            lst = [doc['id'], doc['title'], doc['abstract'], doc['categories'],doc['authors']]
            data.append(lst)

    df = pd.DataFrame(data=data, columns=COLUMNS_DATA).sample(n=10_000, random_state=68)
    data_dict = {}
  
    # Iterate over the first 500 rows of the DataFrame
    for _, row in df.head(500).iterrows():
        data_dict[row['id']] = {
            "title": row['title'],
            "cat": row['categories'],
            "abstract": row['abstract'],
            "authors": row['authors']
        }

    # Convert the dictionary to a JSON file
    with open(DATA_FOLDER+DATASET_FILENAME, 'w') as json_file:
        json.dump(data_dict, json_file, indent=4)
    
    return data_dict

def download_files(data_dict):
    final_dict = {}
    for id in data_dict.keys():
        response = requests.get(DATASET_URL_BASE + id)
        try:
            filename = DATA_FOLDER+id+".pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            final_dict[id] = data_dict[id]
        except Exception as e:
            print(e)
        # Convert the dictionary to a JSON file
    with open(DATA_FOLDER+DATASET_FILENAME, 'w') as json_file:
        json.dump(final_dict, json_file, indent=4)

def has_permit_extension(filename):
    permit_extensions = [".pdf"]
    # Construct a regular expression pattern to match any of the permitted extensions
    pattern = r"(" + "|".join(re.escape(ext) for ext in permit_extensions) + r")$"
    return bool(re.search(pattern, filename))

def get_ext(archivo):
    return archivo.split(".")[-1]

def get_id(archivo):
    return archivo.split("."+get_ext(archivo))[0]

def get_files():
    archivos = os.listdir(DATA_FOLDER)
    return [(DATA_FOLDER+archivo,get_ext(archivo),get_id(archivo)) for archivo in archivos if has_permit_extension(archivo)]


def add_text_input_to_Dataset():
    with open(DATA_FOLDER+DATASET_FILENAME, 'r', encoding='latin-1') as jsonfile:
        data_dict = json.load(jsonfile)
    docs = get_files()
    data = []
    strategyReader = PdfReader()
    for doc in docs:
        text = strategyReader.extract_text_with_xml_tags(doc[0])
        data_dict[doc[2]]["original_text"] = text
        data_dict[doc[2]] = {k: v for k, v in data_dict[doc[2]].items() if k != "abstract"}
        data.append(data_dict[doc[2]])


    # Save the filtered dictionary back to the JSON file
    with open(DATA_FOLDER+DATASET_FILENAME, 'w', encoding='latin-1') as jsonfile:
        json.dump(data, jsonfile, indent=4)


data_dict = parse_json()
download_files(data_dict)
add_text_input_to_Dataset()