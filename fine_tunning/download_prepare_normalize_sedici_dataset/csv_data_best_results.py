import pandas as pd
from constant import DATA_FOLDER,JSON_FOLDER,CSV_FOLDER
from utils.read_and_write_files import write_to_json,read_data_json
import ast
import json

# csv con los matchs
csv_file =  "results_full_pdf_text_patter_ids3.csv"
#csv_file =  "results_full_pfd_text.csv"
check_json_file = "metadata_to_check4.json"
#json to read metadata to make results dict and remove false determinate attr
metadata_json = "final_metadata_Chekced2.json"
metadata_json1 = "metadata_sedici_files2.json"
values_to_add =["dc.language","dc.description.abstract","dc.subject","dc.title","dc.type",
                "sedici.creator.person","sedici.subject.materias","mods.originInfo.place",
                "sedici.relation.journalTitle","sedici.relation.journalVolumeAndIssue",
                "sedici.identifier.issn","sedici.title.subtitle",#"sedici.date.exposure",
                "sedici.contributor.director","sedici.contributor.codirector","sedici.identifier.isbn",
                "sedici.rights.license","sedici.rights.uri","sedici.relation.isRelatedWith",
                "sedici.identifier.uri","dc.identifier.uri","sedici.contributor.editor",
                "sedici.contributor.compiler","dc.publisher","dc.date.issued","sedici.contributor.colaborator",
                "sedici.institucionDesarrollo","thesis.degree.name","thesis.degree.grantor","sedici.relation.event"
                ]#,"sedici.description.fulltext","sedici.subtype"]


#make dict results only with keys from values_to_add and if all the keys avg is more than min_avg
def make_dict_best_averge_metadata(csv_file,min_avg):
    df = pd.read_csv(csv_file)
    actual_id=  df["id"].iloc[0]
    results = {}
    r = {}
    col_pass = []# ["dc.subject","dc.type","dc.title","sedici.subject.materias","dc.description.abstract","sedici.relation.journalVolumeAndIssue" ,"sedici.relation.journalTitle"]
    for index, row in df.iterrows():
        if(row["clave"] in values_to_add):
            id = row["id"]
            res = ast.literal_eval(row["resultado"])
            if(id != actual_id):
                avg = sum(r.values())/len(r.values())
                if(avg > min_avg):
                    r["avg"] = avg
                    results[actual_id] = r
                r = {}
                actual_id = id
            try:
                if(row["clave"] in col_pass):
                    print(row["clave"],id)
                    r[row["clave"]] = 1
                elif(isinstance(res,list)):
                    r[row["clave"]]=sum(res)/len(res)
                else:
                    r[row["clave"]]=int(res)
            except:
                print(res)
    return results


def make_dict_avg_by_types(results):
    types = {}
    for key in results.keys():
        for k,v in results[key].items():
            if(k not in types):
                types[k] = {}
                types[k]["sum"] = 0
                types[k]["total"] = 0
            types[k]["sum"] +=v
            types[k]["total"] +=1 
    return types


#make dict with the metadata of the approved_ids(ids with more than 90% giid attr) and only the attr filtered
def make_final_metadata(approved_ids):
    dict_metadata =  read_data_json(JSON_FOLDER / metadata_json ,"utf-8")
    dict_metadata ={
    k: {x: y for x, y in v.items() if x in values_to_add}
    for k, v in dict_metadata.items()
    if k in approved_ids
    }


#remove journaltitle origin place, issn, isbn and date exposure if not in the text and make json with attr to check for each document
def make_dict_values_to_check(results):
    final_dict = {}
    dict_metadata =  read_data_json(JSON_FOLDER / metadata_json ,"utf-8")
    values_to_chage = ["sedici.relation.journalTitle","mods.originInfo.place","sedici.identifier.issn","sedici.date.exposure","sedici.identifier.isbn"]
    values_to_ignore = ["sedici.relation.journalTitle","dc.type","mods.originInfo.place","dc.subject","sedici.subject.materias","sedici.identifier.issn","sedici.date.exposure","sedici.identifier.isbn"]
    for key in results.keys():
        r = []
        for k,v in results[key].items():
            if(k in values_to_ignore):
                if(k in values_to_chage):
                    try:
                        dict_metadata[key].pop(k)
                    except:
                        print("ERRR no esta la key",k)
            elif(int(v) != 1) and (k != "avg"):
                r.append(k)
        if r:
            final_dict[key]  = r
    #write_to_json(JSON_FOLDER+metadata_json,dict_metadata,"utf-8")
    return final_dict

results = make_dict_best_averge_metadata(DATA_FOLDER / csv_file,0.1)
#dict_to_check=make_dict_values_to_check(results)
#new_dict_metadata = make_final_metadata(results.keys())
#write_to_json(JSON_FOLDER / "final_metadata_Chekced2.json",new_dict_metadata,"utf-8")
#write_to_json(JSON_FOLDER / check_json_file,dict_to_check,"utf-8")

#make avg for each key (avg of author, avg of director, avg of title)...
types=make_dict_avg_by_types(results)
for k,v in types.items():
    print("prom para k",k,"es",v["sum"]/v["total"]," los val son: ",v["sum"]," ",v["total"])
print(len(results.keys()))

