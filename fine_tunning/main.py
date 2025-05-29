import torch
import os
import logging
from constants import LOG_DIR,JSON_FOLDER,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,FINAL_MODEL_PATH
from utils.text_extraction.read_and_write_files import read_data_json,detect_encoding,write_to_json
from fine_tunning.hugging_face_connection import get_dataset
from huggingface_hub import login
from dotenv import load_dotenv
from fine_tunning.generate_tokens import get_tokens
from fine_tunning.trainer import train
from fine_tunning.model_managment import get_model,get_model_type


#prox update from args
#could be LED,GEMMA,MISTRAL,LLAMA
MODEL_SELECTED = "LED"
QUANTIZATION = False
PEFT = False
TYPE_OF_MODEL_INPUT = "prompt"  # "prompt" or "schema"  NuExtract is "schema"   

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

filename_dataset = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED

if not filename_dataset.exists():
    load_dotenv()
    token = os.getenv("TOKEN_HUGGING_FACE")
    login(token=token)
    logger.info("donwloading dataset from huggingface....")
    data = get_dataset(DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED)
    write_to_json(filename_dataset,data,"utf-8")



# Verify CPU/GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {device}")


model = get_model(MODEL_SELECTED,quantized=QUANTIZATION, peft=PEFT)
model_type = get_model_type(model.get_model_name())

if PEFT:
    logger.info("using peft configuration:")
    logger.info(model.model.print_trainable_parameters())


enc = detect_encoding(filename_dataset)["encoding"]
dict_dataset =  read_data_json(filename_dataset,enc)

tokenized_datasets = get_tokens(dict_dataset,model.tokenizer,type_of_model=TYPE_OF_MODEL_INPUT,model_type=model_type)


logger.info("START FINETUNNING")
torch.cuda.empty_cache()


model = train(model,tokenized_datasets,MODEL_SELECTED,model_type)
logger.info("FINISH FINETUNNING")


# Guardar el modelo afinado
os.makedirs(FINAL_MODEL_PATH)
# Assuming `model` is your DataParallel model
model_to_save = model.model.module if isinstance(model.model, torch.nn.DataParallel) else model.model


model_to_save.save_pretrained(FINAL_MODEL_PATH)

print(type(model_to_save))
print(FINAL_MODEL_PATH)

#merge peft model with base model
if PEFT:
    model.save_merged_model(FINAL_MODEL_PATH)

model.tokenizer.save_pretrained(FINAL_MODEL_PATH)