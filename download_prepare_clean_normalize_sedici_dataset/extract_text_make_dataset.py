import os
from utils.text_extraction.pdf_reader import PdfReader
from utils.text_extraction.read_and_write_files import write_to_text,read_data_json,read_data_txt,detect_encoding,write_to_json
from multiprocessing import Pool
from constants import TXT_FOLDER,PDF_FOLDER,COLUMNS_TYPES
from utils.colors.colors_terminal import Bcolors
import pandas as pd

def process_pdf_data_wrapper(args):
    return process_pdf_data(*args)

def process_pdf_data(pdf_path, pdf_id):
    print(pdf_id)
    try:
        pdfreader = PdfReader()
        text = pdfreader.extract_text_with_xml_tags(pdf_path,ocr=True)
        txt_filename=TXT_FOLDER / f"{pdf_id}.txt"
        write_to_text(txt_filename,text)
    except Exception as e:
        print(f"{Bcolors.FAIL}error processing pdf{pdf_id} with error {e}{Bcolors.ENDC}")

def extract_text(selected_ids=None):
    text = [x.replace(".txt",".pdf") for x in os.listdir(TXT_FOLDER)]
    
    if selected_ids:
        pdf_paths = [(str(PDF_FOLDER / f"{id_val}.pdf"), id_val) for id_val in selected_ids if f"{id_val}.pdf" not in text and (PDF_FOLDER / f"{id_val}.pdf").exists()]
    else:
        pdf_paths = [(os.path.join(PDF_FOLDER,x),x.replace(".pdf","")) for x in os.listdir(PDF_FOLDER) if x not in text]   
    
    with Pool(2) as pool:
        pool.map(process_pdf_data_wrapper, pdf_paths)
    return

def make_json_metadata(metadata_filename,csv_filename,selected_ids):
    df = pd.read_csv(csv_filename)
    df = df[df['id'].isin(selected_ids)]
    rename_dict = {key: value["rename"] for key, value in COLUMNS_TYPES.items() if value.get("rename")}
    df = df.rename(columns=rename_dict)
    column_order = [value["rename"] for value in COLUMNS_TYPES.values() if value.get("rename")]
    df = df.reindex(columns=column_order)
    df = df.drop_duplicates(subset='id', keep='first')
    dict_metadata = df.set_index('id').to_dict(orient='index')
    write_to_json(metadata_filename,dict_metadata,"utf-8")

def add_text_input_to_dataset(metadata_filename, metadata_text_filename):
    enc = detect_encoding(metadata_filename)['encoding']
    dict_metadata = read_data_json(metadata_filename, enc)
    texts = [x.replace(".txt", "") for x in os.listdir(TXT_FOLDER)]
    keys_to_iterate = [key for key in dict_metadata.keys() if key in texts]
    filtered_metadata = {}
    for k in keys_to_iterate:
        try:
            txt_filename = TXT_FOLDER / f"{k}.txt"
            enc_txt = detect_encoding(txt_filename)['encoding']
            text = read_data_txt(txt_filename, enc_txt)
            new_entry = dict_metadata[k]
            new_entry["original_text"] = text
            filtered_metadata[k] = new_entry
        except Exception as e:
            print(f"{Bcolors.FAIL} Error processing txt file for id {k} with error {e}{Bcolors.ENDC}")
    write_to_json(metadata_text_filename, filtered_metadata, "utf-8")

def extract_and_make_dataset(metadata_filename,metadata_text_filename,csv_filename,selected_ids):
    ids_with_pdf = [id_val for id_val in selected_ids if (PDF_FOLDER / f"{id_val}.pdf").exists()]
    extract_text(ids_with_pdf)
    make_json_metadata(metadata_filename,csv_filename,ids_with_pdf)
    add_text_input_to_dataset(metadata_filename,metadata_text_filename)


