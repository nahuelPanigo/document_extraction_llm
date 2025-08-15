from utils.normalization.normalice_data import normalice_text, get_corrects_keywords, remove_honorifics, amend_title_with_subtitle
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json
from constants import PERCENTAGE_DATASET_FOR_STEPS
from collections import defaultdict
import random


def split_dataset(dict_dataset):
    """
    Stratified split to maintain the same percentage of document types 
    across training, test, and validation sets
    """
    # Group samples by type
    type_groups = defaultdict(list)
    for id_, val in dict_dataset.items():
        doc_type = val.get("type", "unknown")
        type_groups[doc_type].append({**val, "id": id_})
    
    # Shuffle each type group to ensure randomness
    for doc_type in type_groups:
        random.shuffle(type_groups[doc_type])
    
    # Initialize split containers
    data = {"training": [], "test": [], "validation": []}
    
    # Split each type according to the percentages
    for doc_type, samples in type_groups.items():
        total_samples = len(samples)
        
        # Calculate split indices
        train_end = int(total_samples * PERCENTAGE_DATASET_FOR_STEPS["training"])
        test_end = train_end + int(total_samples * PERCENTAGE_DATASET_FOR_STEPS["test"])
        
        # Distribute samples
        data["training"].extend(samples[:train_end])
        data["test"].extend(samples[train_end:test_end])
        data["validation"].extend(samples[test_end:])
        
        print(f"{doc_type}: train={train_end}, test={test_end-train_end}, val={len(samples)-test_end}")
    
    # Shuffle final datasets to mix types
    for split in data:
        random.shuffle(data[split])
    
    print(f"Final split sizes - training: {len(data['training'])}, test: {len(data['test'])}, validation: {len(data['validation'])}")
    
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