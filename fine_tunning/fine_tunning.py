import torch
import torch.distributed as dist
#from torch.nn.parallel import DistributedDataParallel as DDP
import json
import os
import psutil
import logging
from transformers import LEDTokenizer, LEDForConditionalGeneration, Trainer, TrainingArguments
from datasets import Dataset,DatasetDict
from constant import LOG_DIR,JSONS_FOLDER,DATASET_WITH_TEXT_DOC,BASE_MODEL,FINAL_MODEL_PATH,CHECKPOINT_MODEL_PATH,MAX_TOKENS_INPUT,MAX_TOKENS_OUTPUT
from download_prepare_normalize_sedici_dataset.utils.read_and_write_files import read_data_json,detect_encoding,write_to_json
from peft import LoraConfig, TaskType,get_peft_model
from hugging_face_connection import get_dataset

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

filename_dataset = JSONS_FOLDER / DATASET_WITH_TEXT_DOC

if not (DATASET_WITH_TEXT_DOC) in os.listdir(JSONS_FOLDER):
    print("donwloading dataset from huggingface....")
    data = get_dataset(DATASET_WITH_TEXT_DOC)
    write_to_json(filename_dataset,data,"utf-8")


enc = detect_encoding(filename_dataset)["encoding"]

dict_dataset =  read_data_json(filename_dataset,enc)

data = {}
total_len = len(dict_dataset)
#total_len = 100
train_end = int(total_len * 0.8)
test_end = int(total_len * 0.9)
list_items_dataset = list(dict_dataset.values())
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
tokenizer = LEDTokenizer.from_pretrained(BASE_MODEL)
model = LEDForConditionalGeneration.from_pretrained(BASE_MODEL)
peft_config = LoraConfig(task_type=TaskType.FEATURE_EXTRACTION, inference_mode=False, r=128, lora_alpha=16, lora_dropout=0.1, target_modules=["query", "key", "value"])
model = get_peft_model(model,peft_config)
model.print_trainable_parameters()


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
    evaluation_strategy="epoch",
    logging_dir= LOG_DIR,            # Directorio de los registros
    logging_steps=10,     
    learning_rate=2e-5,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    num_train_epochs=3,
    weight_decay=0.01,
    save_total_limit=2,
    save_steps=10,
    fp16=True,  
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
model.save_pretrained(FINAL_MODEL_PATH)
tokenizer.save_pretrained(FINAL_MODEL_PATH)