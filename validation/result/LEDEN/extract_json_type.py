import json
import os
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[0]


def extract_json_type(filename):
    final_data = {}
    with open(filename, 'r') as f:
        data = json.load(f)
        for key, col in data.items():
            try:
                final_data[key] = col[1]
            except Exception as e:  
                print("no tiene elementos, fallo con error: ", e)   
    return final_data

def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)



if __name__ == "__main__":
    filename = FOLDER / "result_test_2048_prompt_by_type_without_keywords_andUri.json"
    data= extract_json_type(filename)   
    save_json(data, FOLDER / "results_only_type.json")