import threading
import time
import pandas as pd
from genai_consumer import consume_llm
from pdf_reader import PdfReader
import json
from constant import PDF_FOLDER,CSV_METADATA,JSON_FILENAME,APROX_TOK_PER_SOL,JSON_FILENAMEFINAL
from utils import read_json,write_json

# Define requests limits --global var--
requests_limits = {
    "req_per_day": 1500,
    "req_per_min": 15,
    "tok_per_min": 32000,
}
#control vars
runnning = True
lock = threading.Lock()




def make_request(metadata, extracted_text):
    global requests_limits
    while True:
        #wait until updates requests limits per min
        while requests_limits["req_per_min"] == 0 or requests_limits["req_per_day"] == 0 or requests_limits["tok_per_min"] < APROX_TOK_PER_SOL:
            print("No se puede realizar la solicitud, esperando...",requests_limits)
            time.sleep(5)  
        response = consume_llm(metadata, extracted_text)
        with lock:
            requests_limits["req_per_min"] -= 1
            requests_limits["req_per_day"] -= 1
            requests_limits["tok_per_min"] -= APROX_TOK_PER_SOL
        print(f"Solicitud realizada: req_per_min={requests_limits['req_per_min']}, req_per_day={requests_limits['req_per_day']}, tok_per_min={requests_limits['tok_per_min']}")
        return response

def save_json(id, data):
    try:
        metadata = read_json(JSON_FILENAME)
        data = data.strip()
        if data.startswith("```json") and data.endswith("```"):
            print("entro")
            data = data[7:-3].strip()
        else:
            print(data[7:-3].strip())
        data = json.loads(data)
        metadata[id] = data
        write_json(JSON_FILENAME, metadata)
    except json.JSONDecodeError as e:
        print(f"Decode Error in JSON: {e}")
        print(data)




def get_incorrects_to_resend2():
    ids = ["10915-140387","10915-111599","10915-108709"]
    df = pd.read_csv(CSV_METADATA)
    metadata = []
    for id in ids:
        filtered_row = df[df["id"] == id]
        dict_metadata = filtered_row.iloc[0].to_dict()
        metadata.append(metadata.append({k: v for k, v in dict_metadata.items() if not (isinstance(v, float) and pd.isna(v)) and (k != "dc.description.abstract")}))
    return metadata


def get_incorrects_to_resend():
    df = pd.read_csv(CSV_METADATA)
    data = read_json(JSON_FILENAMEFINAL)
    metadata = []
    for index, row in df.iloc[2500:4000].iterrows():
        dict_metadata = row.to_dict()
        if dict_metadata["id"] not in data.keys() :
            metadata.append({k: v for k, v in dict_metadata.items() if not (isinstance(v, float) and pd.isna(v)) and (k != "dc.description.abstract")})
    return metadata[0:1000]

# Función para procesar las filas del CSV
def process_csv():
    #df = pd.read_csv(CSV_METADATA)
    metadatas = get_incorrects_to_resend2()
    reader = PdfReader()
    # id= "10915-68147"
    # row = df[df["id"] == id]
    # dict =  row.to_dict()
    # metadata = {k: v for k, v in dict.items() if not (isinstance(v, float) and pd.isna(v)) and (k != "dc.description.abstract")}
    # filename = f"{id}.pdf"
    # extracted_text = reader.extract_text_with_xml_tags(PDF_FOLDER / filename)
    # if(extracted_text != ""):
    #     response = make_request(metadata, extracted_text)
    #     if(response):
    #         print(id,response)
    #         print("metadata cargara: ")
    #         print(metadata)
    # else:
    #     print("empty extraction")
    for index,metadata in  enumerate(metadatas):
        try:
            dict_metadata = {k: v for k, v in metadata.items() if not (isinstance(v, float) and pd.isna(v)) and (k != "dc.description.abstract")}
            id = metadata["id"]
            filename = f"{id}.pdf"
            extracted_text = reader.extract_text_with_xml_tags(PDF_FOLDER / filename)
            print(extracted_text[0:1000])
            if(extracted_text != ""):
                response = make_request(dict_metadata, extracted_text)
                if(response):
                    save_json(id,response)
            else:
                print("empty extraction")
        except Exception as e:
            print(f"cannot process the row {index} error: {e}")


def reset_limits():
    while runnning:
        time.sleep(60)
        with lock:
            requests_limits["req_per_min"] = 15
            requests_limits["tok_per_min"] = 32000
            print("Request Limits: req_per_min=15, tok_per_min=32000")


def main():
    global runnning
    reset_thread = threading.Thread(target=reset_limits)
    reset_thread.daemon = True 
    reset_thread.start()


    process_csv()
    runnning = False

if __name__ == "__main__":
    main()
    #print(get_incorrects_to_resend()[0])
    #process_csv()