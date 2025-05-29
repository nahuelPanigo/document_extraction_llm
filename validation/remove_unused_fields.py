from constants  import RESULT_FOLDER_VALIDATION
from ..utils.text_extraction.read_and_write_files import read_data_json,write_to_json



unused_fields = ["dc.uri", "dc.type", "sedici.uri","keywords"]

def remove_unused_fields(filename):
    final_data = {}
    data = read_data_json(filename)
    for key, inner_dict in data.items():
        cleaned_dict = {k: v for k, v in inner_dict.items() if k not in unused_fields}
        final_data[key] = cleaned_dict
    return final_data

if __name__ == "__main__":
    filename = RESULT_FOLDER_VALIDATION / "result_test_original_metadata.json"
    data = remove_unused_fields(filename)
    write_to_json(RESULT_FOLDER_VALIDATION / "metadata_corrected.json",data)
