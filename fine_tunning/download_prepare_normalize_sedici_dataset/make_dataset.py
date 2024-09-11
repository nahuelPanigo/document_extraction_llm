import pandas as pd
import  json
from constant import JSON_FOLDER,TXT_FOLDER,DATASET_WITH_TEXT_DOC2,DATASET_WITH_METADATA_CHECKED,DATA_FOLDER
from utils.read_and_write_files import read_data_json,read_data_txt,detect_encoding,write_to_json
from utils.normalice_data import normalize_text

TXT_FOLDER2 = DATA_FOLDER / "texts2"

def add_text_input_to_dataset():
    metadata_filename = JSON_FOLDER / DATASET_WITH_METADATA_CHECKED
    enc = detect_encoding(metadata_filename)['encoding']
    dict_metadata = read_data_json(metadata_filename,enc)
    for k in dict_metadata.keys():
        txt_filename = TXT_FOLDER / f"{k}.txt"
        enc = detect_encoding(txt_filename)['encoding']
        text = read_data_txt(txt_filename,enc)
        #uncomment tu normalize
        #text = normalize_text(text)
        dict_metadata[k]["original_text"] = text
    # Save the filtered dictionary back to the JSON file
    write_to_json(JSON_FOLDER / DATASET_WITH_TEXT_DOC2,dict_metadata,"utf-8")



add_text_input_to_dataset()