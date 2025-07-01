import json
from app.errors.error import MODEL_ERRORS as MD_E
from dotenv import load_dotenv
from app.services.model_managment import get_model
import re
import os
from app.logging_config import logging
from pathlib import Path
from app.services.llm_library_strategy import HuggingFaceStrategy,OllamaStrategy


class ModelExtraction:
    def __init__(self):
        load_dotenv()
        self.logger = logging.getLogger(__name__)
        if self._str_to_bool(os.getenv("IS_OLLAMA_MODEL")):
            host_url = os.getenv("OLLAMA_HOST_URL")
            self.strategy = OllamaStrategy(os.getenv("MODEL_SELECTED"),host_url)
        else:
            base_dir = Path(__file__).resolve().parent.parent
            if  self._str_to_bool(os.getenv("IS_LOCAL_MODEL")):
                model_path = base_dir / os.getenv("MODEL_PATH")
            else:
                model_path = os.getenv("MODEL_PATH")
            model = get_model(os.getenv("MODEL_SELECTED"),quantized=self._str_to_bool(os.getenv("QUANTIZATION")),custom_path=model_path)
            max_length_input = int(os.getenv("MAX_TOKENS_INPUT", 2048))
            max_length_output = int(os.getenv("MAX_TOKENS_OUTPUT", 512))
            special_tokens_treatment = self._str_to_bool(os.getenv("SPECIAL_TOKENS_TREATMENT",True))
            errors_treatment = os.getenv("ERRORS_TREATMENT","replace")
            self.strategy = HuggingFaceStrategy(model,max_length_input,max_length_output,os.getenv("TRUNACTION",True),special_tokens_treatment,errors_treatment)

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


    def clean_json(self,prediction):
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
        return(prediction_json),None    



    @staticmethod
    def _str_to_bool(value):
        return str(value).lower() in ("true", "1", "yes", "on")


    def model_extraction(self,final_prompt):
        try: 
            prediction = self.strategy.generate(final_prompt)
        except Exception as e:
            logging.error(f"error extracting model: {e}")
            return MD_E["ERROR_OPENING_MODEL"],MD_E["CODE_ERROR_OPENING_MODEL"]
        return self.clean_json(prediction)

