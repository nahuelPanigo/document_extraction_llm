from abc import ABC, abstractmethod
from dotenv import load_dotenv
import os
from app.logging_config import logging
import requests
from typing import Tuple, Optional

class TypeStrategy(ABC):
    def __init__(self):
        self.logger = logging.getLogger(__name__)


    @abstractmethod
    def get_metadata(self,text : str) -> dict:
        pass


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

class GeneralStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")

    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_GENERAL,KEYS_GENERAL
        self.logger.info(f"calling llm service to extract metadata")
        llm_input = PROMPT_GENERAL + text
        response, error = self.consume_llm(
            api_key=self.llm_service_api_key,
            input=llm_input,
            url=self.llm_service_url
        )
        if error is None:
            self.logger.info(f"response from llm service: {response}")
            response = self.check_and_add_missing_keys(response, KEYS_GENERAL)
        return response, error


class TesisStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")

    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_TESIS,KEYS_TESIS
        self.logger.info(f"calling llm service to extract metadata")
        llm_input = PROMPT_TESIS + text
        response, error = self.consume_llm(
            api_key=self.llm_service_api_key,
            input=llm_input,
            url=self.llm_service_url
        )
        if error is None:
            self.logger.info(f"response from llm service: {response}")
            response = self.check_and_add_missing_keys(response, KEYS_TESIS)
        return response, error
    

class ArticuloStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")
    
    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_ARTICULO,KEYS_ARTICULO
        self.logger.info(f"calling llm service to extract metadata")
        llm_input = PROMPT_ARTICULO + text
        response, error = self.consume_llm(
            api_key=self.llm_service_api_key,
            input=llm_input,
            url=self.llm_service_url
        )
        if error is None:
            self.logger.info(f"response from llm service: {response}")
            response = self.check_and_add_missing_keys(response, KEYS_ARTICULO)
        return response, error
    
class LibroStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")

    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_LIBRO,KEYS_LIBRO
        self.logger.info(f"calling llm service to extract metadata")
        llm_input = PROMPT_LIBRO + text
        response, error = self.consume_llm(
            api_key=self.llm_service_api_key,
            input=llm_input,
            url=self.llm_service_url
        )
        if error is None:
            self.logger.info(f"response from llm service: {response}")
            response = self.check_and_add_missing_keys(response, KEYS_LIBRO)
        return response, error