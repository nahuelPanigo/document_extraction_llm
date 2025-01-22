import torch
import os
import psutil
import logging
from transformers import Trainer, TrainingArguments 
from constant import LOG_DIR,JSONS_FOLDER,DATASET_WITH_TEXT_DOC,FINAL_MODEL_PATH,CHECKPOINT_MODEL_PATH
from download_prepare_normalize_sedici_dataset.utils.read_and_write_files import read_data_json,detect_encoding,write_to_json
from hugging_face_connection import get_dataset
from huggingface_hub import login
from dotenv import load_dotenv
from model_managment import LedModel,LlamaModel,GemmaModel
from generate_tokens import get_tokens

#prox update from args
#could be LED,GEMMA,MISTRAL,LLAMA
MODEL_SELECTED = "LED"
QUANTIZATION = False
PEFT = False


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


load_dotenv()
token = os.getenv("TOKEN_HUGGING_FACE")
login(token=token)

model_mapping = {
    "LED": LedModel,
    "LLAMA": LlamaModel,
    "GEMMA": GemmaModel
}
model_class = model_mapping.get(MODEL_SELECTED)
model = model_class(quantized=QUANTIZATION, peft=PEFT)
if PEFT:
    print(model.model.print_trainable_parameters())


filename_dataset = JSONS_FOLDER / DATASET_WITH_TEXT_DOC
if not (DATASET_WITH_TEXT_DOC) in os.listdir(JSONS_FOLDER):
    print("donwloading dataset from huggingface....")
    data = get_dataset(DATASET_WITH_TEXT_DOC)
    write_to_json(filename_dataset,data,"utf-8")


enc = detect_encoding(filename_dataset)["encoding"]
dict_dataset =  read_data_json(filename_dataset,enc)
tokenized_datasets = get_tokens(dict_dataset,model.model,model.tokenizer)


# Configurar los argumentos de entrenamiento
training_args = TrainingArguments(
    output_dir= CHECKPOINT_MODEL_PATH,
    eval_strategy="epoch",
    logging_dir= LOG_DIR,            # Directorio de los registros
    logging_steps=10,     
    learning_rate=2e-5,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    num_train_epochs=2,
    weight_decay=0.01,
    save_total_limit=2,
    save_steps=50,
    warmup_steps=100,
)

# Inicializar el entrenador
trainer = Trainer(
    model=model.model,
    args=training_args,
    train_dataset=tokenized_datasets["training"],
    eval_dataset=tokenized_datasets["validation"]
)


#convert model tu gpu
model.model = model.model.to('cuda')
model.model = torch.nn.DataParallel(model.model)


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
model_to_save = model.model.module if isinstance(model.model, torch.nn.DataParallel) else model.model


model_to_save.save_pretrained(FINAL_MODEL_PATH)
model.tokenizer.save_pretrained(FINAL_MODEL_PATH)

print(type(model_to_save))
print(FINAL_MODEL_PATH)

#merge peft model with base model
if PEFT:
    model.save_merged_model(FINAL_MODEL_PATH)

model.tokenizer.save_pretrained(FINAL_MODEL_PATH)