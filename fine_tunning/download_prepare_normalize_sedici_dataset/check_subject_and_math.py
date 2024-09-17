from constant import JSON_FOLDER,DATASET_WITH_METADATA_CHECKED
from utils.read_and_write_files import read_data_json
import os


dict_total = {"dc.subject":{},"sedici.subject.materias":{}}

dc_type = set()

def sum_in_dict(first_key,second_key):
    if second_key in dict_total[first_key]:
        dict_total[first_key][second_key]+=1
    else:
        dict_total[first_key][second_key] = 1


filename = os.path.join(JSON_FOLDER, DATASET_WITH_METADATA_CHECKED)

data = read_data_json(filename,"utf-8")
dict_total = {"dc.subject":{},"sedici.subject.materias":{}}



for elem in data.values():
    dc_type.add(elem["dc.type"])
    try:
        for subject in elem["dc.subject"]:
            sum_in_dict("dc.subject", subject)
    except:
        print("no tiene subject")
    try:
        if isinstance(elem["sedici.subject.materias"],list):
            for mat in  elem["sedici.subject.materias"]:
                sum_in_dict("sedici.subject.materias", mat)
        else:
            sum_in_dict("sedici.subject.materias", elem["sedici.subject.materias"])
    except:
        print("no tiene materias")



print(dc_type)