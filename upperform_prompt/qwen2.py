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
- Si un valor no se puede verificar con certeza, debe dejarse la key con el value string vacio.
- La salida debe  ser un json bien formateado con cada uno de los campos que se pasaron en la entrada. de la forma clave : valorCorrecto.
---

[METADATOS A VALIDAR]

"""


keys_general = ["creator", "title", "subtitle", "subject", "rights", "rightsurl", "date", "originPlaceInfo.", "isRelatedWith"]
keys_tesis = keys_general +["codirector", "director", "degree.grantor", "degree.name"]
keys_libro = keys_general +["publisher", "isbn", "compiler"]
keys_articulo = keys_general + ["journalTitle", "journalVolumeAndIssue", "issn", "event"]


texto_a_procesar = """
 <think>                                                                                                     Okay, let's tackle this. The user provided a list of metadata to validate against a given academic text. I need to check each field and ensure the values are correct. Let me go through each one step by step.                                                                                                                                                First, the creator is "Paloma, María Inés". Looking at the text, the author is mentioned as "PALOMAA MARIA HERAS". Wait, that's a typo in the name. The correct name should be Paloma, María Inés, so I need to correct that. But the original metadata says "Paloma, María Inés", which matches the corrected version of the author's name in the text. So that's okay.                                                                                                                                                                                                                                 Next, the title is "Centro de Encipe Intergenerencional". The text has "C.E.I. CENTRO DE ENCUENTRO INTERGENERACIONAL Á1 RESIDENCIA PARA LA 3RA EDAD PALOMA MARIA HERAS". The title in the metadata is "Centro de Encipe Intergenerencional", but the text has "Centro de Encuentro Intergeneracional". The "Encipe" is likely a typo for "Encuentro". So the title should be corrected to "Centro de Encuentro Intergeneracional".                                                                                                                                                                       Subtitle is "RESIDENCIA PARA LA 3RA EDAD PALOMA MARIA HERAS". The text has "RESIDENCIA PARA LA 3RA EDAD PALOMA MARIA HERAS", so that's correct. The subtitle is accurate.                                                                                                                                                                                      Subject is "Ingeniero urbanismo". The text mentions "Facultad de Arquitectura Nacional y Urbanismo", so the subject should be "Arquitectura" or "Arquitectura y Urbanismo". But the metadata says "Ingeniero urbanismo". Hmm, maybe that's a mistake. The correct field would be "Arquitectura" as the main subject here. But the user's metadata says "Ingeniero urbanismo", which is a bit off. Wait, the text is about a project for a senior center, so maybe the subject is "Turismo" as per the metadata. Wait, the metadata says "subject: Ingeniero urbanismo", but in the text, the author is working on a project in architecture, so maybe "Arquitectura" is more accurate. But the metadata says "Ingeniero urbanismo", which might be a mistake. However, the user's metadata has "subject: Ingeniero urbanismo", but the text is about architecture. Wait, the original metadata's subject is "Ingeniero urbanismo", but in the text, the author is from the Facultad de Arquitectura, so maybe the subject should be "Arquitectura". But the user's metadata says "Ingeniero urbanismo", which is a different field. Hmm, this might be an error. However, the user's metadata is what we need to validate against the text. The text mentions "Facultad de Arquitectura Nacional y Urbanismo", so the subject might be "Arquitectura y Urbanismo". But the metadata says "Ingeniero urbanismo". I need to check if that's correct. The user's metadata says "Ingeniero urbanismo", but the text is about a project in architecture, so maybe that's incorrect. But the user's metadata is the one to validate. Wait, the user provided the metadata to validate. Wait, the user says: "Recibirás: 1. Un texto completo correspondiente a un documento académico. 2. y distintos metadatos extraídos que deberas validar." So the metadata is the one to be validated against the text. So if the text is about architecture, then the subject should be "Arquitectura" or "Arquitectura y Urbanismo". But the metadata says "Ingeniero urbanismo". So that's incorrect. So I need to correct that. But the user's metadata says "subject: Ingeniero urbanismo", but the text is about a project in architecture. Therefore, the correct subject should be "Arquitectura y Urbanismo" or "Arquitectura". So I need to change that.                                                                                                                                                                                                        Next, rights: "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)" which is correct. The rightsurl is also correct.                                                                                                                                                                                                     Date is "2019-01-01", but in the text, the defense date is "JUEVES 19 DE DICIEMBRE 2019". So the date in the metadata is incorrect. The correct date should be "2019-12-19".                                                                                                                                                                                   originPlaceInfo.: The text mentions "Facultad de UNIVERSIDAD Arquitectura NACIONAL y Urbanismo DE LA PLATA", so the origin place is "La Plata, Argentina". But the metadata doesn't have a field for originPlaceInfo. Wait, the metadata has "originPlaceInfo.: " (with a colon and a space), but in the input, it's just "originPlaceInfo.: " (empty). Wait, looking back, the user's metadata includes "originPlaceInfo.: " which is empty. But the text has "Facultad de UNIVERSIDAD Arquitectura NACIONAL y Urbanismo DE LA PLATA", so the origin place is "La Plata, Argentina". So the originPlaceInfo should be "La Plata, Argentina". But the metadata's originPlaceInfo is empty. So I need to fill that in.                                                                                                                              isRelatedWith: The metadata has this as empty. The text mentions "TUTOR: PABLO BARROSO" which is the director, but the metadata's "isRelatedWith" is empty. However, the text also mentions "codirector: " (empty), but in the text, the director is "PABLO BARROSO". Wait, the metadata says "director: PabLO BARROSO", and in the text, the tutor is "PABLO BARROSO". So "isRelatedWith" is probably the co-director, but in the text, the co-director isn't mentioned. The text has "TUTOR: PABLO BARROSO", but no co-director. So "isRelatedWith" is empty. The metadata says "isRelatedWith: " (empty), which is correct.                                                                                                                                                                                                                     codirector: The metadata has this as empty. The text doesn't mention a co-director, so it's correct to leave it empty.                                                                                                                                                                                                                                         degree.grantor: "Universidad Nacional de La Plata" which is correct as per the text.                                                                                                                                                      degree.name: "Especialista en Turismo" but in the text, the project is "PROYECTO FINAA L DE CARRERA TALLER VERTICAL DE ARQUITECTURA N°1: SBARRA - MORANO - CUETO RUA". The degree name should be "Especialista en Arquitectura" or "Especialista en Arquitectura y Urbanismo". But the metadata says "Especialista en Turismo", which is incorrect. The text is about a project in architecture, so the degree should be "Especialista en Arquitectura".                                                                                                                                                 So, the corrected metadata would have:                                                                                                                                                                                                    creator: Paloma, María Inés (corrected from the text's "PALOMAA MARIA HERAS")                                                                                                                                                             title: Centro de Encuentro Intergeneracional (corrected from "Encipe" to "Encuentro")                                                                                                                                                     subtitle: RESIDENCIA PARA LA 3RA EDAD PALOMA MARIA HERAS (correct)                                                                                                                                                                        subject: Arquitectura y Urbanismo (corrected from "Ingeniero urbanismo" to match the text's context)                                                                                                                                      rights: same as before                                                                                                                                                                                                                    rightsurl: same as before                                                                                                                                                                                                                 date: 2019-12-19 (corrected from 2019-01-01)                                                                                                                                                                                              originPlaceInfo: La Plata, Argentina (from the text's "Facultad de UNIVERSIDAD Arquitectura NACIONAL y Urbanismo DE LA PLATA")                                                                                                                                                                                                                                 isRelatedWith: (empty, as no co-director mentioned)                                                                                                                                                                                       codirector: (empty)                                                                                                                                                                                                                       director: PabLO BARROSO (corrected from "PABLO BARROSO" to "PabLO BARROSO")                                                                                                                                                               degree.grantor: same                                                                                                                                                                                                                      degree.name: Especialista en Arquitectura (corrected from "Turismo")                                                                                                                                                                      Wait, but the original metadata says "degree.name: Especialista en Turismo", but the text is about a project in architecture. So that's incorrect. So the degree name should be "Especialista en Arquitectura".                                                                                                                                                So all these fields need to be adjusted accordingly. The user's metadata may have some errors that need correction based on the text.                                                                                                     </think>                                                                                                                                                                                                                                  {                                                                                                                      "creator": "Paloma, María Inés",                                                                                     "title": "Centro de Encuentro Intergeneracional",                                                                    "subtitle": "RESIDENCIA PARA LA 3RA EDAD PALOMA MARIA HERAS",                                                        "subject": "Arquitectura y Urbanismo",                                                                               "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",               "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",                                                    "date": "2019-12-19",                                                                                                "originPlaceInfo": "La Plata, Argentina",                                                                            "isRelatedWith": "",                                                                                                 "codirector": "",                                                                                                    "director": "PabLO BARROSO",                                                                                         "degree.grantor": "Universidad Nacional de La Plata",                                                                "degree.name": "Especialista en Arquitectura"                                                                      }     
"""

def extract_text_from_ollama(text):
    dict = text.split("</think>")[1]
    dict = dict.strip()
    json.loads(dict)
    return dict

def extract_text(request):
    dict = json.loads(request)
    text = dict["data"]["text"]
    return " ".join(text.split()[:500])

if __name__ == "__main__":
    #print(extract_text_from_ollama(texto_a_procesar))
    load_dotenv()
    token_orchestrator = os.getenv("ORCHESTRATOR_TOKEN")
    token_extractor = os.getenv("EXTRACTOR_TOKEN")
    #llamada a la api


    filename = PDF_FOLDER / "10915-151542.pdf"
    type = "Tesis"
    request = make_requests_xml_text(filename,token_extractor,True)
    text  =  extract_text(request)
    print(text)
    start = time.time()
    metadata = upload_file(filename,token_orchestrator,True,type,deepanalize=False)
    print(metadata)
    metadata = metadata["data"]
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
            model='qwen3:8b',
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
