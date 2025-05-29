from utils.normalization.normalice_data import normalice_text
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json


def split_dataset(dict_dataset):
    metadata_col = [{**val, "id": id_} for id_, val in dict_dataset.items()]
    data = {}
    total_len = len(metadata_col)
    train_end = int(total_len * 0.8)
    test_end = int(total_len * 0.9)
    data["training"]=metadata_col[:train_end]
    data["test"] = metadata_col[train_end:test_end]
    data["validation"] = metadata_col[test_end:total_len]
    return data


def normalize_texts(dict_dataset):
    final_dict = {}
    for id_, metadata in dict_dataset.items():
        final_dict[id_] = metadata
        if "abstract" in metadata:
            if isinstance(metadata["abstract"],str):
                final_dict[id_]["abstract"] = normalice_text(metadata["abstract"])
            else:
                final_dict[id_]["abstract"] = [normalice_text(x) for x in metadata["abstract"]]
        final_dict[id_]["original_text"] = normalice_text(metadata["original_text"])
    return final_dict

def normalize_and_split_dataset(json_filename):
    data = read_data_json(json_filename,"utf-8")
    data = normalize_texts(data)
    write_to_json(json_filename,split_dataset(data),"utf-8")