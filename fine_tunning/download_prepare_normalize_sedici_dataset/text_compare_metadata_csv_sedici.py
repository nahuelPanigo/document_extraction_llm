from multiprocessing import Pool, cpu_count

import os
import re
import csv
import pandas as pd
import time
from utils.colors_terminal import Bcolors

from constant import DATA_FOLDER,JSON_FOLDER,CANT_TOKENS,TOKENS_LENGTH
from utils.normalice_data import normalize_text,build_pattern_issn,build_pattern_volume,build_pattern_license
from utils.read_and_write_files import detect_encoding,read_data_txt

TXT_FOLDER = DATA_FOLDER / "texts3/"

def parse_and_search_patters_ids(value, pdf_text,key):
    try:
        if(key=="sedici.identifier.issn"):
            pattern =  build_pattern_issn(value)
            return re.search(pattern, pdf_text) is not None
        elif(key == "sedici.identifier.isbn"):
            pattern = build_pattern_volume(value)
            return re.search(pattern, pdf_text, re.IGNORECASE) is not None
        else:
            pattern = build_pattern_license(value)
            print(pattern)
            result = re.search(pattern, pdf_text) is not None
            print (result)
            return result
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
    try:
        pdf_text = read_data_txt(file_path,enc)
    except:
        print('\x1b[0;31;40m'+"error en el archivo",file_path,'\x1b[0m')
    try:
        # max_tokens = max((CANT_TOKENS * TOKENS_LENGTH),len(pdf_text))
        # pdf_text = pdf_text[0:max_tokens]
        auth_and_contr = ["sedici.creator.person","sedici.contributor.director"
                        ,"sedici.contributor.juror","sedici.contributor.codirector"]
        issn_isbn_vol_or_licence =["sedici.identifier.issn","sedici.relation.journalVolumeAndIssue","sedici.rights.license"]
        for key, value in reg.items():
            if(value is None) or pd.isna(value):
                continue
            elif(key == "sedici.relation.journalTitle" and value == "Documento de Trabajo del CEDLAS"):
                result = True
            elif(key == "mods.originInfo.place" and value == "Centro de Estudios Distributivos, Laborales y Sociales (CEDLAS)"):
                result = True
            elif(key == "dc.type"and value == "Articulo" and is_art_cedlas(reg)):
                result =  True
            elif key in auth_and_contr:
                result = search_text_in_pdf(make_col_split(value),pdf_text)
            else:
                result = search_text_in_pdf(value, pdf_text)
                if(not result) and (key in issn_isbn_vol_or_licence):
                    result = parse_and_search_patters_ids(value, pdf_text,key)
            results[key] = (value, result)
        return pdf_id, results
    except Exception as e:
        print('\x1b[0;31;40m'+"error en el archivo",pdf_id+'\x1b[0m',e,key,value)
        return pdf_id,{}

def verificar_metadatos():
    #keys = [filename.replace(".txt","") for filename in os.listdir(TXT_FOLDER)]
    keys = ["10915-65740"]
    file_csv = DATA_FOLDER / "sedici_filtered_2018_2024.csv"
    metadata =  pd.read_csv(file_csv)
    txt_paths = []
    for elem in keys:
        try:
           elem_clean = elem.strip()
           txt_paths.append((TXT_FOLDER / f"{elem}.txt",metadata.loc[metadata['id'].astype(str) == elem_clean].to_dict(orient='records')[0],elem_clean))
        except Exception as e:
            print("no encontro el elemento ", metadata.loc[metadata['id'] == elem] , e)
    results = []
    for element in txt_paths:
        results.append(process_txt_data(element[0],element[1],element[2]))
    # with Pool(2) as pool:
    #     results = pool.map(process_pdf_data_wrapper, txt_paths)
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
    # combined_results = {}
    # for pdf_id, result_dict in results:
    #     combined_results[pdf_id] = result_dict
    #     csv_filename= "results_full_pdf_text_patter_ids3.csv"
    #exportar_a_csv(combined_results,"utf-8",csv_filename)



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
