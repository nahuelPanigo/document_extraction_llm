from transformers import LEDTokenizer, LEDForConditionalGeneration
from app.constants import MODEL_PARAMETERS as MD_P
from app.constants import PROMPT
import json
from app.errors import MODEL_ERRORS as MD_E

model_dir= MD_P["LOCATION"]
tokenizer = LEDTokenizer.from_pretrained(MD_P["NAME"])
model = LEDForConditionalGeneration.from_pretrained(model_dir)

def model_extraction(text):
    try: 
        inputs = tokenizer(f"{PROMPT} Document: {text}", return_tensors="pt", max_length=MD_P["MAX_TOKENS_INPUT"], truncation=True)
        outputs = model.generate(**inputs, max_length=MD_P["MAX_TOKENS_OUTPUT"])
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
    except:
        return MD_E["ERROR_OPENING_MODEL"],MD_E["CODE_ERROR_OPENING_MODEL"]
    try:
        prediction_json = json.loads(prediction)
    except json.JSONDecodeError:
        prediction = prediction.replace("'", '"')  
        try:
            prediction_json = json.loads(prediction)
        except json.JSONDecodeError as e:
            return MD_E["ERROR_PARSING_OUTPUT"],MD_E["CODE_ERROR_PARSING_OUTPUT"]
    return(prediction_json),None  # None for: no error has occurred

