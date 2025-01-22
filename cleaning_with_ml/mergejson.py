from constant import JSON_FILENAME,JSON_FILENAME2,JSON_FILENAME3,JSON_FILENAME4,JSON_FILENAMEFINAL
import json
from utils import read_json,write_json




data = read_json(JSON_FILENAME)
data2 = read_json(JSON_FILENAMEFINAL)
# data2 = read_json(JSON_FILENAME2)
# data3 = read_json(JSON_FILENAME3)
# data4 = read_json(JSON_FILENAME4)

# final_dict = {}
# keys = list(data.keys()) + list(data2.keys()) + list(data3.keys()) + list(data4.keys())
# keys = set(keys)
# for key  in keys:
#     elem = data.get(key, None)
#     elem2 = data2.get(key, None) 
#     elem3 = data3.get(key, None) 
#     elem4 = data4.get(key, None)
#     elems = [elem,elem2,elem3,elem4]
#     elems_unicos = list({tuple(sorted(d.items())) for d in elems if d is not None})
#     elems = [dict(tupla) for tupla in elems_unicos]
#     if(len(elems) > 1):
#         diccionario_con_mas_llaves = max(elems, key=lambda d: len(d.keys()))
#         final_dict [key] = diccionario_con_mas_llaves
#         print("entro aca y los diccionarios eran: ",elems)
#     else:
#         final_dict [key] = elems[0] 
    

print(len(data2))
print(len(data))
for key,elem in data.items():
    data2[key] = elem


write_json(JSON_FILENAMEFINAL,data2)

print(len(data2))
