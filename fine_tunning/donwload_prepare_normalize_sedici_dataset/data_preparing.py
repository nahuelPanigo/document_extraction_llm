DATA_FOLDER= "/home/nahuel/Documents/tesis/fine_tunning/data/sedici/"
JSON_FOLDER=DATA_FOLDER+"jsons/"
PDF_FOLDER=DATA_FOLDER+"pdfs/"
XML_FOLDER=DATA_FOLDER+"xmls/"
TEXT_FOLDER=DATA_FOLDER+"texts/"
JSON_FILE = "metadata_sedici_files.json"
VALID_ACCENTS = "áéíóúüñÁÉÍÓÚÜÑ"
import time

#from multiprocessing import Pool, cpu_count
import json
import os
import pdfplumber
import re
import csv
import unicodedata


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def remove_specific_unicode(text, unicode_value):
    # Convertir el valor Unicode de hexadecimal a decimal
    unicode_value = int(unicode_value, 16)
    # Filtrar caracteres basados en su valor Unicode
    filtered_text = ''.join(c for c in text if ord(c) != unicode_value)
    return filtered_text

def remove_accents(text):
    # Normaliza el texto para descomponer los caracteres acentuados
    text = unicodedata.normalize('NFD', text)
    # Elimina los caracteres diacríticos (acentos)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Normaliza el texto nuevamente a la forma compuesta
    text = unicodedata.normalize('NFC', text)
    return text

def print_unicode_info(char):
    # Obtener el valor Unicode en decimal
    unicode_decimal = ord(char)
    # Obtener el valor Unicode en hexadecimal
    unicode_hex = hex(unicode_decimal)
    # Obtener la categoría del carácter
    unicode_category = unicodedata.category(char)
    return unicode_decimal, unicode_hex, unicode_category


def normalize_text(text):
    # Convertir a minúsculas
    text = text.lower()
    # Reemplazar saltos de línea y tabulaciones con espacios
    text = re.sub(r'[\n\t]', ' ', text)
    # Eliminar caracteres no imprimibles excepto los signos de puntuación y caracteres visibles
    text = re.sub(r'[^\x20-\x7E\u00A0-\u00FF]', '', text)  # Mantener caracteres imprimibles ASCII y algunos caracteres extendidos
    # Eliminar acentos
    text = remove_accents(text)
    text = remove_specific_unicode(text,'b4')
    # Reemplazar múltiples espacios con un solo espacio
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def search_text_in_pdf(value, pdf_text):
    if isinstance(value, list):
        res = []
        for elem in value:
            res.append(search_text_in_pdf(elem,pdf_text))
        return res
    pattern = re.compile(re.escape(normalize_text(value)), re.IGNORECASE)
    matches = pattern.findall(normalize_text(pdf_text))
    return bool(matches)


def read_data(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)

def write_data_in_json(json_file,data):
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
def process_pdf_data_wrapper(args):
    return process_pdf_data(*args)

def make_col_split(value):
    if isinstance(value,list):
        col = []
        for elem in value:
            col.extend([word.rstrip(',') for word in elem.split()])
        return col
    return [word.rstrip(',') for word in value.split()]

def save_text_file(text,id):
    with open(os.path.join(TEXT_FOLDER, f"{id}.txt"), "w") as text_file:
        text_file.write(text)


def process_pdf_data(pdf_path, reg, pdf_id):
    results = {}
    print(pdf_id)
    pdf_text = extract_text_from_pdf(pdf_path)
    save_text_file(pdf_text,pdf_id)
    auth_and_contr = ["sedici.creator.person","sedici.contributor.director"
                      ,"sedici.contributor.juror","sedici.contributor.codirector"]
    for key, value in reg.items():
        if key in auth_and_contr :
            result = search_text_in_pdf(make_col_split(value),pdf_text)
        else:
            result = search_text_in_pdf(value, pdf_text)
        results[key] = (value, result)
    time.sleep(35)
    return pdf_id, results

def verificar_metadatos():
    data_dict = read_data(JSON_FOLDER+JSON_FILE)
    filenames = os.listdir(TEXT_FOLDER)
    keys = [filename.replace(".txt","") for filename in filenames]
    pdf_paths = [(os.path.join(PDF_FOLDER, f"{key}.pdf"), reg, key) for key, reg in data_dict.items() if not key in keys]
    results = []
    for item in pdf_paths:
        results.append(process_pdf_data(item[0], item[1], item[2]))
    return results


def exportar_a_csv(combined_results):
    with open(DATA_FOLDER+"restuls4.csv", mode='w', newline='', encoding='utf-8') as file:
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

# #print(ord('´'))
#data = read_data(JSON_FOLDER+JSON_FILE)
# key = "ARG-UNLP-TPG-0000001028"
# print(process_pdf_data(os.path.join(PDF_FOLDER, f"{key}.pdf"),data[key],key)[1]["dc.title"])



