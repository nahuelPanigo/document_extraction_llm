import json
import re
import sys
import os

# Add parent directory to path to import constants
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED, JSON_FOLDER



def load_json():
    dataset_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"Error: Dataset file not found at {dataset_path}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in dataset file: {e}")
        return

    return dataset


def create_isbn_regex():
    """Create regex patterns for ISBN validation in text"""
    # ISBN patterns: ISBN-10 and ISBN-13 with various formats
    patterns = [
        # ISBN with hyphens or spaces
        r'isbn[-:\s]*(\d{1,5}[-\s]?\d{1,7}[-\s]?\d{1,7}[-\s]?[\dX])',
        r'isbn[-:\s]*(\d{3}[-\s]?\d{1,5}[-\s]?\d{1,7}[-\s]?\d{1,7}[-\s]?\d)',
        # ISBN without prefix
        r'\b(\d{1,5}[-\s]?\d{1,7}[-\s]?\d{1,7}[-\s]?[\dX])\b',
        r'\b(\d{3}[-\s]?\d{1,5}[-\s]?\d{1,7}[-\s]?\d{1,7}[-\s]?\d)\b',
        # Clean numbers that could be ISBN (10 or 13 digits)
        r'\b(\d{10}|\d{13})\b'
    ]
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def create_issn_regex():
    """Create regex patterns for ISSN validation in text"""
    # ISSN patterns: XXXX-XXXX format
    patterns = [
        # ISSN with prefix
        r'issn[-:\s]*(\d{4}[-\s]?\d{3}[\dX])',
        # ISSN without prefix
        r'\b(\d{4}[-\s]?\d{3}[\dX])\b'
    ]
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def normalize_identifier(identifier):
    """Normalize ISBN/ISSN by removing spaces and hyphens"""
    if not identifier:
        return ""
    return re.sub(r'[-\s]', '', str(identifier).strip())


def search_identifier_in_text(text, identifier, regex_patterns):
    """Search for identifier in text using regex patterns"""
    if not text or not identifier:
        return False
    
    normalized_identifier = normalize_identifier(identifier)
    text_lower = text.lower()
    
    # Direct search for normalized identifier
    if normalized_identifier.lower() in text_lower:
        return True
    
    # Regex pattern search
    for pattern in regex_patterns:
        matches = pattern.findall(text_lower)
        for match in matches:
            normalized_match = normalize_identifier(match)
            if normalized_match == normalized_identifier:
                return True
    
    return False


def check_isbn_issn_in_dataset():
    """Main function to check ISBN and ISSN in dataset"""
    
    # Load dataset
    dataset= load_json()
    
    # Create regex patterns
    isbn_patterns = create_isbn_regex()
    issn_patterns = create_issn_regex()
    
    # Collections for mismatches
    isbn_should_be_null = []
    issn_should_be_null = []
    
    # Collections for IDs
    isbn_mismatch_ids = []
    issn_mismatch_ids = []
    
    # Statistics counters
    total_records = 0
    isbn_null_count = 0
    isbn_exists_count = 0
    isbn_ok_count = 0
    issn_null_count = 0
    issn_exists_count = 0
    issn_ok_count = 0
    
    # Process each step (test, validation, training)
    for step_name, step_data in dataset.items():
        print(f"Processing {step_name} step with {len(step_data)} records")
        
        # Process each record in the step
        for i, record in enumerate(step_data):
            total_records += 1
            
            if 'original_text' not in record:
                continue
                
            original_text = record['original_text']
            record_id = record.get('id', 'unknown')
            
            # Check ISBN
            if 'isbn' not in record or not record['isbn'] or record['isbn'] == 'null':
                isbn_null_count += 1
            else:
                isbn_exists_count += 1
                isbn_found = search_identifier_in_text(original_text, record['isbn'], isbn_patterns)
                if isbn_found:
                    isbn_ok_count += 1
                else:
                    isbn_should_be_null.append({
                        'step': step_name,
                        'index': i,
                        'id': record_id,
                        'isbn': record['isbn'],
                        'title': record.get('title', 'No title')[:100]
                    })
                    isbn_mismatch_ids.append(record_id)
            
            # Check ISSN
            if 'issn' not in record or not record['issn'] or record['issn'] == 'null':
                issn_null_count += 1
            else:
                issn_exists_count += 1
                issn_found = search_identifier_in_text(original_text, record['issn'], issn_patterns)
                if issn_found:
                    issn_ok_count += 1
                else:
                    issn_should_be_null.append({
                        'step': step_name,
                        'index': i,
                        'id': record_id,
                        'issn': record['issn'],
                        'title': record.get('title', 'No title')[:100]
                    })
                    issn_mismatch_ids.append(record_id)
    
    # Print detailed results
    print(f"\n" + "="*50)
    print("RESULTS")
    print("="*50)
    
    print(f"\nTotal records: {total_records}")
    
    print(f"\nISBN Statistics:")
    print(f"  Null: {isbn_null_count}")
    print(f"  Exists: {isbn_exists_count}")
    print(f"  OK (found in text): {isbn_ok_count}")
    print(f"  Mismatches (should be null): {len(isbn_should_be_null)}")
    
    print(f"\nISSN Statistics:")
    print(f"  Null: {issn_null_count}")
    print(f"  Exists: {issn_exists_count}")
    print(f"  OK (found in text): {issn_ok_count}")
    print(f"  Mismatches (should be null): {len(issn_should_be_null)}")
    
    print(f"\nTotal mismatches: {len(isbn_should_be_null) + len(issn_should_be_null)}")
    
    # Print IDs as collections
    if isbn_mismatch_ids:
        print(f"\nISBN mismatch IDs: {isbn_mismatch_ids}")
    if issn_mismatch_ids:
        print(f"\nISSN mismatch IDs: {issn_mismatch_ids}")
    
    # Breakdown by step
    if isbn_should_be_null or issn_should_be_null:
        print(f"\nBreakdown by step:")
        for step in ['test', 'validation', 'training']:
            isbn_count = len([x for x in isbn_should_be_null if x['step'] == step])
            issn_count = len([x for x in issn_should_be_null if x['step'] == step])
            print(f"  {step}: ISBN={isbn_count}, ISSN={issn_count}")
    
    return isbn_should_be_null, issn_should_be_null



def get_journal_title(id,step,data):
    try:
        for elem in data[step]:
            if elem['id'] == id:
                return elem['journalTitle']
        return "No title"
    except Exception as e:
        print(e)
        return "No title"


if __name__ == "__main__":
    isbn, issn = check_isbn_issn_in_dataset()


    data = load_json()
    docs = [x.replace(".pdf","") for x in  os.listdir("./data/sedici/pdfs/")]
    estan = []
    for elem in issn:
        id = elem['id']
        step = elem['step']
        if id in docs:
            elem = data[step]
            journal_title = get_journal_title(id,step,data)
            estan.append((id,step,journal_title))
    
    print(estan)