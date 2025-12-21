from utils.normalization.normalice_data import normalice_text, get_corrects_keywords, remove_honorifics, amend_title_with_subtitle
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json
from constants import PERCENTAGE_DATASET_FOR_STEPS
from collections import defaultdict
import random
import math
import re


def analyze_cid_corruption(text):
    """Analyze CID corruption level in text"""
    if not text:
        return 0.0, 0, 0
    
    # Find all CID patterns
    cid_matches = re.findall(r'\(cid:\d+\)', text)
    
    # Calculate corruption percentage
    total_chars = len(text)
    cid_chars = sum(len(match) for match in cid_matches)
    corruption_percentage = (cid_chars / total_chars) * 100 if total_chars > 0 else 0
    
    return corruption_percentage, len(cid_matches), len(set(re.findall(r'\(cid:(\d+)\)', text)))

def clean_cid_content(text):
    """Remove CID patterns from text while preserving readable content"""
    if not text:
        return text
    
    # Remove CID patterns
    cleaned = re.sub(r'\(cid:\d+\)', '', text)
    
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove empty tags that might be left
    cleaned = re.sub(r'<(\w+)>\s*</\1>', '', cleaned)
    
    return cleaned.strip()

def filter_heavily_corrupted_documents(dict_dataset, corruption_threshold=70.0):
    """Remove documents with heavy CID corruption from dataset (agnostic approach)"""
    
    print("🧹 FILTERING HEAVILY CORRUPTED DOCUMENTS")
    print("=" * 50)
    print(f"📋 Corruption threshold: {corruption_threshold}%")
    
    filtered_dataset = {}
    stats = {
        'original_total': len(dict_dataset),
        'heavily_corrupted_removed': 0,
        'lightly_corrupted_cleaned': 0,
        'clean_documents': 0,
        'final_total': 0
    }
    
    heavily_corrupted_ids = []
    
    for doc_id, doc_data in dict_dataset.items():
        # Analyze corruption level in original_text
        original_text = doc_data.get('original_text', '')
        corruption_pct, cid_count, unique_cids = analyze_cid_corruption(original_text)
        
        # Check if heavily corrupted (above threshold)
        if corruption_pct >= corruption_threshold:
            print(f"  🗑️ Removing heavily corrupted: {doc_id} ({corruption_pct:.1f}% CID)")
            heavily_corrupted_ids.append(doc_id)
            stats['heavily_corrupted_removed'] += 1
            continue
        
        # Light corruption (5-70%) - clean it
        elif corruption_pct > 5.0:
            cleaned_text = clean_cid_content(original_text)
            doc_data['original_text'] = cleaned_text
            stats['lightly_corrupted_cleaned'] += 1
            print(f"  🧽 Cleaned {doc_id}: {corruption_pct:.1f}% CID → {len(cleaned_text)} chars")
        
        # Clean document
        else:
            stats['clean_documents'] += 1
        
        filtered_dataset[doc_id] = doc_data
        stats['final_total'] += 1
    
    # Print statistics
    print(f"\n📊 FILTERING RESULTS:")
    print(f"Original documents: {stats['original_total']}")
    print(f"Heavily corrupted removed: {stats['heavily_corrupted_removed']}")
    print(f"Lightly corrupted cleaned: {stats['lightly_corrupted_cleaned']}")
    print(f"Already clean documents: {stats['clean_documents']}")
    print(f"Final dataset size: {stats['final_total']}")
    print(f"Documents removed: {((stats['heavily_corrupted_removed'] / stats['original_total']) * 100):.1f}%")
    
    if heavily_corrupted_ids:
        print(f"\n🗑️ Removed documents: {heavily_corrupted_ids}")
    
    return filtered_dataset, stats

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
        
        # Distribute samples (ID is already included in each sample)
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
        item["subject"] = original_metadata[id_]["subject"]
        item["id"] = id_
        
        final_dict[id_] = item
    
    return final_dict


def is_null_or_empty(value):
    """Check if a value is null, NaN, or empty string."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def clean_metadata_nulls(metadata):
    """
    Remove null, NaN, and empty string values from metadata.
    
    Args:
        metadata: Dictionary with metadata to clean
    
    Returns:
        Cleaned metadata dictionary and count of removed fields
    """
    total_fields_removed = 0
    
    # Clean each document
    for doc_id, doc_metadata in metadata.items():
        fields_to_remove = []
        
        # Find fields with null/empty values
        for field, value in doc_metadata.items():
            if is_null_or_empty(value):
                fields_to_remove.append(field)
        
        # Remove the null/empty fields
        for field in fields_to_remove:
            del doc_metadata[field]
            total_fields_removed += 1
    
    print(f"Metadata cleaning: {total_fields_removed} null/empty fields removed")
    return metadata, total_fields_removed


def normalize_and_split_dataset(json_filename,original_json_filename,split_filename):
    data = read_data_json(json_filename,"utf-8")
    original_metadata = read_data_json(original_json_filename,"utf-8")
    
    # Clean null/empty values before normalization
    data, removed_fields = clean_metadata_nulls(data)
    
    # Filter heavily corrupted documents (>70% CID) and clean lightly corrupted ones
    data, corruption_stats = filter_heavily_corrupted_documents(data, corruption_threshold=70.0)
    
    data = final_normalization_post_llm(data,original_metadata)
    write_to_json(split_filename,split_dataset(data),"utf-8")