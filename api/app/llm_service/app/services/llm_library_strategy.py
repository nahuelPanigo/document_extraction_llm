import torch
from app.logging_config import logging
from ollama import Client
from app.services.model_managment import get_truncation
from app.services.utils import parse_json,extract_text_from_ollama
from typing import Tuple, Optional

class LLMStrategy:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate(self, prompt: str) -> str:
        raise NotImplementedError
    
    def clean_json(self, prediction) -> Tuple[dict, Optional[int]]:
        raise NotImplementedError
    

class HuggingFaceStrategy(LLMStrategy):
    def __init__(self,model,max_input,max_output,trunaction,special_tokens_treatment,errors_treatment):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.model
        self.model.to(self.device)
        self.tokenizer = model.tokenizer
        self.trunaction = get_truncation(self.tokenizer,trunaction)
        self.max_length_input = max_input
        self.max_length_output = max_output
        self.special_tokens_treatment =  special_tokens_treatment
        self.errors_treatment = errors_treatment


    def generate_with_fallback(self,inputs, max_input, max_output):
        if "max_new_tokens" in self.model.generate.__code__.co_varnames:
            self.logger.info(f"using max_new_tokens")
            return self.model.generate(**inputs, max_new_tokens=max_output)
        else:
            self.logger.info(f"using max_length")
            return self.model.generate(**inputs, max_length=max_input + max_output)

    def generate(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", max_length=self.max_length_input, truncation=self.trunaction) 
        inputs = {k: v.to(self.device) for k, v in inputs.items()}  
        self.logger.info(f"generating with model")
        outputs  = self.generate_with_fallback(inputs, self.max_length_input, self.max_length_output)
        self.logger.info(f"decoding output of length: {len(outputs[0])}")
        prediction = self.tokenizer.decode(outputs[0].cpu(), skip_special_tokens=self.special_tokens_treatment, errors=self.errors_treatment)
        return prediction
    
    def clean_json(self, prediction) -> Tuple[dict, Optional[int]]:
        return parse_json(prediction)

class OllamaStrategy(LLMStrategy):
    def __init__(self, model, host_url=None):
        super().__init__()
        self.model = model
        clean_host = host_url.strip() if host_url else "http://localhost:11434"
        self.logger.info(f"Ollama host: {clean_host}")
        self.client = Client(host=clean_host)

    def generate(self, prompt: str) -> str:
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            stream=False
        )
        return response['response']
    
    def clean_json(self, prediction)-> Tuple[dict, Optional[int]]:
        return extract_text_from_ollama(prediction)