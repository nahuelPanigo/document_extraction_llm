# from transformers import LEDTokenizer, LEDForConditionalGeneration
# from transformers import LongformerTokenizer, LongformerModel
# from transformers import AutoTokenizer,AutoModel
from ...constants import PROMPT,MODEL_PARAMETERS as MD_P
import json
from ...errors import MODEL_ERRORS as MD_E


# BASE_MODEL_LED="mrm8488/longformer-base-4096-spanish"
# tokenizer = LEDTokenizer.from_pretrained(BASE_MODEL_LED)
# model = LEDForConditionalGeneration.from_pretrained(BASE_MODEL_LED)


from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("TOKEN_HUGGING_FACE")
login(token=token)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B-Instruct")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B-Instruct")



# tokenizer = AutoTokenizer.from_pretrained("mrm8488/longformer-base-4096-spanish")
# model = AutoModel.from_pretrained("mrm8488/longformer-base-4096-spanish")

# model_dir= MD_P["LOCATION"]
# tokenizer = LEDTokenizer.from_pretrained(MD_P["NAME"])
# model = LEDForConditionalGeneration.from_pretrained(model_dir)

def model_extraction(text):
    try: 
        inputs = tokenizer(f"{PROMPT} Document: {text[:4000]}", return_tensors="pt", max_length=MD_P["MAX_TOKENS_INPUT"], truncation=True)     
        outputs = model.generate(**inputs, max_length=MD_P["MAX_TOKENS_INPUT"] + 512 )
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        print("el error fue: ",e)
        return MD_E["ERROR_OPENING_MODEL"],MD_E["CODE_ERROR_OPENING_MODEL"]
    try:
        print(prediction)
        prediction_json = json.loads(prediction)
    except json.JSONDecodeError:
        prediction = prediction.replace("'", '"')  
        try:
            prediction_json = json.loads(prediction)
        except json.JSONDecodeError as e:
            return MD_E["ERROR_PARSING_OUTPUT"],MD_E["CODE_ERROR_PARSING_OUTPUT"]
    return(prediction_json),None  # None for: no error has occurred

