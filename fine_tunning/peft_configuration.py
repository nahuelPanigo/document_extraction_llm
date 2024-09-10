import bitsandbytes as bnb
import torch
from peft import LoraConfig,TaskType

def determine_quantization_type(model):
    quantization_type = 'none'
    for name, module in model.named_modules():
        if isinstance(module, bnb.nn.Linear4bit):
            return bnb.nn.Linear4bit
        elif isinstance(module, bnb.nn.Linear8bitLt):
            return bnb.nn.Linear8bitLt
    return torch.nn.Linear



def find_all_linear_names(model):
    cls = determine_quantization_type(model)
    lora_module_names = set()
    for name, module in model.named_modules():
        if isinstance(module, cls):
            names = name.split('.')
            lora_module_names.add(names[0] if len(names) == 1 else names[-1])
        if 'lm_head' in lora_module_names: # needed for 16-bit
            lora_module_names.remove('lm_head')
    return list(lora_module_names)



def get_peft_config(model):
    modules = find_all_linear_names(model)
    return LoraConfig(
        r=32,
        lora_alpha=32,
        target_modules=modules,
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

