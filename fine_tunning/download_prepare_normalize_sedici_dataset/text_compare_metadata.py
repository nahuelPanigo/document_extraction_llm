from multiprocessing import Pool, cpu_count
import json
import os
import re
import csv

from constant import DATA_FOLDER,DATASET_FILENAME,JSON_FOLDER,XML_FOLDER,CANT_TOKENS,TOKENS_LENGTH
from utils.normalice_data import normalize_text,build_pattern_issn,build_pattern_volume
from utils.read_and_write_files import read_data_json,detect_encoding,read_data_txt

TXT_FOLDER = DATA_FOLDER / "texts2/"

def parse_and_search_patters_ids(value, pdf_text,key):
    try:
        if(key=="sedici.identifier.issn"):
            pattern =  build_pattern_issn(value)
            return re.search(pattern, pdf_text) is not None
        else:
            pattern = build_pattern_volume(value)
            return re.search(pattern, pdf_text, re.IGNORECASE) is not None
    except:
        return False

def search_text_in_pdf(value, file_text):
    if isinstance(value, list):
        res = []
        for elem in value:
            res.append(search_text_in_pdf(elem,file_text))
        return res
    if value.split()[0] == "[Autogenerado]:" :
        return True
    pattern = re.compile(re.escape(normalize_text(value)), re.IGNORECASE)
    matches = pattern.findall(normalize_text(file_text))
    return bool(matches)


def process_pdf_data_wrapper(args):
    return process_txt_data(*args)

def make_col_split(value):
    if isinstance(value,list):
        col = []
        for elem in value:
            col.extend([word.rstrip(',') for word in elem.split()])
        return col
    return [word.rstrip(',') for word in value.split()]

def is_art_cedlas(reg):
    if (reg.get("mods.originInfo.place","") == "Centro de Estudios Distributivos, Laborales y Sociales (CEDLAS)"):
        return True
    return reg.get("sedici.relation.journalTitle","") == "Documento de Trabajo del CEDLAS"     

def process_txt_data(file_path, reg, pdf_id):
    results = {}
    enc=detect_encoding(file_path)['encoding']
    print(pdf_id)
    try:
        pdf_text = read_data_txt(file_path,enc)
        # max_tokens = max((CANT_TOKENS * TOKENS_LENGTH),len(pdf_text))
        # pdf_text = pdf_text[0:max_tokens]
        auth_and_contr = ["sedici.creator.person","sedici.contributor.director"
                        ,"sedici.contributor.juror","sedici.contributor.codirector"]
        issn_isbn_vol =["sedici.identifier.issn","sedici.relation.journalVolumeAndIssue"]
        for key, value in reg.items():
            if(key == "sedici.relation.journalTitle" and value == "Documento de Trabajo del CEDLAS"):
                result = True
            elif(key == "mods.originInfo.place" and value == "Centro de Estudios Distributivos, Laborales y Sociales (CEDLAS)"):
                result = True
            elif(key == "dc.type"and value == "Articulo" and is_art_cedlas(reg)):
                result =  True
            elif key in auth_and_contr :
                result = search_text_in_pdf(make_col_split(value),pdf_text)
            else:
                result = search_text_in_pdf(value, pdf_text)
                if(not result) and (key in issn_isbn_vol):
                    result = parse_and_search_patters_ids(value, pdf_text,key)
            results[key] = (value, result)
        return pdf_id, results
    except:
        print('\x1b[0;31;40m'+"error en el archivo",pdf_id,enc+'\x1b[0m')
        return pdf_id,{}

def verificar_metadatos():
    keys = [filename.replace(".txt","") for filename in os.listdir(TXT_FOLDER)]
    file_json = JSON_FOLDER / f"metadata_sedici_files2.json"
    enc=detect_encoding(file_json)['encoding']
    data_dict = read_data_json(file_json,enc)
    txt_paths = [(os.path.join(TXT_FOLDER, f"{key}.txt"), data_dict[key], key) for key in keys]
    with Pool(2) as pool:
        results = pool.map(process_pdf_data_wrapper, txt_paths)
    return results


def exportar_a_csv(combined_results,enc,csv_filename):
    with open(DATA_FOLDER / f"{csv_filename}", mode='w', newline='', encoding=enc) as file:
        writer = csv.writer(file)
        writer.writerow(["id", "clave", "valor","valor_normalizado" ,"resultado"])
        for id_key, value_dict in combined_results.items():
            for key, (value, result) in value_dict.items():
                if isinstance (value,list):
                    norm_text = [normalize_text(text) for text in value]
                else:
                    norm_text = normalize_text(value)
                writer.writerow([id_key, key, value,norm_text, result])

if __name__ == '__main__':
    results = verificar_metadatos()
    combined_results = {}
    for pdf_id, result_dict in results:
        combined_results[pdf_id] = result_dict
        csv_filename= "results_full_pdf_text_patter_ids2.csv"
    exportar_a_csv(combined_results,"utf-8",csv_filename)



# id="ARG-UNLP-ART-0000000025"
# file_path=TXT_FOLDER+id+".txt"
# enc=detect_encoding(file_path)['encoding']
# data= read_data_json(JSON_FOLDER+DATASET_FILENAME,"utf-8")
# pdf_text = read_data_txt(file_path,enc)
# text=normalize_text(pdf_text[70:100])
# print(text)
# print("-----------------")
# print(data[id]["sedici.creator.person"])
# print(normalize_text(data[id]["sedici.creator.person"]))
# print(search_text_in_pdf(make_col_split(data[id]["sedici.creator.person"]),pdf_text))
# print(make_col_split(data[id]["sedici.creator.person"]))
# # for reg in regs:
# #     record = data[id][reg]
# #     print(record)
# #new_rec = process_txt_data(file_path, data[id], id)
