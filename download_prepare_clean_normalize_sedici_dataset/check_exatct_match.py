import json
import pprint
import pandas as pd
import re 


def read_data_json(json_filename, enc):
    with open(json_filename, 'r', encoding=enc) as file:
        return json.load(file)

def write_to_json(json_filename, data, enc):
    with open(json_filename, 'w', encoding=enc) as jsonfile:
        json.dump(data, jsonfile, indent=4)

# Cargar datos y definir las estructuras iniciales
filename = "metadata_sedici_and_text_checked.json"
filenameoriginal = "metadata_sedici_and_text.json"
data = read_data_json(filename, "utf-8")
data_original = read_data_json(filenameoriginal, "utf-8")

exact_match_fields = ["rights", "rightsurl", "sedici.uri", "dc.uri"]



cc_pattern = re.compile(
    r"""
    (                           
        # Variante larga (Creative Commons ... versión)
        (?:licencia\s*)?creative\s*commons
        .*?(?:\b\d+\.\d+\b)?     # allow optional version

    |   # Variante abreviada (CC BY, CC-BY-NC-SA, etc.)
        cc[-\s]*by               # CC BY or CC-BY
        (?:[-\s]?[a-z]+)*        # NC, SA, etc.
        (?:\s*\d+\.\d+(?:\s*\w+)?)?  # version like 4.0, 3.0 Unported (optional)

    |   # Variante con URL oficial
        https?://creativecommons\.org/licenses/
        [\w\-/]*
        (?:/\d+\.\d+[^/\s]*)?    # version optional, may have suffix
    )
    """,
    flags=re.IGNORECASE | re.VERBOSE
)

def case_rights(doc_id, value, text):
    if value:
        m = cc_pattern.search(text)
        if m:
            return True
    return False


def is_in_text(id,key,value,text,metadata):
    if key == "rights":
       return case_rights(id,value,text)
    elif key == "dc.uri":
        if value:
            if value.lower() in text.lower():
                return True
            return False
        return True
    else:
        if value:
            if value.lower() in text.lower():  
                return True
            return False
        return False
    


ok_metadata = {"rights": ([],[]), "sedici.uri": ([],[]), "dc.uri": ([],[])}



for step, metadatas in data.items():
    for metadata in metadatas:
        id = metadata["id"]
        record = data_original[id]
        for key in ok_metadata.keys():
            if key in metadata and key in record and record[key] and metadata[key]:
                if is_in_text(id,key,metadata[key],metadata["original_text"],metadata):
                    ok_metadata[key][0].append(id)
                else:
                    ok_metadata[key][1].append(id)
            # else:
            #     if key in metadata and key in record:
            #         print(f"the key is {key} and the value is {metadata[key]} and in the original metadata is {record[key]}")
            #     else:
            #         print(f"the key is {key} is not in the metadata and in the original metadata")
for key in ok_metadata.keys():
    print(f"{key}: {len(ok_metadata[key][0])} ok, {len(ok_metadata[key][1])} not ok")


print(f"for key rights the first 10 elements ok are: {ok_metadata['rights'][0][:10]}")
print(f"for key dc.uri the first 10 elements ok are: {ok_metadata['dc.uri'][0][:10]}")
print(f"for key sedici.uri the first 10 elements ok are: {ok_metadata['sedici.uri'][0][:10]}")
print(f"for key rights the first 10 elements not ok are: {ok_metadata['rights'][1][:10]}")
print(f"for key dc.uri the first 10 elements not ok are: {ok_metadata['dc.uri'][1][:10]}")  
print(f"for key sedici.uri the first 10 elements not ok are: {ok_metadata['sedici.uri'][1][:10]}")

