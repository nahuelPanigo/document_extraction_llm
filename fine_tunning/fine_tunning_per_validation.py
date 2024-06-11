import json
from transformers import LEDTokenizer, LEDForConditionalGeneration


with open('data/output2.json', 'r', encoding='latin-1') as jsonfile:
    data_dict = json.load(jsonfile)

model_name = "allenai/led-base-16384"
tokenizer = LEDTokenizer.from_pretrained(model_name)
model = LEDForConditionalGeneration.from_pretrained("./fine-tuned-model")

data = {}
total_len = len(data_dict)
train_end = int(total_len * 0.8)
test_end = int(total_len * 0.9)
data["training"]=data_dict[:train_end]
data["test"] = data_dict[train_end:test_end]
data["validation"] = data_dict[test_end:]

predictions = []

for doc in data["test"]:
    inputs = tokenizer(f"Document: {doc}", return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(**inputs, max_length=512)
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