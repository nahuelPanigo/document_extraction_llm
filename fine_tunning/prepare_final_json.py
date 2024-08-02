from constant import JSONS_FOLDER,ORIGINAL_FILENAME
import json



col = {}
with open(JSONS_FOLDER+ORIGINAL_FILENAME, 'r', encoding='latin-1') as jsonfile:
    data_dict = json.load(jsonfile)


for key in data_dict:
    if not data_dict[key]["dc.type"] in col:
        col[data_dict[key]["dc.type"]] = 1
    else:
        col[data_dict[key]["dc.type"]] += 1


total =len(data_dict.keys())

data_training = {k: v*0.8 for k,v in col.items()}
data_test = {k: v*0.1 for k,v in col.items()}
data_validation = {k: v*0.1 for k,v in col.items()}

print(data_training)
print(data_test)
print(data_validation)
print(col)

