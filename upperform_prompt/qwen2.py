# from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
# import torch
import time
import ollama
from constants import PDF_FOLDER
from utils.consume_apis.consume_extractor import make_requests_xml_text
from utils.consume_apis.consume_orchestrator import upload_file
from dotenv import load_dotenv
import os

PROMPT ="""
Your task is to review a set of metadata fields automatically extracted from an academic document. You will be given:

1. The full text of the document.
2. A JSON object containing the extracted metadata.

Your job is to:

- Verify if the metadata values in the JSON are accurate by comparing them with the content of the document.
- Correct any incorrect values.
- Fill in missing values only if they can be reliably determined from the text.
- Do **not** guess or invent any values. If a value cannot be confirmed from the text, leave it as `null`.
- Preserve the original structure and field names of the JSON.
- Return **only** the corrected JSON, with no additional explanation or output.

---
Extracted metadata:
```json
"""


keys_general = ["creator", "title", "subtitle", "subject", "rights", "rightsurl", "date", "originPlaceInfo.", "isRelatedWith"]
keys_tesis = keys_general +["codirector", "director", "degree.grantor", "degree.name"]
keys_libro = keys_general +["publisher", "isbn", "compiler"]
keys_articulo = keys_general + ["journalTitle", "journalVolumeAndIssue", "issn", "event"]




if __name__ == "__main__":
    load_dotenv()
    token_llm = os.getenv("LLM_LED_TOKEN")
    token_extractor = os.getenv("EXTRACTOR_TOKEN")
    #llamada a la api

    filename = PDF_FOLDER / "10915-151583.pdf"
    type = "Tesis"
    text = make_requests_xml_text(filename,token_extractor,True)
    metadata = upload_file(filename,token_llm,True,type,deepanalize=False)
    print(metadata)
    
    #obtencion de metadata y agregado de keys faltantes

    for key in keys_tesis:
        if key not in metadata:
            metadata[key] = ""

    # llamada qwen para validar metadatos


    prompt = f"""{PROMPT}{metadata}```
    TEXT: {text}"""



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
