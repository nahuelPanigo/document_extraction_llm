from constant import PROMPT,MAX_TOKENS_INPUT,MAX_TOKENS_OUTPUT
import json
from datasets import Dataset,DatasetDict

def split_dataset(dict_dataset):
    data = {}
    total_len = len(dict_dataset)
    #total_len = 100
    # Crear un nuevo diccionario sin el campo "abstract"
    new_dict = {x: {k: v for k, v in y.items() if k != "dc.description.abstract"} for x, y in dict_dataset.items()}
    train_end = int(total_len * 0.8)
    test_end = int(total_len * 0.9)
    list_items_dataset = list(new_dict.values())
    data["training"]=list_items_dataset[:train_end]
    data["test"] = list_items_dataset[train_end:test_end]
    data["validation"] = list_items_dataset[test_end:total_len]
    return data


def add_prompt_and_structure(dict_dataset):
    data = split_dataset(dict_dataset)
    formatted_data = {}
    for step in data.keys():
        step_data = []
        for item in data[step]:  
            input_text = f"{PROMPT} Document: {item['original_text']}"
            output_text = json.dumps({k: v for k, v in item.items() if k != "original_text"})
            step_data.append({"input": input_text, "output": output_text})
        formatted_data[step] = step_data
    dataset_dict = {}
    for step, step_data in formatted_data.items():
      dataset_dict[step] = Dataset.from_list(step_data)
    return DatasetDict(dataset_dict)


def preprocess_function(examples,model,tokenizer):
    inputs = examples['input']
    targets = examples['output']
    model_inputs = tokenizer(inputs, max_length=MAX_TOKENS_INPUT, truncation=True, padding="max_length")
    labels = tokenizer(targets, max_length=MAX_TOKENS_OUTPUT, truncation=True, padding="max_length")
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


def get_tokens(dict_dataset,model,tokenizer):
    datasets = add_prompt_and_structure(dict_dataset)
    # Tokenize dataset
    return datasets.map(preprocess_function, batched=True, fn_kwargs={'model': model , "tokenizer" : tokenizer})

