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


def _regex_repair(text: str):
    """
    Last-resort repair for broken LLM JSON output.
    Extracts all "key": value pairs via regex, ignoring orphan values.
    For duplicate keys keeps the one with the longest value (more information).
    Handles string values and array values.
    """
    pattern = re.compile(
        r'"([^"]+)"\s*:\s*'
        r'('
          r'"[^"]*"'            # string value
          r'|\[[^\]]*\]'        # array value  (no nested arrays)
          r'|true|false|null'   # primitives
          r'|-?\d+(?:\.\d+)?'  # numbers
        r')'
    )
    pairs = {}
    for m in pattern.finditer(text):
        key, value = m.group(1), m.group(2)
        if key not in pairs or len(value) > len(pairs[key]):
            pairs[key] = value
    if not pairs:
        return None
    result = {}
    for key, value in pairs.items():
        try:
            result[key] = json.loads(value)
        except Exception:
            result[key] = value.strip('"')
    return result


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
            prediction_json = json.loads(cleaned_prediction, strict=False)
        except json.JSONDecodeError:
            try:
                prediction_json = _regex_repair(cleaned_prediction)
                if prediction_json is None:
                    return MD_E["ERROR_PARSING_OUTPUT"], MD_E["CODE_ERROR_PARSING_OUTPUT"]
            except Exception:
                return MD_E["ERROR_PARSING_OUTPUT"], MD_E["CODE_ERROR_PARSING_OUTPUT"]
    return prediction_json, None