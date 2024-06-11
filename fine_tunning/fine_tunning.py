import torch
import json
import os
import psutil
import logging
from transformers import LEDTokenizer, LEDForConditionalGeneration, Trainer, TrainingArguments
from datasets import Dataset,DatasetDict
from constant import LOG_DIR,DATA_FOLDER,DATASET_FILENAME,BASE_MODEL,FINAL_MODEL_PATH,CHECKPOINT_MODEL_PATH,MAX_TOKENS_INPUT,MAX_TOKENS_OUTPUT


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
# Verificar CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {device}")


with open(DATA_FOLDER+DATASET_FILENAME, 'r', encoding='latin-1') as jsonfile:
    data_dict = json.load(jsonfile)

data = {}
total_len = len(data_dict)
train_end = int(total_len * 0.8)
test_end = int(total_len * 0.9)
data["training"]=data_dict[:train_end]
data["test"] = data_dict[train_end:test_end]
data["validation"] = data_dict[test_end:]


formatted_data = {}

for step in data.keys():
    step_data = []
    for item in data[step]:
        input_text = f"Document: {item['original_text']}"
        output_text = json.dumps({
            "title": item["title"],
            "authors": item["authors"],
            "category": item["cat"]
        })
        step_data.append({"input": input_text, "output": output_text})
    formatted_data[step] = step_data

dataset_dict = {}
for step, step_data in formatted_data.items():
    dataset_dict[step] = Dataset.from_list(step_data)

datasets =  DatasetDict(dataset_dict)

# Cargar el modelo preentrenado y el tokenizador
tokenizer = LEDTokenizer.from_pretrained(BASE_MODEL)
model = LEDForConditionalGeneration.from_pretrained(BASE_MODEL)



# Tokenizar el conjunto de datos
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
    fp16=False,  
)

# Inicializar el entrenador
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["training"],
    eval_dataset=tokenized_datasets["validation"]
)

# Habilitar la depuración en PyTorch
torch.autograd.set_detect_anomaly(True)
process = psutil.Process(os.getpid())
logger.info(f"Memory usage before training: {process.memory_info().rss / 1024 ** 2:.2f} MB")

logger.info("START")
# Ajuste fino del modelo
trainer.train()
logger.info("FINISH")

# Verificar el uso de memoria después de finalizar el entrenamiento
logger.info(f"Memory usage after training: {process.memory_info().rss / 1024 ** 2:.2f} MB")
# Guardar el modelo afinado
model.save_pretrained(FINAL_MODEL_PATH)
tokenizer.save_pretrained(FINAL_MODEL_PATH)