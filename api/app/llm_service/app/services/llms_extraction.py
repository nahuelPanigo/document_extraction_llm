import json
from app.errors.error import MODEL_ERRORS as MD_E
from dotenv import load_dotenv
from app.services.model_managment import get_model,get_truncation
import re
import os
from app.logging_config import logging
import torch
from app.logging_config import logging
from pathlib import Path

class ModelExtraction:
    def __init__(self):
        load_dotenv()
        base_dir = Path(__file__).resolve().parent.parent
        if  self._str_to_bool(os.getenv("IS_LOCAL_MODEL")):
            model_path = base_dir / os.getenv("MODEL_PATH")
        else:
            model_path = os.getenv("MODEL_PATH")
        model = get_model(os.getenv("MODEL_SELECTED"),quantized=self._str_to_bool(os.getenv("QUANTIZATION")),custom_path=model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.model
        self.model.to(self.device)
        self.tokenizer = model.tokenizer
        self.max_length_input = int(os.getenv("MAX_TOKENS_INPUT", 2048))
        self.max_length_output = int(os.getenv("MAX_TOKENS_OUTPUT", 512))
        self.trunaction = get_truncation(self.tokenizer,os.getenv("TRUNACTION",True))
        self.special_tokens_treatment = self._str_to_bool(os.getenv("SPECIAL_TOKENS_TREATMENT",True))
        self.errors_treatment = os.getenv("ERRORS_TREATMENT","replace")
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _normalice_latin_char(text):
            text = text.replace("\\r\\n", " ")
            text = re.sub(r'\\[Rp/c]', '', text)  # Si hay más casos, agrégalos aquí
        # 2️⃣ Si quedan secuencias válidas (\uXXXX o \n, \r, etc.), aplicar unicode_escape
            if re.search(r'\\u[0-9A-Fa-f]{4}|\\[nr]', text):  
                text = bytes(text, "utf-8").decode("unicode_escape")
            text = re.sub(r'"\[(.*?)\]"', r'[\1]', text) 
            text = text.replace("\�", "¿")
            return text

    @staticmethod
    def _str_to_bool(value):
        return str(value).lower() in ("true", "1", "yes", "on")

    def generate_with_fallback(self,inputs, max_input, max_output):
        if "max_new_tokens" in self.model.generate.__code__.co_varnames:
            self.logger.info(f"using max_new_tokens")
            return self.model.generate(**inputs, max_new_tokens=max_output)
        else:
            self.logger.info(f"using max_length")
            return self.model.generate(**inputs, max_length=max_input + max_output)


    def model_extraction(self,final_prompt):
        try: 
            self.logger.info(f"loading model with device: {self.device} max input: {self.max_length_input} max output: {self.max_length_output} and truncation: {self.trunaction}")
            inputs = self.tokenizer(final_prompt, return_tensors="pt", max_length=self.max_length_input, truncation=self.trunaction) 
            inputs = {k: v.to(self.device) for k, v in inputs.items()}  
            self.logger.info(f"generating with model")
            outputs  = self.generate_with_fallback(inputs, self.max_length_input, self.max_length_output)
            self.logger.info(f"decoding output of length: {len(outputs[0])}")
            prediction = self.tokenizer.decode(outputs[0].cpu(), skip_special_tokens=self.special_tokens_treatment, errors=self.errors_treatment)
        except Exception as e:
            logging.error(f"error extracting model: {e}")
            return MD_E["ERROR_OPENING_MODEL"],MD_E["CODE_ERROR_OPENING_MODEL"]
        try:
            prediction_json = json.loads(prediction)
        except json.JSONDecodeError:
            prediction = prediction.replace("'", '"')  
            prediction = prediction.replace("\"[", "[")
            prediction = prediction.replace("]\"", "]")
            prediction = prediction.replace("\�", "¿")
            prediction = self._normalice_latin_char(prediction)
            cleaned_prediction = prediction.encode('latin1', 'replace').decode('utf-8', 'replace')
            try:
                prediction_json = json.loads(cleaned_prediction,strict=False)
            except json.JSONDecodeError as e:
                logging.error(f"error parseing llm output: {e}, output: {prediction}")
                return MD_E["ERROR_PARSING_OUTPUT"],MD_E["CODE_ERROR_PARSING_OUTPUT"]
        return(prediction_json),None  # None for: no error has occurred

