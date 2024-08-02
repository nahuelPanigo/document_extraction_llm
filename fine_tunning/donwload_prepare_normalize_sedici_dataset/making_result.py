DATA_FOLDER= "/home/nahuel/Documents/tesis/fine_tunning/data/sedici/"
JSON_FOLDER=DATA_FOLDER+"jsons/"
PDF_FOLDER=DATA_FOLDER+"pdfs/"
XML_FOLDER=DATA_FOLDER+"xmls/"
TEXT_FOLDER=DATA_FOLDER+"texts/"
JSON_FILE = "metadata_sedici_files.json"

from multiprocessing import Pool, cpu_count
import json
import os
import re
import csv
import unicodedata

def remove_accents(text):
    # Normaliza el texto para descomponer los caracteres acentuados
    text = unicodedata.normalize('NFD', text)
    # Elimina los caracteres diacríticos (acentos)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Normaliza el texto nuevamente a la forma compuesta
    text = unicodedata.normalize('NFC', text)
    return text

def normalize_text(text):
    # Convertir a minúsculas
    text = text.lower()
    # Reemplazar saltos de línea y tabulaciones con espacios
    text = re.sub(r'[\n\t]', ' ', text)
    # Reemplazar múltiples espacios con un solo espacio
    text = re.sub(r'\s+', ' ', text).strip()
    text = remove_accents(text)
    return text


def search_text_in_pdf(value, file_text):
    if isinstance(value, list):
        res = []
        for elem in value:
            res.append(search_text_in_pdf(elem,file_text))
        return res
    pattern = re.compile(re.escape(normalize_text(value)), re.IGNORECASE)
    matches = pattern.findall(normalize_text(file_text))
    return bool(matches)

def read_data(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)


def process_pdf_data_wrapper(args):
    return process_txt_data(*args)

def make_col_split(value):
    if isinstance(value,list):
        col = []
        for elem in value:
            col.extend([word.rstrip(',') for word in elem.split()])
        return col
    return [word.rstrip(',') for word in value.split()]

def extract_text_from_file(file_path):
    with open(file_path, 'r') as content_file:
        content_list = content_file.read().strip()
    return content_list

def process_txt_data(file_path, reg, pdf_id):
    results = {}
    pdf_text = extract_text_from_file(file_path)
    auth_and_contr = ["sedici.creator.person","sedici.contributor.director"
                    ,"sedici.contributor.juror","sedici.contributor.codirector"]
    for key, value in reg.items():
        if key in auth_and_contr :
            result = search_text_in_pdf(make_col_split(value),pdf_text)
        else:
            result = search_text_in_pdf(value, pdf_text)
        results[key] = (value, result)
    return pdf_id, results

def verificar_metadatos():
    filenames = os.listdir(TEXT_FOLDER)
    keys = [filename.replace(".txt","") for filename in filenames]
    data_dict = read_data(JSON_FOLDER+JSON_FILE)
    txt_paths = [(os.path.join(TEXT_FOLDER, f"{key}.txt"), data_dict[key], key) for key in keys]
    with Pool(2) as pool:
        results = pool.map(process_pdf_data_wrapper, txt_paths)
    return results


def exportar_a_csv(combined_results):
    with open(DATA_FOLDER+"restuls.csv", mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["id", "clave", "valor","valor_normalizado" ,"resultado"])
        for id_key, value_dict in combined_results.items():
            for key, (value, result) in value_dict.items():
                if isinstance (value,list):
                    norm_text = [normalize_text(text) for text in value]
                else:
                    norm_text = normalize_text(value)
                writer.writerow([id_key, key, value,norm_text, result])


results = verificar_metadatos()
combined_results = {}
for pdf_id, result_dict in results:
    combined_results[pdf_id] = result_dict
exportar_a_csv(combined_results)
