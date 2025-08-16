from abc import ABC, abstractmethod
from dotenv import load_dotenv
import os
from app.logging_config import logging
import requests
from typing import Tuple, Optional

class TypeStrategy(ABC):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")

    def consume_llm(self, api_key: str, input: str, url: str) -> Tuple[dict, Optional[int]]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.logger.info(f"calling llm service url: {url}")
        response_llm = requests.post(
            url,
            headers=headers,
            json={"text": input}
        )

        response_json = response_llm.json()

        if response_llm.status_code != 200:
            self.logger.error(f"LLM error: {response_json['error']}")
            return response_json, response_json["error"]["code"]

        self.logger.info(f"response from llm service: {response_json}")
        return response_json["data"], None
    
    def check_and_add_missing_keys(self, metadata: dict, keys: list) -> dict:
        for key in keys:
            self.logger.info(f"checking key: {key}")
            if key not in metadata:
                self.logger.info(f"adding key: {key}")
                metadata[key] = ""
        return metadata
    
    def get_metadata(self, input: str , keys: list) -> Tuple[dict, Optional[int]]:
        self.logger.info(f"calling llm service to extract metadata")
        response, error = self.consume_llm(
            api_key=self.llm_service_api_key,
            input=input,
            url=self.llm_service_url
        )
        if error is None:
            self.logger.info(f"response from llm service: {response}")
            response = self.check_and_add_missing_keys(response, keys)
        return response, error


class GeneralStrategy(TypeStrategy):
    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_GENERAL,KEYS_GENERAL      
        llm_input = PROMPT_GENERAL + text
        return super().get_metadata(llm_input, KEYS_GENERAL)


class ObjectConferenceStrategy(TypeStrategy):

    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_OBJECTO_CONFERENCIA,KEYS_OBJETO_CONFERENCIA
        llm_input = PROMPT_OBJECTO_CONFERENCIA + text
        return super().get_metadata(llm_input, KEYS_OBJETO_CONFERENCIA)

class TesisStrategy(TypeStrategy):

    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_TESIS,KEYS_TESIS
        llm_input = PROMPT_TESIS + text
        return super().get_metadata(llm_input, KEYS_TESIS)
    

class ArticuloStrategy(TypeStrategy):

    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_ARTICULO,KEYS_ARTICULO
        llm_input = PROMPT_ARTICULO + text
        return super().get_metadata(llm_input, KEYS_ARTICULO)
    
class LibroStrategy(TypeStrategy):

    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_LIBRO,KEYS_LIBRO
        llm_input = PROMPT_LIBRO + text
        return super().get_metadata(llm_input, KEYS_LIBRO)