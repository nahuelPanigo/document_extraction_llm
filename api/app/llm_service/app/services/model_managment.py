import torch
from transformers import BitsAndBytesConfig,AutoModelForCausalLM, PreTrainedTokenizer
from app.constants.constant import BASE_MODEL_GEMMA,BASE_MODEL_LLAMA,BASE_MODEL_LED,BASE_MODEL_DEEPSEK_QWEN,BASE_MODEL_NUEXTRACT,BASE_MODEL_LED_SPANISH,BASE_MODEL_LED_LARGE,BASE_MODEL_T5,BASE_MODEL_MISTRAL
from app.logging_config import logging

def get_model(model_name, quantized=False, custom_path=None):
    model_mapping = {
        "LED": LedModel,
        "LLAMA": AutoModelForCausalLM,
        "QWEN": AutoModelForCausalLM,
        "GEMMA": AutoModelForCausalLM,
        "LED_SPANISH": LedModel,
        "DEEPSEK_QWEN": AutoModelForCausalLM,
        "LED_LARGE": LedModel,
        "NUEXTRACT": AutoModelForCausalLM,
        "T5": T5Model,
    }

    model_name_mapping = {
        "LED": BASE_MODEL_LED,
        "LLAMA": BASE_MODEL_LLAMA,
        "GEMMA": BASE_MODEL_GEMMA,
        "LED_SPANISH": BASE_MODEL_LED_SPANISH,
        "DEEPSEK_QWEN": BASE_MODEL_DEEPSEK_QWEN,
        "LED_LARGE": BASE_MODEL_LED_LARGE,
        "NUEXTRACT": BASE_MODEL_NUEXTRACT,
        "T5": BASE_MODEL_T5
    }

    model_class = model_mapping.get(model_name)
    model_path = custom_path if custom_path else model_name_mapping.get(model_name)
    logging.info(f"model path: {model_path}")
    logging.info(f"model class: {model_class}")

    return model_class(model_path, quantized)


def get_truncation(tokenizer, truncation):
    if isinstance(tokenizer, PreTrainedTokenizer):
        truncation = truncation
    else:
        truncation = "only_first"


# Clase base para todos los modelos
class BaseModel:
    def __init__(self, base_model_name, quantized=True):
        self.base_model_name = base_model_name
        self.quantized = quantized
        self.model = None
        self.tokenizer = None
        # Cargar el modelo y el tokenizador al crear la instancia
        self.load_model_and_tokenizer()


    def get_model_name(self):
        return self.base_model_name
    
    def load_quantized_configuration(self):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        logging.info(f"loading quantized configuration {bnb_config}")
        return bnb_config

    def load_base_model(self, model_class, tokenizer_class):
        """Carga el modelo base sin configuración PEFT."""
        if self.quantized:
            bnb_config = self.load_quantized_configuration()
            self.model = model_class.from_pretrained(self.base_model_name, quantization_config=bnb_config, low_cpu_mem_usage=True)
        else:
            self.model = model_class.from_pretrained(self.base_model_name)
        self.tokenizer = tokenizer_class.from_pretrained(self.base_model_name)


    def load_model_and_tokenizer(self):
        """Carga el modelo y el tokenizador dependiendo de la configuración PEFT."""
        model_class, tokenizer_class = self.get_base_model_class()
        self.load_base_model(model_class, tokenizer_class)

    def get_base_model_class(self):
        """Devuelve la clase del modelo base usada para cargar modelos."""
        raise NotImplementedError("Este método debe ser implementado por las subclases.")


# Subclase para el modelo LED
class LedModel(BaseModel):
    def get_base_model_class(self):
        from transformers import LEDTokenizer, LEDForConditionalGeneration
        return LEDForConditionalGeneration, LEDTokenizer

    
class AutoModelForCausalLM(BaseModel):
    def get_base_model_class(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM
        return AutoModelForCausalLM, AutoTokenizer
    

class T5Model(BaseModel):
    def get_base_model_class(self):
        from transformers import T5Tokenizer, T5ForConditionalGeneration
        return T5ForConditionalGeneration, T5Tokenizer
    



    
