import json
import os
import requests
import pdfplumber
import re

ROUTE = "/home/nahuel/Documents/tesis/fine_tunning/data/sedici/"
JSON_ROUTE = ROUTE + "jsons/"
XML_ROUTE = ROUTE + "xmls/"
PDF_ROUTE = ROUTE + "pdfs/"
METADATA_FILE = "metadata_sedici_files.json"
URL_GROBID_SERVICES = "http://localhost:8070/api/processFulltextDocument"



#return data from json filename args
def get_data_from_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data2 = json.load(file)         
    return data2

#write data to json filename args
def write_data_to_json_file(filename,data):
    with open(filename, 'w', encoding='utf-8') as final_output:
        json.dump(data, final_output, ensure_ascii=False, indent=4)

#make a str extracting type from file [TDG,TPG,ART,DIS] + type + subtype
def get_key_format(key,dict):
    file_tag = key.split("-")[2]
    dc_type = dict["dc.type"]
    sedici_subtype = dict["sedici.subtype"]
    return file_tag+"-"+dc_type+"-"+sedici_subtype

#make json all attributes for each type_subtype  {TDG {tot=cant1 dc.type=cant2}...}
def make_files_types_json():
    data = get_data_from_json_file(os.path.join(JSON_ROUTE,METADATA_FILE))
    dict = {}       
    for id_key in data.keys():
        new_key = get_key_format(id_key,data[id_key])
        if(not new_key in dict):
            dict[new_key] = {}
            dict[new_key]["total"] = 1
        else: 
            dict[new_key]["total"] = dict[new_key]["total"] + 1
            for key in data[id_key].keys():
                if(key in dict[new_key]):
                    dict[new_key][key] = dict[new_key][key] + 1
                else:
                    dict[new_key][key] = 1
    write_data_to_json_file(os.path.join(JSON_ROUTE,"metadata_by_type.json"),dict)


#make json type_subtype for each attr  {dc.type{TDG:cant1,TPG:cant2..}..}
def make_attr_json():
    data = get_data_from_json_file(os.path.join(JSON_ROUTE,METADATA_FILE))
    dict = {}       
    for id_key in data.keys():
        new_key = get_key_format(id_key,data[id_key])
        for key in data[id_key].keys():
            if (not key in dict):
                dict[key] = {}
            else:
                if(new_key in dict[key]):
                    dict[key][new_key] = dict[key][new_key]+1
                else:
                    dict[key][new_key] = 1
    write_data_to_json_file(os.path.join(JSON_ROUTE,"metadata_by_type2.json"),dict)

#make json withe the final subtypes and agrouping in general commons attr
def make_final_json():
    data2 = get_data_from_json_file(os.path.join(JSON_ROUTE, "metadata_by_type2.json"))
    data = get_data_from_json_file(os.path.join(JSON_ROUTE, "metadata_by_type.json")) 
    cant_type_subtype= len(data.keys())   
    final_json = {y : [] for y in data.keys()}
    final_json ["general"] = []

    #itero por los diccionarios de atributos (atributo , {type:cant...})
    for attribute_tuple in data2.items():
        type_subtype= []
        #voy iterando por los type(type,cant)
        for type_tuple in attribute_tuple[1].items():
            type_subtype.append(type_tuple[0])
            if(type_tuple[1]/data[type_tuple[0]]["total"]< 0.1):
                print(type_tuple, data[type_tuple[0]]["total"],attribute_tuple[0])
        if(len(type_subtype)==cant_type_subtype):
            final_json["general"].append(attribute_tuple[0])
        else:
            for t_s in type_subtype:
                final_json[t_s].append(attribute_tuple[0])
    
    write_data_to_json_file(os.path.join(JSON_ROUTE,"metadata_by_type3.json"),final_json)

#send pdf to GROBID services and save xml
def make_xml():
    id_con_errores=[]
    with open(os.path.join(JSON_ROUTE, METADATA_FILE), 'r', encoding='utf-8') as file:
        data = json.load(file)      
        for id_key in data.keys():
            pdf_filename = id_key + ".pdf"
            pdf_path = os.path.join(PDF_ROUTE, pdf_filename)
            with open(pdf_path, 'rb') as pdf_file:
                pdf = {'input': pdf_file}
                response = requests.post(URL_GROBID_SERVICES, files=pdf, headers={})
                if response.status_code == 200:
                    xml_filename = id_key + ".xml"
                    xml_filepath = os.path.join(XML_ROUTE, xml_filename)
                    with open(xml_filepath, 'wb') as xml_file:
                        xml_file.write(response.content)
                    print(f"XML generado y guardado para {id_key}")
                else:
                    id_con_errores.append(id_key)
                    print(f"Error al procesar {pdf_filename}: {response.status_code}")
    return id_con_errores

#delete pdf with no xml(GROBID bad responses)
def delete_files_no_xml():
    xmls = [x.replace(".xml","") for x in os.listdir(XML_ROUTE)]
    pdfs_to_delete = [x for x in os.listdir(PDF_ROUTE) if(x.replace(".pdf","") not in xmls)]
    for filename in pdfs_to_delete:
        os.remove(PDF_ROUTE+filename)

#removes pdf xml and json keys corresponding to unnecessary subtype files
def delete_unused_file_type():
    files_type = {("TPG","Libro","Libro") : [] , ("REP","Articulo","Articulo") : [] , 
                  ("DIS","Articulo","Articulo") :[] , ("REV","Articulo", "Revision") : [],("REV","Articulo","Revision"):[],
                  ("PAR","Imagen en movimiento","Video"):[],("PAR","Imagen fija","Imagen fija"):[],("TPG","Libro","Libro"):[],
                  ("TDG","Tesis","Tesis de maestria"):[],("TPG","Tesis","Tesis de grado"):[]}
    with open(os.path.join(JSON_ROUTE, METADATA_FILE), 'r', encoding='utf-8') as file:
        data = json.load(file)
    final_data = {}
    for key in data.keys():
        try:
            tuple_key_type_subtype = (key.split("-")[2],data[key]["dc.type"],data[key]["sedici.subtype"])
            print(tuple_key_type_subtype)
            if(tuple_key_type_subtype in files_type):
                files_type[tuple_key_type_subtype].append(key)
                os.remove(PDF_ROUTE+key+".pdf")
                os.remove(XML_ROUTE+key+".xml")
            else:
                final_data[key] = data[key]
        except:
            print(key)
    with open(os.path.join(JSON_ROUTE,METADATA_FILE), 'w', encoding='utf-8') as final_output:
        json.dump(final_data, final_output, ensure_ascii=False, indent=4)    
    return files_type

#group_json()
#print(make_xml())
#print(make_final_json())
#delete_files_no_xml()
#make_attr_json()
#make_files_types_json()
#print(delete_unused_file_type())

