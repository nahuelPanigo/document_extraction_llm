import json
import pandas as pd
from pathlib import Path
from constant import JSON_FILENAMEFINAL
from utils import write_json,read_json

columns_types = {
    'sedici.rights.license' : {'type':str,'cant' : "unique","DCMIID":"dc.rights"},
    'sedici.rights.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.rights"},
    'sedici.relation.isRelatedWith' : {'type':str,'cant' : "unique","DCMIID":"dc.relation"},
    'dc.coverage.spatial' : {'type':str,'cant' : "unique","DCMIID":"dc.coverage"},
    'dc.coverage.temporal' : {'type':str,'cant' : "unique","DCMIID":"dc.coverage"},
    'sedici.identifier.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier"},
    'dc.identifier.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier"},
    'sedici.contributor.editor' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'sedici.contributor.compiler' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'dc.publisher' : {'type':str,'cant' : "unique","DCMIID":"dc.publisher"},
    'dc.date.issued' : {'type': "str",'cant' : "unique","DCMIID":"dc.date"},
    'sedici.contributor.colaborator' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'dc.description.abstract' : {'type':str,'cant' : "many","DCMIID":"dc.description"},
    'sedici.institucionDesarrollo' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'thesis.degree.name' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor.degree.name"},
    'thesis.degree.grantor' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor.degree.grantor"},
    'sedici.relation.event' : {'type':str,'cant' : "unique","DCMIID":"dc.relation"},
    'sedici.identifier.isbn' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier"},
    'sedici.identifier.issn' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier"},
    'dc.title' : {'type':str,'cant' : "unique","DCMIID":"dc.title"},
    'sedici.title.subtitle' : {'type':str,'cant' : "unique","DCMIID":"dc.title"},
    'sedici.creator.person' : {'type':str,'cant' : "unique","DCMIID":"dc.creator"},
    'dc.language' : {'type':str,'cant' : "unique","DCMIID":"dc.language"},
    'dc.subject' : {'type':str,'cant' : "unique","DCMIID":"dc.subject"},
    'sedici.contributor.director' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'sedici.contributor.codirector' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'dc.type' : {'type':str,'cant' : "unique","DCMIID":"dc.type"},
    'sedici.relation.journalTitle' : {'type':str,'cant' : "unique","DCMIID":"dc.title"},
    'sedici.relation.journalVolumeAndIssue' : {'type':str,'cant' : "unique","DCMIID":"dc.relation.journalVolumeAndIssue"},
    'sedici.subject.materias' : {'type':str,'cant' : "unique","DCMIID":"dc.subject"},
    'mods.originInfo.place' : {'type':str,'cant' : "unique","DCMIID":"mods.originInfo.place"},
    'id' : {"type": str},
    'dc.description.filiation' : {'type':str,'cant' : "unique","DCMIID":"dc.description.filiation"},
    'dc.subject.ford' : {'type':str,'cant' : "unique","DCMIID":"dc.subject"}
}


keys = columns_types.keys()

FILENAME = "metadata_correjida.json"
DATA_FOLDER = Path(__file__).parents[1] / "fine_tunning/data/sedici" 
CSV_METADATA = DATA_FOLDER / "sedici_filtered_2018_2024.csv"

def duplicate_file_with_only_correct():
    with open(FILENAME, 'r', encoding='utf-8') as f:
        datos = json.load(f)
        lista = []
        for key,values in datos.items():
            if set(values.keys()).issubset(keys):
                lista.append(key)
            else:
                print(values.keys())
        final_dict = {key:values for key,values in datos.items() if set(values.keys()).issubset(keys)}
    write_json(FILENAME,final_dict)
    return final_dict




if __name__ == "__main__":
    # df = pd.read_csv(CSV_METADATA)
    # metadata = {}
    # with open(FILENAME, 'r', encoding='utf-8') as f:
    #     final_dict = json.load(f)
    # print(len(final_dict))
    # final_dict = duplicate_file_with_only_correct()
    # keys = final_dict.keys()
    # for index,row in df.head(5000).iterrows():
    #     if row["id"] in keys:
    #         id = row["id"]
    #         metadata[id] = row.to_dict()
    # write_json(FILENAME3,metadata)
    # with open(FILENAME2, 'r', encoding='utf-8') as f:
    #     datos = json.load(f)
    # with open(FILENAME3, 'r', encoding='utf-8') as f:
    #     datos2 = json.load(f)
    # count= 0
    # for key,value in datos.items():
    #     value2 = datos2[key]
    #     for k,v in value2.items():
    #         if(pd.notna(v) and k != "dc.description.abstract"):
    #             if k not in value.keys():
    #                 count +=1
    #                 print(key,k,v)
    #                 break
    #             # elif v != value[k]:
    #             #     print(f"esta pero es diferente {k} {highlight_diff(v,value2[k])}")
    #             #     print(v)
    #             #     print(value2[k])
    # print(count)
    #print(len(datos2.keys()))
    # print(len(final_dict))
    print(len(columns_types))
    final_dict =  read_json(JSON_FILENAMEFINAL)

    cants = {}
    dict1 = {}
    dict2 = {}
    for key,dict in final_dict.items():
        cant =  len(dict.keys())
        # if(cant in cants):
        #     cants[cant] +=1
        # else:
        #     cants[cant] = 1
        if(cant < 12):
            dict1[key] = dict
        else:
            dict2[key] = dict
    write_json("metadata_correjida.json",dict1)
    write_json("metadata_correjida2.json",dict2)