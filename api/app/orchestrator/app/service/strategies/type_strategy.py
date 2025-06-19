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

        return response_json["data"], None


class TesisStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")

    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_TESIS
        self.logger.info(f"calling llm service to extract metadata")
        llm_input = PROMPT_TESIS + text
        response, error = self.consume_llm(
            api_key=self.llm_service_api_key,
            input=llm_input,
            url=self.llm_service_url
        )
        return response, error
    

class ArticuloStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")
    
    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_ARTICULO
        self.logger.info(f"calling llm service to extract metadata")
        llm_input = PROMPT_ARTICULO + text
        response, error = self.consume_llm(
            api_key=self.llm_service_api_key,
            input=llm_input,
            url=self.llm_service_url
        )
        return response, error
    
class LibroStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")

    def get_metadata(self, text: str) -> Tuple[dict, Optional[int]]:
        from app.constants.constant import PROMPT_LIBRO
        self.logger.info(f"calling llm service to extract metadata")
        llm_input = PROMPT_LIBRO + text
        response, error = self.consume_llm(
            api_key=self.llm_service_api_key,
            input=llm_input,
            url=self.llm_service_url
        )
        return response, error