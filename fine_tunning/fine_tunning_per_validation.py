import json
from transformers import LEDTokenizer, LEDForConditionalGeneration
from download_prepare_normalize_sedici_dataset.utils.read_and_write_files import read_data_json,detect_encoding
from constant import JSONS_FOLDER,DATASET_WITH_METADATA_CHECKED,MAX_TOKENS_INPUT,MAX_TOKENS_OUTPUT

filename_dataset = JSONS_FOLDER+DATASET_WITH_METADATA_CHECKED
enc = detect_encoding(filename_dataset)["encoding"]
dict_dataset =  read_data_json(filename_dataset,enc)



model_name = "allenai/led-base-16384"
tokenizer = LEDTokenizer.from_pretrained(model_name)
model = LEDForConditionalGeneration.from_pretrained("./fine-tuned-model")

data = {}
total_len = len(dict_dataset)
train_end = int(total_len * 0.8)
test_end = int(total_len * 0.9)
list_items_dataset = list(dict_dataset.items())
data["training"]=list_items_dataset[:train_end]
data["test"] = list_items_dataset[train_end:test_end]
data["validation"] = list_items_dataset[test_end:]

predictions = []

for doc in data["test"]:
    inputs = tokenizer(f"Document: {doc}", return_tensors="pt", max_length=MAX_TOKENS_INPUT, truncation=True)
    outputs = model.generate(**inputs, max_length=MAX_TOKENS_OUTPUT)
    prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
    try:
        # Validar y limpiar el JSON generado
        prediction_json = json.loads(prediction)
        predictions.append(prediction_json)
    except json.JSONDecodeError:
        # Si hay un error, intentar limpiar y corregir el JSON
        prediction = prediction.replace("'", '"')  # Reemplazar comillas simples por comillas dobles
        try:
            prediction_json = json.loads(prediction)
            predictions.append(prediction_json)
        except json.JSONDecodeError as e:
            print(f"Error decodificando JSON: {e}")
            print(f"Texto problemático: {prediction}")

# Guardar predicciones en un archivo JSON
with open('predictions.json', 'w') as f:
    json.dump(predictions, f, indent=4)