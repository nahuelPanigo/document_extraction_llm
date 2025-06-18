from abc import ABC, abstractmethod
from dotenv import load_dotenv
import os
from app.logging_config import logging
import requests

class TypeStrategy(ABC):
    def __init__(self):
        self.logger = logging.getLogger(__name__)


    @abstractmethod
    def get_metadata(self,text : str) -> dict:
        pass


    def consume_llm(self,api_key:str,input: str,url: str) -> dict:
           # Paso 2: Llamar al servicio de LLM
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
        if response_llm.status_code != 200:
            self.logger.error(f"LLM error: {response_llm.text}")
            return {
                "error": "Error during LLM inference",
                "detail": response_llm.text,
                "code": response_llm.status_code
            }
        return response_llm.json()


class TesisStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")

    def get_metadata(self,text : str) -> dict:
        from app.constants.constant import PROMPT_TESIS
        self.logger.info(f"calling llm service to extract metadata")
        input  = PROMPT_TESIS + text
        return self.consume_llm(api_key=self.llm_service_api_key,input=input,url=self.llm_service_url)
    

class ArticuloStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")
    
    def get_metadata(self,text : str) -> dict:
        from app.constants.constant import PROMPT_ARTICULO
        self.logger.info(f"calling llm service to extract metadata")
        input  = PROMPT_ARTICULO + text
        return self.consume_llm(api_key=self.llm_service_api_key,input=input,url=self.llm_service_url)
    
class LibroStrategy(TypeStrategy):
    def __init__(self):
        super().__init__()  
        load_dotenv()
        self.llm_service_url = os.getenv("LLM_LED_URL") + "/consume-llm"
        self.llm_service_api_key = os.getenv("LLM_LED_TOKEN")

    def get_metadata(self,text : str) -> dict:
        from app.constants.constant import PROMPT_LIBRO
        self.logger.info(f"calling llm service to extract metadata")
        input  = PROMPT_LIBRO + text
        return self.consume_llm(api_key=self.llm_service_api_key,input=input,url=self.llm_service_url)