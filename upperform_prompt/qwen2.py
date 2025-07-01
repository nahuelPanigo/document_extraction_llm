# from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
# import torch
import time
import ollama
from constants import PDF_FOLDER
from utils.consume_apis.consume_extractor import make_requests_xml_text
from utils.consume_apis.consume_orchestrator import upload_file
from dotenv import load_dotenv
import os
import json

PROMPT ="""
Eres un validador estricto de metadatos académicos presentes en los libros.

Recibirás:
1. Un texto completo correspondiente a un documento académico.
2. y distintos metadatos extraídos que deberas validar.

Tu tarea es:
- Ver cada uno de los campos y verificar que el valor sea el correcto.
- Debes corregir cualquier valor incorrecto.
- Completar valores faltantes **solo si pueden confirmarse claramente en el texto**.
- Si un valor no se puede verificar con certeza, debe dejarse en vacio.
- La salida tiene que ser un json bien formateado con cada uno de los campos que se pasaron en la entrada.
---

[METADATOS A VALIDAR]

"""


keys_general = ["creator", "title", "subtitle", "subject", "rights", "rightsurl", "date", "originPlaceInfo.", "isRelatedWith"]
keys_tesis = keys_general +["codirector", "director", "degree.grantor", "degree.name"]
keys_libro = keys_general +["publisher", "isbn", "compiler"]
keys_articulo = keys_general + ["journalTitle", "journalVolumeAndIssue", "issn", "event"]


def extract_text(request):
    dict = json.loads(request)
    text = dict["data"]["text"]
    return " ".join(text.split()[:2000])

if __name__ == "__main__":
    load_dotenv()
    token_orchestrator = os.getenv("ORCHESTRATOR_TOKEN")
    token_extractor = os.getenv("EXTRACTOR_TOKEN")
    #llamada a la api


    filename = PDF_FOLDER / "10915-151583.pdf"
    type = "Tesis"
    request = make_requests_xml_text(filename,token_extractor,True)
    text  =  extract_text(request)
    start = time.time()
    metadata = upload_file(filename,token_orchestrator,True,type,deepanalize=False)["data"]
    print(f"Time taken in extractor service: {time.time() - start}")

    print(metadata)
    #obtencion de metadata y agregado de keys faltantes

    for key in keys_tesis:
        if key not in metadata:
            metadata[key] = ""

    # llamada qwen para validar metadatos
    fields_str = "\n".join([f"{key}: {metadata[key]}" for key in keys_tesis])

    prompt = f"""{PROMPT}{fields_str}[FIN METADATOS A VALIDAR]```
    [TEXTO]: {text} [FIN TEXTO]"""

    print(prompt)

    try:
        start = time.time()
        response = ollama.generate(
            model='qwen3:4b',
            prompt=prompt,
            stream=False, # Set to True for streaming responses
            # You can add other options here as well, e.g.:
            # temperature=0.7,
            # top_p=0.9
        )
        print("content:", response['response'].strip())
        print(f"Time taken: {time.time() - start}")

    except Exception as e:
        print(f"Error communicating with Ollama: {e}")




    # model_id = "Qwen/Qwen3-4B"  # o Qwen2 si estás usando otro

    # bnb_config = BitsAndBytesConfig(
    #     load_in_4bit=True,
    #     bnb_4bit_compute_dtype=torch.float16,
    #     bnb_4bit_use_double_quant=True,
    #     bnb_4bit_quant_type="nf4"
    # )

    # tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

    # model = AutoModelForCausalLM.from_pretrained(
    #     model_id,
    #     device_map="cuda",
    #     quantization_config=bnb_config,
    #     trust_remote_code=True
    # )

    # # Generación de texto simple
    # start = time.time()
    # inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    # outputs = model.generate(**inputs, max_new_tokens=1024)
    # end = time.time()

    # print(tokenizer.decode(outputs[0]))
    # print(f"Tiempo de respuesta: {end - start} segundos")

    # print(f"cantidad de tokens de input: {inputs['input_ids'].shape[1]}")
    # print(f"Cantidad de tokens de output: {outputs.shape[0]}")
