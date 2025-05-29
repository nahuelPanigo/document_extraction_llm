from transformers import LEDTokenizer, LEDForConditionalGeneration
# from transformers import LongformerTokenizer, LongformerModel
# from transformers import AutoTokenizer,AutoModel
from ...constants import MODEL_PARAMETERS as MD_P
import json
from ...errors import MODEL_ERRORS as MD_E
from ...constants import PROMPT_GENERAL,PROMPT_ARTICULO,PROMPT_TESIS,PROMPT_LIBRO
import re

# BASE_MODEL_LED="mrm8488/longformer-base-4096-spanish"
# tokenizer = LEDTokenizer.from_pretrained(BASE_MODEL_LED)
# model = LEDForConditionalGeneration.from_pretrained(BASE_MODEL_LED)


# from transformers import AutoTokenizer, AutoModelForCausalLM
# from huggingface_hub import login
# from dotenv import load_dotenv
# import os

# load_dotenv()
# token = os.getenv("TOKEN_HUGGING_FACE")
# login(token=token)
# tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B-Instruct")
# model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B-Instruct")

# tokenizer = AutoTokenizer.from_pretrained("mrm8488/longformer-base-4096-spanish")
# model = AutoModel.from_pretrained("mrm8488/longformer-base-4096-spanish")
from transformers import AutoTokenizer



model_dir= MD_P["LOCATION"]
tokenizer = LEDTokenizer.from_pretrained(MD_P["NAME"])
#tokenizer = AutoTokenizer.from_pretrained(MD_P["NAME"])
model = LEDForConditionalGeneration.from_pretrained(model_dir)

def get_prompt(type):
    if type == "General":
        return PROMPT_GENERAL
    if type == "Articulo":
        return PROMPT_ARTICULO
    if type == "Tesis":
        return PROMPT_TESIS
    return PROMPT_LIBRO


def normalice_latin_char(text):
        text = text.replace("\\r\\n", " ")
        text = re.sub(r'\\[Rp/c]', '', text)  # Si hay más casos, agrégalos aquí
    # 2️⃣ Si quedan secuencias válidas (\uXXXX o \n, \r, etc.), aplicar unicode_escape
        if re.search(r'\\u[0-9A-Fa-f]{4}|\\[nr]', text):  
            text = bytes(text, "utf-8").decode("unicode_escape")
        text = re.sub(r'"\[(.*?)\]"', r'[\1]', text) 
        text = text.replace("\�", "¿")
        return text


def model_extraction(text,type):
    try: 
        prompt = get_prompt(type)
        final_prompt = f"{prompt} Document: {text}"
        inputs = tokenizer(final_prompt, return_tensors="pt", max_length=MD_P["MAX_TOKENS_INPUT"], truncation=True)   
        outputs = model.generate(**inputs, max_length=MD_P["MAX_TOKENS_INPUT"])
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True, errors="replace")
    except Exception as e:
        print("el error fue: ",e)
        return MD_E["ERROR_OPENING_MODEL"],MD_E["CODE_ERROR_OPENING_MODEL"]
    try:
        prediction_json = json.loads(prediction)
    except json.JSONDecodeError:
        prediction = prediction.replace("'", '"')  
        prediction = prediction.replace("\"[", "[")
        prediction = prediction.replace("]\"", "]")
        prediction = prediction.replace("\�", "¿")
        prediction = normalice_latin_char(prediction)
        cleaned_prediction = prediction.encode('latin1', 'replace').decode('utf-8', 'replace')
        try:
            prediction_json = json.loads(cleaned_prediction,strict=False)
        except json.JSONDecodeError as e:
            print(f"el error fue: {e}")
            return MD_E["ERROR_PARSING_OUTPUT"],MD_E["CODE_ERROR_PARSING_OUTPUT"]
    return(prediction_json),None  # None for: no error has occurred

