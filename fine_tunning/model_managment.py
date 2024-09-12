import torch
from peft import PeftModel
from peft_configuration import get_peft_config
from transformers import BitsAndBytesConfig

# Clase base para todos los modelos
class BaseModel:
    def __init__(self, base_model_name, quantized=True, peft=True):
        self.base_model_name = base_model_name
        self.quantized = quantized
        self.peft = peft
        self.model = None
        self.tokenizer = None
        # Cargar el modelo y el tokenizador al crear la instancia
        self.load_model_and_tokenizer()

    def load_quantized_configuration(self):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        return bnb_config

    def load_base_model(self, model_class, tokenizer_class):
        """Carga el modelo base sin configuración PEFT."""
        if self.quantized:
            bnb_config = self.load_quantized_configuration()
            self.model = model_class.from_pretrained(self.base_model_name, quantization_config=bnb_config, low_cpu_mem_usage=True)
        else:
            self.model = model_class.from_pretrained(self.base_model_name)
        self.tokenizer = tokenizer_class.from_pretrained(self.base_model_name)

    def load_peft_model(self, model_class, tokenizer_class):
        """Carga el modelo base con configuración PEFT."""
        self.load_base_model(model_class, tokenizer_class)
        self.model = get_peft_config(self.model)

    def load_model_and_tokenizer(self):
        """Carga el modelo y el tokenizador dependiendo de la configuración PEFT."""
        model_class, tokenizer_class = self.get_base_model_class()
        if self.peft:
            self.load_peft_model(model_class, tokenizer_class)
        else:
            self.load_base_model(model_class, tokenizer_class)

    def save_merged_model(self, final_model_path):
        """Guarda el modelo fusionado si PEFT está habilitado."""
        if self.peft:
            model_class, _ = self.get_base_model_class()
            base_model = model_class.from_pretrained(self.base_model_name)
            peft_model = PeftModel.from_pretrained(base_model, final_model_path)
            merged_model = peft_model.merge_and_unload()
            merged_model.save_pretrained(final_model_path, safe_serialization=True)

    def get_base_model_class(self):
        """Devuelve la clase del modelo base usada para cargar modelos."""
        raise NotImplementedError("Este método debe ser implementado por las subclases.")


# Subclase para el modelo Llama
class LlamaModel(BaseModel):
    def __init__(self, quantized=True, peft=True):
        from constant import BASE_MODEL_LLAMA
        super().__init__(BASE_MODEL_LLAMA, quantized, peft)

    def get_base_model_class(self):
        from transformers import LlamaTokenizer, LlamaForCausalLM
        return LlamaForCausalLM, LlamaTokenizer


# Subclase para el modelo Gemma
class GemmaModel(BaseModel):
    def __init__(self, quantized=True, peft=True):
        from constant import BASE_MODEL_GEMMA
        super().__init__(BASE_MODEL_GEMMA, quantized, peft)

    def get_base_model_class(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        return AutoModelForCausalLM, AutoTokenizer


# Subclase para el modelo LED
class LedModel(BaseModel):
    def __init__(self, quantized=False, peft=False):
        from constant import BASE_MODEL_LED
        super().__init__(BASE_MODEL_LED, quantized, peft)

    def get_base_model_class(self):
        from transformers import LEDTokenizer, LEDForConditionalGeneration
        return LEDForConditionalGeneration, LEDTokenizer
