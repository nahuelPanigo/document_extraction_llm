from constants import JSON_FOLDER,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,DATASET_WITH_METADATA_AND_TEXT_DOC
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json
import pandas as pd



if __name__ == "__main__":
    issn_ok = []
    issn_not_ok = []
    isbn_ok = []
    isbn_not_ok = []
    data = read_data_json(JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC, "utf-8")
    for id,metadata in data.items():
        if "issn" in metadata:
            try:
                if metadata["issn"] in metadata["original_text"]:
                    issn_ok.append(id)
                else:
                    issn_not_ok.append(id)
            except:
                e = 1
        if "isbn" in metadata:
            try:
                if metadata["isbn"] in metadata["original_text"]:
                    isbn_ok.append(id)
                else:
                    isbn_not_ok.append(id)
            except: 
                e = 2

    print(f"ISSN ok: {len(issn_ok)}")
    print(f"ISSN not ok: {len(issn_not_ok)}")
    print(f"ISBN ok: {len(isbn_ok)}")
    print(f"ISBN not ok: {len(isbn_not_ok)}")


    for id  in issn_not_ok[:10]:
        print(id,data[id]["issn"])
    
    for id  in isbn_not_ok[:10]:
        print(id,data[id]["isbn"])

    uniques_cant_issn = {}

    for id  in issn_not_ok:
        issn = data[id]["issn"]
        if issn not in uniques_cant_issn:
            uniques_cant_issn[issn] = 1
        else:
            uniques_cant_issn[issn] += 1
    
    uniques_cant_isbn = {}

    for id  in isbn_not_ok:
        isbn = data[id]["isbn"]
        if id not in uniques_cant_isbn:
            uniques_cant_isbn[isbn] = 1
        else:    
            uniques_cant_isbn[isbn] += 1

    
    print(uniques_cant_issn)
    print(uniques_cant_isbn)