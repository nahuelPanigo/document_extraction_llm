"""
Analyze originPlaceInfo and institucionDesarrollo fields:
- Unique values for each field
- Which document types each field appears in (and count)
- How many nulls/empty per type

Usage:
    python -m extras.check_institucionDesarrollo_and_originPlace
"""

import json
from collections import defaultdict
from constants import JSON_FOLDER, DATASET_WITH_METADATA_AND_TEXT_DOC, DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED

FIELDS_TO_CHECK = ["originPlaceInfo", "institucionDesarrollo"]


def load_flat_dataset(path):
    """Load dataset - handles both flat dict and split (training/validation/test) format."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # If it has splits, flatten
    if "training" in data or "validation" in data or "test" in data:
        flat = {}
        for split in ["training", "validation", "test"]:
            for item in data.get(split, []):
                if isinstance(item, dict):
                    doc_id = item.get("id", "")
                    flat[doc_id] = item
        return flat
    return data


def analyze_field(dataset, field_name):
    """Analyze a single field across the dataset."""
    unique_values = set()
    by_type = defaultdict(lambda: {"total": 0, "present": 0, "null_or_empty": 0, "values": []})

    for doc_id, doc in dataset.items():
        doc_type = doc.get("dc.type") or doc.get("type") or "unknown"
        value = doc.get(field_name)

        by_type[doc_type]["total"] += 1

        if value and str(value).strip() and str(value).strip().lower() not in ("null", "none", "nan"):
            by_type[doc_type]["present"] += 1
            by_type[doc_type]["values"].append(value)
            unique_values.add(str(value))
        else:
            by_type[doc_type]["null_or_empty"] += 1

    return unique_values, dict(by_type)


def main():
    # Load both datasets
    original_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC
    checked_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED

    print("Loading datasets...")
    original_data = load_flat_dataset(original_path)
    checked_data = load_flat_dataset(checked_path)

    for field in FIELDS_TO_CHECK:
        print(f"\n{'#' * 70}")
        print(f"# FIELD: {field}")
        print(f"{'#' * 70}")

        # Analyze in ORIGINAL (uncleaned) dataset
        print(f"\n{'=' * 60}")
        print(f"IN ORIGINAL DATASET ({DATASET_WITH_METADATA_AND_TEXT_DOC})")
        print(f"{'=' * 60}")
        unique_vals, by_type = analyze_field(original_data, field)

        print(f"\nPer document type:")
        for doc_type in sorted(by_type.keys()):
            info = by_type[doc_type]
            print(f"  {doc_type}:")
            print(f"    total={info['total']}, present={info['present']}, null/empty={info['null_or_empty']}")

        print(f"\nUnique values ({len(unique_vals)} total):")
        for v in sorted(unique_vals):
            print(f"  - {v}")

        # Analyze in CHECKED (final cleaned) dataset
        print(f"\n{'=' * 60}")
        print(f"IN CLEANED DATASET ({DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED})")
        print(f"{'=' * 60}")
        unique_vals_c, by_type_c = analyze_field(checked_data, field)

        print(f"\nPer document type:")
        for doc_type in sorted(by_type_c.keys()):
            info = by_type_c[doc_type]
            print(f"  {doc_type}:")
            print(f"    total={info['total']}, present={info['present']}, null/empty={info['null_or_empty']}")

        print(f"\nUnique values ({len(unique_vals_c)} total):")
        for v in sorted(unique_vals_c):
            print(f"  - {v}")

        # Show what was lost in cleaning
        lost = unique_vals - unique_vals_c
        if lost:
            print(f"\nValues lost during cleaning ({len(lost)}):")
            for v in sorted(lost):
                print(f"  - {v}")


if __name__ == "__main__":
    main()
