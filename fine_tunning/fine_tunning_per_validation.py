import json
from transformers import LEDTokenizer, LEDForConditionalGeneration
#from transformers import AutoModelForCausalLM , AutoTokenizer,BitsAndBytesConfig
from download_prepare_normalize_sedici_dataset.utils.read_and_write_files import read_data_json,detect_encoding
from constant import JSONS_FOLDER,DATASET_WITH_TEXT_DOC,MAX_TOKENS_INPUT,MAX_TOKENS_OUTPUT,FINAL_MODEL_PATH,PROMPT
import torch
from generate_tokens import get_tokens

filename_dataset = JSONS_FOLDER / DATASET_WITH_TEXT_DOC
enc = detect_encoding(filename_dataset)["encoding"]
dict_dataset =  read_data_json(filename_dataset,enc)

data = {}
total_len = len(dict_dataset)
test_end = int(total_len * 0.8)
items_list = list(dict_dataset.values())
data["test"] = items_list[test_end:int(total_len*0.9)]

# Cargar el tokenizador y el modelo ajustado

tokenizer = LEDTokenizer.from_pretrained(FINAL_MODEL_PATH)
model = LEDForConditionalGeneration.from_pretrained(FINAL_MODEL_PATH)

# # Mover el modelo a la GPU si está disponible
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)

# # Configurar el modelo para inferencia
model.eval()

# # Ejemplo de texto de entrada
input_to_check = data["test"][3]
input_text = input_to_check["original_text"]

input_to_check.pop("original_text")
input_to_check.pop("dc.description.abstract")
# Tokenizar la entrada
inputs = tokenizer(f"{PROMPT}{input_text}", return_tensors="pt", truncation=True, padding=True,max_length=MAX_TOKENS_INPUT)


# Mover datos a la misma GPU/CPU que el modelo
inputs = {k: v.to(device) for k, v in inputs.items()}                   

# Realizar inferencia
with torch.no_grad():
    outputs = model.generate(**inputs,max_new_tokens=MAX_TOKENS_OUTPUT)

# Decodificar la salida
decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("decoded output: ")
print(decoded_output)
print("input to check:")
print(input_to_check)