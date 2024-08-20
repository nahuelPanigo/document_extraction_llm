import os
import requests
from constant import JSON_FOLDER,XML_FOLDER,PDF_FOLDER,DATASET_FILENAME,GROBID_URL
from utils.read_and_write_files import read_data_json,write_to_json



#make a str extracting type from file [TDG,TPG,ART,DIS] + type + subtype
def get_key_format(key,dict):
    file_tag = key.split("-")[2]
    dc_type = dict["dc.type"]
    sedici_subtype = dict["sedici.subtype"]
    return file_tag+"-"+dc_type+"-"+sedici_subtype

#make json all attributes for each type_subtype  {TDG {tot=cant1 dc.type=cant2}...}
def make_files_types_json():
    data = read_data_json(os.path.join(JSON_FOLDER,DATASET_FILENAME),"utf-8")
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
    write_to_json(os.path.join(JSON_FOLDER,"metadata_by_type.json"),dict,"utf-8")


#make json type_subtype for each attr  {dc.type{TDG:cant1,TPG:cant2..}..}
def make_attr_json():
    data = read_data_json(os.path.join(JSON_FOLDER,DATASET_FILENAME),"utf-8")
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
    write_to_json(os.path.join(JSON_FOLDER,"metadata_by_type2.json"),dict,"utf-8")

#make json withe the final subtypes and agrouping in general commons attr
def make_final_json():
    data2 = read_data_json(os.path.join(JSON_FOLDER, "metadata_by_type2.json"),"utf-8")
    data = read_data_json(os.path.join(JSON_FOLDER, "metadata_by_type.json"),"utf-8") 
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
    
    write_to_json(os.path.join(JSON_FOLDER,"metadata_by_type3.json"),final_json,"utf-8")

#send pdf to GROBID services and save xml
def make_xml():
    id_con_errores=[]
    data = read_data_json(os.path.join(JSON_FOLDER, DATASET_FILENAME),"utf-8")     
    for id_key in data.keys():
        pdf_filename = id_key + ".pdf"
        pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
        with open(pdf_path, 'rb') as pdf_file:
            pdf = {'input': pdf_file}
            response = requests.post(GROBID_URL, files=pdf, headers={})
            if response.status_code == 200:
                xml_filename = id_key + ".xml"
                xml_filepath = os.path.join(XML_FOLDER, xml_filename)
                with open(xml_filepath, 'wb') as xml_file:
                    xml_file.write(response.content)
                print(f"XML generado y guardado para {id_key}")
            else:
                id_con_errores.append(id_key)
                print(f"Error al procesar {pdf_filename}: {response.status_code}")
    return id_con_errores

#delete pdf with no xml(GROBID bad responses)
def delete_files_no_xml():
    xmls = [x.replace(".xml","") for x in os.listdir(XML_FOLDER)]
    pdfs_to_delete = [x for x in os.listdir(PDF_FOLDER) if(x.replace(".pdf","") not in xmls)]
    for filename in pdfs_to_delete:
        os.remove(PDF_FOLDER+filename)

#removes pdf xml and json keys corresponding to unnecessary subtype files
def delete_unused_file_type():
    files_type = {("TPG","Libro","Libro") : [] , ("REP","Articulo","Articulo") : [] , 
                  ("DIS","Articulo","Articulo") :[] , ("REV","Articulo", "Revision") : [],("REV","Articulo","Revision"):[],
                  ("PAR","Imagen en movimiento","Video"):[],("PAR","Imagen fija","Imagen fija"):[],("TPG","Libro","Libro"):[],
                  ("TDG","Tesis","Tesis de maestria"):[],("TPG","Tesis","Tesis de grado"):[]}
    data = read_data_json(os.path.join(JSON_FOLDER, DATASET_FILENAME),"utf-8")
    final_data = {}
    for key in data.keys():
        try:
            tuple_key_type_subtype = (key.split("-")[2],data[key]["dc.type"],data[key]["sedici.subtype"])
            print(tuple_key_type_subtype)
            if(tuple_key_type_subtype in files_type):
                files_type[tuple_key_type_subtype].append(key)
                os.remove(PDF_FOLDER+key+".pdf")
                os.remove(XML_FOLDER+key+".xml")
            else:
                final_data[key] = data[key]
        except:
            print(key)
    write_to_json(os.path.join(JSON_FOLDER,DATASET_FILENAME),final_data,"utf-8")
    return files_type

#group_json()
#print(make_xml())
#print(make_final_json())
#delete_files_no_xml()
#make_attr_json()
#make_files_types_json()
#print(delete_unused_file_type())

