import json
from app.errors.error import MODEL_ERRORS as MD_E
import  re

def normalice_latin_char(text):
        text = text.replace("\\r\\n", " ")
        text = re.sub(r'\\[Rp/c]', '', text)  # Si hay más casos, agrégalos aquí
    # 2️⃣ Si quedan secuencias válidas (\uXXXX o \n, \r, etc.), aplicar unicode_escape
        if re.search(r'\\u[0-9A-Fa-f]{4}|\\[nr]', text):  
            text = bytes(text, "utf-8").decode("unicode_escape")
        text = re.sub(r'"\[(.*?)\]"', r'[\1]', text) 
        text = text.replace("\�", "¿")
        return text

def extract_text_from_ollama(text):
    try:
        print(text)
        dict = text.split("</think>")[1]
        dict = dict.strip()
        dict = json.loads(dict)
        return dict,None
    except Exception as e:
        return MD_E["ERROR_PARSING_OUTPUT"],MD_E["CODE_ERROR_PARSING_OUTPUT"]


def parse_json(prediction):
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
            return MD_E["ERROR_PARSING_OUTPUT"],MD_E["CODE_ERROR_PARSING_OUTPUT"]
    return(prediction_json),None    