import json
import re
import sys
import os

# Add parent directory to path to import constants
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED, JSON_FOLDER


# ---------- IO ----------

def load_json():
    dataset_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- REGEX ----------

def create_isbn_regex():
    patterns = [
        r'isbn[-:\s]*(\d{10}|\d{13})',
        r'\b(\d{10}|\d{13})\b'
    ]
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def create_issn_regex():
    patterns = [
        r'issn[-:\s]*(\d{4}[-\s]?\d{3}[\dX])',
        r'\b(\d{4}[-\s]?\d{3}[\dX])\b'
    ]
    return [re.compile(p, re.IGNORECASE) for p in patterns]


# ---------- HELPERS ----------

def is_null(value):
    return value is None or value == "" or value == "null"


def exists_in_text(text, value, patterns):
    if not text or not value:
        return False

    value_norm = re.sub(r"[-\s]", "", str(value))
    text_norm = re.sub(r"[-\s]", "", text.lower())

    if value_norm.lower() in text_norm:
        return True

    for p in patterns:
        if p.search(text):
            return True

    return False


def extract_from_text(text, patterns):
    """Extract ISBN/ISSN from text using patterns"""
    if not text:
        return None
    
    for pattern in patterns:
        matches = pattern.findall(text)
        if matches:
            return matches[0]
    return None


# ---------- MAIN ----------

def normalize_by_text_only():
    dataset = load_json()

    isbn_patterns = create_isbn_regex()
    issn_patterns = create_issn_regex()

    final_dataset = {}

    add_existing_isbn = []
    add_existing_issn = []
    to_delete_isbn = []
    to_delete_issn = []
    ok_isbn = []
    ok_issn = []

    for step, records in dataset.items():
        final_dataset[step] = []
        
        for record in records:
            record_id = record.get("id")
            text = record.get("original_text", "")
            
            # Create a copy of the record to modify
            processed_record = record.copy()

            # ---------- ISBN ----------
            isbn = record.get("isbn")
            isbn_in_text = exists_in_text(text, isbn, isbn_patterns)

            if is_null(isbn) and isbn_in_text:
                # Extract ISBN from text and add to record
                extracted_isbn = extract_from_text(text, isbn_patterns)
                if extracted_isbn:
                    processed_record["isbn"] = extracted_isbn
                add_existing_isbn.append(record_id)

            elif not is_null(isbn) and not isbn_in_text:
                # Remove ISBN from record (set to null)
                processed_record["isbn"] = None
                to_delete_isbn.append(record_id)

            else:
                ok_isbn.append(record_id)

            # ---------- ISSN ----------
            issn = processed_record.get("issn")  # Use processed record in case ISBN was updated
            issn_in_text = exists_in_text(text, issn, issn_patterns)

            if is_null(issn) and issn_in_text:
                # Extract ISSN from text and add to record
                extracted_issn = extract_from_text(text, issn_patterns)
                if extracted_issn:
                    processed_record["issn"] = extracted_issn
                add_existing_issn.append(record_id)

            elif not is_null(issn) and not issn_in_text:
                # Remove ISSN from record (set to null)
                processed_record["issn"] = None
                to_delete_issn.append(record_id)

            else:
                ok_issn.append(record_id)
            
            # Add processed record to final dataset
            final_dataset[step].append(processed_record)

    # Save final dataset to JSON file
    final_dataset_path = JSON_FOLDER / "final_processed_dataset.json"
    
    with open(final_dataset_path, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)

    return {
        "add_existing_isbn": add_existing_isbn,
        "add_existing_issn": add_existing_issn,
        "to_delete_isbn": to_delete_isbn,
        "to_delete_issn": to_delete_issn,
        "ok_isbn": ok_isbn,
        "ok_issn": ok_issn,
        "final_dataset_saved": str(final_dataset_path)
    }


# ---------- RUN ----------

if __name__ == "__main__":
    result = normalize_by_text_only()

    for k, v in result.items():
        print(f"{k}: {len(v)}")
