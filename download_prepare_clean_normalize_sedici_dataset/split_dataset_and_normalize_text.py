from utils.normalization.normalice_data import normalice_text, get_corrects_keywords, remove_honorifics, amend_title_with_subtitle
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

def final_normalization_post_llm(dict_dataset,original_metadata):
    """
    Applies final normalization after LLM processing:
    - Removes honorifics from creator, director, codirector
    - Amends title with subtitle 
    - Normalizes keywords (removes :: suffixes)
    - Normalizes text to fix repeated letters
    """
    final_dict = {}
    for id_, metadata in dict_dataset.items():
        item = metadata.copy()
        
        # Remove honorifics from creator, director, codirector
        for field in ['creator', 'director', 'codirector']:
            if field in item:
                if isinstance(item[field], list):
                    item[field] = [remove_honorifics(name) for name in item[field]]
                else:
                    item[field] = remove_honorifics(item[field])
        
        # Amend title with subtitle
        item = amend_title_with_subtitle(item)
        
        # Normalize keywords
        if 'keywords' in item:
            item['keywords'] = get_corrects_keywords(item['keywords'])
        
        # Normalize title text (fix repeated letters)
        if 'title' in item:
            item['title'] = normalice_text(item['title'])
        
        if "abstract" in item:
            if isinstance(item["abstract"],str):
                item["abstract"] = normalice_text(item["abstract"])
            else:
                item["abstract"] = [normalice_text(x) for x in item["abstract"]]
        item["original_text"] = normalice_text(item["original_text"])

        item["type"] = original_metadata[id_]["dc.type"]

        final_dict[id_] = item
    
    return final_dict


def normalize_and_split_dataset(json_filename,original_json_filename):
    data = read_data_json(json_filename,"utf-8")
    original_metadata = read_data_json(original_json_filename,"utf-8")
    data = final_normalization_post_llm(data,original_metadata)
    write_to_json(json_filename,split_dataset(data),"utf-8")