import torch
import json
import os
import psutil
import logging
#from transformers import LEDTokenizer, LEDForConditionalGeneration, Trainer, TrainingArguments
from transformers import AutoTokenizer, Trainer, TrainingArguments #LlamaForCausalLM,LlamaConfig
from transformers import AutoModelForCausalLM , AutoTokenizer,BitsAndBytesConfig
from datasets import Dataset,DatasetDict
from constant import LOG_DIR,JSONS_FOLDER,DATASET_WITH_TEXT_DOC,BASE_MODEL,FINAL_MODEL_PATH,CHECKPOINT_MODEL_PATH,MAX_TOKENS_INPUT,MAX_TOKENS_OUTPUT
from download_prepare_normalize_sedici_dataset.utils.read_and_write_files import read_data_json,detect_encoding,write_to_json
from peft import get_peft_model,PeftModel
from hugging_face_connection import get_dataset
from huggingface_hub import login
from dotenv import load_dotenv
from peft_configuration import get_peft_config

#Loging config
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'training.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Verify CPU/GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {device}")
print(device)

# config = LlamaConfig.from_pretrained(BASE_MODEL)

# # Correct the rope_scaling configuration
# config.rope_scaling = {
#     "type": "linear",  # Example type
#     "factor": 1.5      # Example factor
# }

#quantization_config = BitsAndBytesConfig(load_in_8bit=True)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

load_dotenv()
token = os.getenv("TOKEN_HUGGING_FACE")

login(token=token)
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL,quantization_config=bnb_config,low_cpu_mem_usage=True,torch_dtype=torch.float16)#, config=config)
model = get_peft_model(model, get_peft_config(model))


filename_dataset = JSONS_FOLDER / DATASET_WITH_TEXT_DOC

if not (DATASET_WITH_TEXT_DOC) in os.listdir(JSONS_FOLDER):
    print("donwloading dataset from huggingface....")
    data = get_dataset(DATASET_WITH_TEXT_DOC)
    write_to_json(filename_dataset,data,"utf-8")


enc = detect_encoding(filename_dataset)["encoding"]

dict_dataset =  read_data_json(filename_dataset,enc)

data = {}
total_len = len(dict_dataset)
# Crear un nuevo diccionario sin el campo "abstract"
new_dict = {x: {k: v for k, v in y.items() if k != "abstract"} for x, y in dict_dataset.items()}
#total_len = 100
train_end = int(total_len * 0.8)
test_end = int(total_len * 0.9)
list_items_dataset = list(new_dict.values())
data["training"]=list_items_dataset[:train_end]
data["test"] = list_items_dataset[train_end:test_end]
data["validation"] = list_items_dataset[test_end:total_len]

formatted_data = {}
for step in data.keys():
    step_data = []
    for item in data[step]:  
        input_text = f"Document: {item['original_text']}"
        output_text = json.dumps({k: v for k, v in item.items() if k != "original_text"})
        step_data.append({"input": input_text, "output": output_text})
    formatted_data[step] = step_data

dataset_dict = {}
for step, step_data in formatted_data.items():
    dataset_dict[step] = Dataset.from_list(step_data)

datasets =  DatasetDict(dataset_dict)

# Charge model and tokenizer
#tokenizer = LEDTokenizer.from_pretrained(BASE_MODEL)
# tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
# #model = LEDForConditionalGeneration.from_pretrained(BASE_MODEL)
# model = LlamaForCausalLM.from_pretrained(BASE_MODEL)
#peft_config = LoraConfig(task_type=TaskType.FEATURE_EXTRACTION, inference_mode=False, r=128, lora_alpha=16, lora_dropout=0.1, target_modules=["query", "key", "value"])
#model = get_peft_model(model,peft_config)
#model.print_trainable_parameters()


# Tokenize dataset
def preprocess_function(examples):
    inputs = examples['input']
    targets = examples['output']
    model_inputs = tokenizer(inputs, max_length=MAX_TOKENS_INPUT, truncation=True, padding="max_length")
    labels = tokenizer(targets, max_length=MAX_TOKENS_OUTPUT, truncation=True, padding="max_length")
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized_datasets = datasets.map(preprocess_function, batched=True)

# Configurar los argumentos de entrenamiento
training_args = TrainingArguments(
    output_dir= CHECKPOINT_MODEL_PATH,
    eval_strategy="epoch",
    logging_dir= LOG_DIR,            # Directorio de los registros
    logging_steps=10,     
    learning_rate=2e-5,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    num_train_epochs=3,
    weight_decay=0.01,
    save_total_limit=2,
    save_steps=50,
    fp16=True,  
    warmup_steps=100,
)

# Inicializar el entrenador
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["training"],
    eval_dataset=tokenized_datasets["validation"]
)


#convert model tu gpu
model = model.to('cuda')
model = torch.nn.DataParallel(model)

# Habilitar la depuración en PyTorch
torch.autograd.set_detect_anomaly(True)
process = psutil.Process(os.getpid())
logger.info(f"Memory usage before training: {process.memory_info().rss / 1024 ** 2:.2f} MB")

logger.info("START")
torch.cuda.empty_cache()
trainer.train()

logger.info("FINISH")

# Verificar el uso de memoria después de finalizar el entrenamiento
logger.info(f"Memory usage after training: {process.memory_info().rss / 1024 ** 2:.2f} MB")
# Guardar el modelo afinado
print(FINAL_MODEL_PATH)
os.makedirs(FINAL_MODEL_PATH)
# Assuming `model` is your DataParallel model
model_to_save = model.module if isinstance(model, torch.nn.DataParallel) else model
print(type(model_to_save))
print(FINAL_MODEL_PATH)


#merge peft model with base model
base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL,quantization_config=bnb_config,low_cpu_mem_usage=True,torch_dtype=torch.float16)#, config=config)
peft_model = PeftModel.from_pretrained(base_model, model_to_save)
merged_model = peft_model.merge_and_unload()
merged_model.save_pretrained(FINAL_MODEL_PATH,safe_serialization=True)

tokenizer.save_pretrained(FINAL_MODEL_PATH)