from constants import CSV_FOLDER, CSV_SEDICI_FILTERED, PDF_FOLDER, JSON_FOLDER, DATASET_TYPE,VALID_TYPES,DATA_FOLDER
import pandas as pd
from utils.text_extraction.read_and_write_files import write_to_json,read_data_json
from download_prepare_clean_normalize_sedici_dataset.download_data import download_files
from download_prepare_clean_normalize_sedici_dataset.extract_text_make_dataset import extract_text
from utils.consume_apis.consume_extractor import make_requests_only_text
import json
from utils.colors.colors_terminal import Bcolors    
import os
from dotenv import load_dotenv

TEXT_FOLDER = DATA_FOLDER /  "texts2"

dataset = {
    "Libro": [],
    "Tesis": [],    
    "Articulo": [],
}

def get_ids_per_type():
    df = pd.read_csv(CSV_FOLDER / CSV_SEDICI_FILTERED)
    for _, row in df.iterrows():
        if row["dc.type"] in VALID_TYPES:
            dataset[row["dc.type"]].append(row.get("id",""))
        else:
            print(f"El documento es de tipo {row['dc.type']}")

    write_to_json(JSON_FOLDER / DATASET_TYPE, dataset, "utf-8")
    return  dataset

def write_to_text(text, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def extract_texts(ids):
    for key in ids:
        try:
            filename = PDF_FOLDER / f"{key}.pdf"
            text = make_requests_only_text(filename,os.getenv("EXTRACTOR_TOKEN"))
            write_to_text(text,TEXT_FOLDER / f"{key}.txt")
            print(f"{Bcolors.OKGREEN} texto extraido {key} {Bcolors.ENDC}")
        except:
            print(f"{Bcolors.FAIL} error en el pdf {key} {Bcolors.ENDC}")


if __name__ == "__main__":
    load_dotenv()
    data =  read_data_json(JSON_FOLDER / DATASET_TYPE, "utf-8")
    ids = data["Libro"] + data["Tesis"] + data["Articulo"]
    extract_texts(ids)
