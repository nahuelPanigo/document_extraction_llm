import torch
from peft import PeftModel
from fine_tunning.peft_configuration import get_peft_config
from transformers import BitsAndBytesConfig,AutoModelForSeq2SeqLM,AutoModelForCausalLM
from constants import BASE_MODEL_GEMMA,BASE_MODEL_LLAMA,BASE_MODEL_LED,BASE_MODEL_DEEPSEK_QWEN,BASE_MODEL_NUEXTRACT,BASE_MODEL_LED_SPANISH,BASE_MODEL_LED_LARGE,BASE_MODEL_T5



def get_model_type(model_name):
    try:
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)  # Try for encoder-decoder
        model.config.is_encoder_decoder  # If True, it's likely an encoder-decoder model
        return "seq2seq"
    except:
        try:
            # Try causal model (Decoder-Only)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            return "causal"
        except:
            raise ValueError("Model architecture not recognized")
            return "unknown"



def get_model(model_name,quantized=False,peft=False):
    model_mapping = {
    "LED": LedModel,
    "LLAMA": AutoModelForCausalLM,
    "GEMMA": AutoModelForCausalLM,
    "LED_SPANISH": LedModel,
    "DEEPSEK_QWEN": AutoModelForCausalLM,
    "LED_LARGE": LedModel,
    "NUEXTRACT": AutoModelForCausalLM,
    "T5": T5Model
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
    model_name = model_name_mapping.get(model_name)
    return model_class(model_name,quantized,peft)



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


    def get_model_name(self):
        return self.base_model_name
    
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
    



    
