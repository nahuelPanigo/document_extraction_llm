from utils.normalization.normalice_data import normalice_text
from constants import  JSON_FOLDER, DATASET_WITH_METADATA_AND_TEXT_DOC_CLEANED
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json


if __name__ == "__main__":
    dataset_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CLEANED
    print(f"📂 Loading dataset from: {dataset_path}")
    data = read_data_json(dataset_path, "utf-8")
    final_data = {}
    print(f"📊 Total records: {len(data)}")
    for id, record in data.items():
        try:
            print(f"📄 Normalizing record: {id}")
            record["original_text"] = normalice_text(record["original_text"])
            record["title"] = normalice_text(record["title"])
            final_data[id] = record
        except Exception as e:
            print(f"📄 Normalizing record: {id} failed")
            print(e)

    write_to_json(dataset_path,final_data, "utf-8")