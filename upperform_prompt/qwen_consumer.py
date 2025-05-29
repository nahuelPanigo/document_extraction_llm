from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch


def consume_qewn(input):

    model_id = "Qwen/Qwen3-4B"  # o Qwen2 si estás usando otro

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda",
        quantization_config=bnb_config,
        trust_remote_code=True
    )

    inputs = tokenizer(input, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=1024)


    return tokenizer.decode(outputs[0])

