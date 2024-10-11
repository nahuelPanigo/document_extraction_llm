import pandas as pd
import  json
from bs4 import BeautifulSoup
from constant import JSON_FOLDER,DATASET_SEDICI_URL_BASE,PDF_URL,DATA_FOLDER
from utils.read_and_write_files import write_to_json
import requests
import re
import os
import time
from utils.pdf_reader import PdfReader
from utils.read_and_write_files import write_to_json



PDF_FOLDER = DATA_FOLDER / "pdfs2/"
DATASET_FILENAME = "metadata_sedici_files3.json"

def get_list_sedici_files_and_meta(page_param):
    response = requests.get(DATASET_SEDICI_URL_BASE+str(page_param))
    soup = BeautifulSoup(response.content, features="lxml-xml")
    return soup.find_all("oai_dc:dc")

def sedici_file_and_meta_page(record,dc_identifier_url):
    resp = requests.get(dc_identifier_url+ "?show=full")
    sp = BeautifulSoup(resp.content, 'html.parser')
    return sp.find_all("tr")

def extract_metadata_from_tag(tag,metadata):
    td_elements = tag.find_all("td")
    key = td_elements[0].text
    value = td_elements[1].text
    if(key in metadata):
        if isinstance(metadata[key], list):
            metadata[key].append(value)
        else:
            metadata[key] = [metadata[key],value]
    else:
        metadata[key] = value

def download_file(metadata,dc_identifier_url,final_metadata):
    try:
        dc_id=dc_identifier_url.split("e/")[1]
        id=dc_id.replace("/","-")
        resp = requests.get(PDF_URL+dc_id+"/Documento_completo.pdf?sequence=1&isAllowed=y")
        if resp.status_code == 200:
            file_path = PDF_FOLDER / f"{id}.pdf"
            with open(file_path, "wb") as f:
                f.write(resp.content)
            print("bajo",id)
            final_metadata[id] = metadata
        else:
            print("no esta el archivo")
    except:  
        print("no hay archivo")



def download_files_and_metadata():
    array_parameter_page = [x*100 for x in range(1400,1410)]
    final_metadata = {}
    #100 resultados por paginas iteramos por 40 paginas
    for page_param in array_parameter_page:
        records =  get_list_sedici_files_and_meta(page_param)
        #iteramos por los 100 registros de cada pagina
        for record in records:
            dc_identifier_url=record.find_all("dc:identifier")[0].text
            tr_elements = sedici_file_and_meta_page(record,dc_identifier_url)
            metadata = {}
            #obtenemos la metadata de cada archivo
            for tr in tr_elements:
                extract_metadata_from_tag(tr,metadata)
            #obtenemos el archivo
            download_file(metadata,dc_identifier_url,final_metadata)
        time.sleep(40)
    write_to_json(JSON_FOLDER / DATASET_FILENAME ,final_metadata,"utf-8")



def get_documents():
    all_files=os.listdir(DATA_FOLDER)
    ids=[]
    for file in all_files:
        if(has_permit_extension(file)):
            ids.append(file.replace(".pdf",""))
    return ids


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
    with open(JSON_FOLDER+DATASET_FILENAME, 'r', encoding='latin-1') as jsonfile:
        data_dict = json.load(jsonfile)
    docs = get_files()
    data = []
    strategyReader = PdfReader()
    for doc in docs:
        text = strategyReader.extract_text_with_xml_tags(doc[0])
        data_dict[doc[2]]["original_text"] = text
        data_dict[doc[2]] = {k: v for k, v in data_dict[doc[2]].items() if k != "abstract"}
        data.append(data_dict[doc[2]])

    write_to_json(JSON_FOLDER+DATASET_FILENAME,data,'utf-8')



download_files_and_metadata()
#add_text_input_to_Dataset()