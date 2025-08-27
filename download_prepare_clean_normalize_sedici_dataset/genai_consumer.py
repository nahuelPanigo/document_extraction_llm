# from transformers import LEDForConditionalGeneration, LEDTokenizer
from google import genai
import os
from dotenv import load_dotenv
from constants import PROMPT_CLEANER_METADATA,APROX_TOK_PER_SOL,GENAI_REQUEST_LIMIT,GENAI_MODEL
import threading
import time
import pandas as pd
import json
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json
from utils.colors.colors_terminal import Bcolors

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)



# Define requests limits --global var--
requests_limits = GENAI_REQUEST_LIMIT.copy()

#control vars
runnning = True
lock = threading.Lock()


def consume_llm(metadata,text):
    input = f"""{PROMPT_CLEANER_METADATA}  
        - Metadata: {metadata}
        - Text: {text}"""
    
    response = client.models.generate_content(
        model=GENAI_MODEL,
        contents=input,
    )
    return response.text


def make_request(metadata, extracted_text):
    global requests_limits
    while True:
        #wait until updates requests limits per min
        while requests_limits["req_per_min"] == 0 or requests_limits["req_per_day"] == 0 or requests_limits["tok_per_min"] < APROX_TOK_PER_SOL:
            print(f"{Bcolors.WARNING}No se puede realizar la solicitud, esperando...{Bcolors.ENDC}",requests_limits)
            time.sleep(5)  
        response = consume_llm(metadata, extracted_text)
        with lock:
            requests_limits["req_per_min"] -= 1
            requests_limits["req_per_day"] -= 1
            requests_limits["tok_per_min"] -= APROX_TOK_PER_SOL
        print(f"{Bcolors.OKGREEN}Solicitud realizada: req_per_min={requests_limits['req_per_min']}, req_per_day={requests_limits['req_per_day']}, tok_per_min={requests_limits['tok_per_min']}{Bcolors.ENDC}")
        return response

def save_json(id, data,output_filename,extracted_text):
    try:
        metadata = read_data_json(output_filename,"utf-8")
        data = data.strip()
        if data.startswith("```json") and data.endswith("```"):
            data = data[7:-3].strip()
        else:
            print(data[7:-3].strip())
        data = json.loads(data)
        metadata[id] = data
        metadata[id]["original_text"] = extracted_text
        write_to_json(output_filename, metadata, "utf-8")
    except json.JSONDecodeError as e:
        print(f"{Bcolors.FAIL}Decode Error in JSON: {e}{Bcolors.ENDC}") 
        print(data)


def reset_limits():
    while runnning:
        time.sleep(60)
        with lock:
            requests_limits["req_per_min"] = 15
            requests_limits["tok_per_min"] = 250000
            print(f"{Bcolors.OKBLUE}Request Limits: req_per_min=15, tok_per_min=250000{Bcolors.ENDC}")


def get_metadata_to_process(metadatas_filename,final_json_filename):
    new_metadatas = read_data_json(metadatas_filename,"utf-8")
    if not (final_json_filename).exists():
        return new_metadatas
    final_metadatas = read_data_json(final_json_filename,"utf-8")
    return {
        k: v for k, v in new_metadatas.items() if k not in final_metadatas.keys()
    }


# Función para procesar las filas del CSV
def process_metadatas(metadatas_filename,final_json_filename):
    print(f"{Bcolors.OKGREEN}extracting metadatas{Bcolors.ENDC}")
    metadatas = get_metadata_to_process(metadatas_filename,final_json_filename)
    print(f"{Bcolors.OKGREEN}processing metadatas{Bcolors.ENDC}")
    already_processed =read_data_json(final_json_filename,"utf-8")
    metadatas_to_process = {k: v for k, v in metadatas.items() if k not in already_processed.keys()}
    for index,metadata in  metadatas_to_process.items():
        try:
            extracted_text = metadata["original_text"]
            id = index
            dict_metadata = {k: v for k, v in metadata.items() if k not in ["original_text", "dc.type"]}
            response = make_request(dict_metadata, extracted_text)
            if(response):
                save_json(id,response,final_json_filename,extracted_text)
        except Exception as e:
            print(f"cannot process the row {index} error: {e}")



def clean_metadata(metadata_filename,final_json_filename):
    global runnning
    reset_thread = threading.Thread(target=reset_limits)
    reset_thread.daemon = True 
    reset_thread.start()
    process_metadatas(metadata_filename,final_json_filename)
    runnning = False
