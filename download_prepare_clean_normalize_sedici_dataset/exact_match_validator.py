import re
from utils.text_extraction.read_and_write_files import read_data_json, write_to_json


# Creative Commons pattern for rights validation
cc_pattern = re.compile(
    r"""
    (                           
        # Variante larga (Creative Commons ... versión)
        (?:licencia\s*)?creative\s*commons
        .*?(?:\b\d+\.\d+\b)?     # allow optional version

    |   # Variante abreviada (CC BY, CC-BY-NC-SA, etc.)
        cc[-\s]*by               # CC BY or CC-BY
        (?:[-\s]?[a-z]+)*        # NC, SA, etc.
        (?:\s*\d+\.\d+(?:\s*\w+)?)?  # version like 4.0, 3.0 Unported (optional)

    |   # Variante con URL oficial
        https?://creativecommons\.org/licenses/
        [\w\-/]*
        (?:/\d+\.\d+[^/\s]*)?    # version optional, may have suffix
    )
    """,
    flags=re.IGNORECASE | re.VERBOSE
)


def validate_rights_field(value, text):
    """Validate rights field using Creative Commons pattern."""
    if value:
        match = cc_pattern.search(text)
        if match:
            return True
    return False


def validate_field_in_text(key, value, text):
    """Validate if a field value is present in the text."""
    if key == "rights":
        return validate_rights_field(value, text)
    elif key in ["dc.uri", "sedici.uri", "rightsurl"]:
        if value:
            return value.lower() in text.lower()
        return False
    return False


def apply_exact_match_validation(checked_filename, original_filename):
    """
    Apply exact match validation using original data and update checked data.
    Validates original values against text and puts original value if valid, null if not.
    Rights and rightsurl are correlated - both get same validation result.
    
    Args:
        checked_filename: Path to the Gemini-checked metadata JSON file (will be updated)
        original_filename: Path to the original metadata JSON file
    """
    exact_match_fields = ["rights", "rightsurl", "sedici.uri", "dc.uri"]
    
    # Read data
    checked_data = read_data_json(checked_filename, "utf-8")
    original_data = read_data_json(original_filename, "utf-8")
    
    # Track validation results
    validation_stats = {field: {"ok": 0, "failed": 0} for field in exact_match_fields}
    
    # Process each document
    for doc_id, metadata in checked_data.items():
        if doc_id not in original_data:
            continue
            
        original_record = original_data[doc_id]
        text = metadata.get("original_text", "")
        
        # Handle rights and rightsurl together (correlated)
        rights_valid = False
        if "rights" in original_record or "rightsurl" in original_record:
            # Check if either rights or rightsurl validates
            rights_original = original_record.get("rights")
            rightsurl_original = original_record.get("rightsurl")
            
            rights_check = validate_field_in_text("rights", rights_original, text) if rights_original else False
            rightsurl_check = validate_field_in_text("rightsurl", rightsurl_original, text) if rightsurl_original else False
            
            # If either validates, both are valid
            rights_valid = rights_check or rightsurl_check
            
            # Apply result to both fields
            if "rights" in original_record:
                if rights_valid:
                    checked_data[doc_id]["rights"] = rights_original
                    validation_stats["rights"]["ok"] += 1
                else:
                    checked_data[doc_id]["rights"] = None
                    validation_stats["rights"]["failed"] += 1
                    
            if "rightsurl" in original_record:
                if rights_valid:
                    checked_data[doc_id]["rightsurl"] = rightsurl_original
                    validation_stats["rightsurl"]["ok"] += 1
                else:
                    checked_data[doc_id]["rightsurl"] = None
                    validation_stats["rightsurl"]["failed"] += 1
        
        # Handle sedici.uri and dc.uri independently
        for field in ["sedici.uri", "dc.uri"]:
            if field in original_record:
                original_value = original_record[field]
                
                if original_value:
                    is_valid = validate_field_in_text(field, original_value, text)
                    
                    if is_valid:
                        checked_data[doc_id][field] = original_value
                        validation_stats[field]["ok"] += 1
                    else:
                        checked_data[doc_id][field] = None
                        validation_stats[field]["failed"] += 1
    
    # Save updated checked data
    write_to_json(checked_filename, checked_data, "utf-8")
    
    # Print validation statistics
    print("Exact match validation results:")
    for field, stats in validation_stats.items():
        total = stats["ok"] + stats["failed"]
        if total > 0:
            print(f"{field}: {stats['ok']} ok, {stats['failed']} set to null ({stats['failed']/total*100:.1f}% failed)")
    
    return validation_stats