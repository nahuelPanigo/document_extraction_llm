import requests
from pathlib import Path
import os
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json
from utils.consume_apis.consume_orchestrator import upload_file
from constants import URL_SERVICES_EXTRACTION,PDF_FOLDER,JSON_FOLDER,RESULT_FOLDER_VALIDATION,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,SUBJECT_MODEL_FOLDERS
import time
from dotenv import load_dotenv
import joblib



def download_pdf(id):
    host_url="http://192.168.100.15:9000"
    final_url = f"{host_url}/{id}.pdf"
    
    try:
        response = requests.get(final_url)
        if response.status_code == 200:
            pdf_path = PDF_FOLDER / f"{id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Downloaded: {id}.pdf")
            return pdf_path
        else:
            print(f"❌ Failed to download {id}.pdf - Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error downloading {id}.pdf: {e}")
        return None


unused_fields = ["dc.uri","sedici.uri","keywords","original_text"]


def remove_unused_fields(data):
    final_data = {}
    for inner_dict in data:
        cleaned_dict = {k: v for k, v in inner_dict.items() if k not in unused_fields}
        final_data[inner_dict["id"]] = cleaned_dict
    return final_data



load_dotenv()

final_dict = {}

actual_metadatas = read_data_json(RESULT_FOLDER_VALIDATION / "test_metadata_validada.json","utf-8")
original_metadatas = read_data_json(JSON_FOLDER / "sedici_finetunnig_metadata.json","utf-8")
validation_original_metadata = remove_unused_fields(original_metadatas["validation"])

cant_tesis = 15
cant_articulos = 15
cant_object_conference = 15
cant_libros = 15


actual_ids = set(actual_metadatas.keys())

# Count how many of each type we already have
type_counts = {}
for metadata in actual_metadatas.values():
    doc_type = metadata.get("type", "Unknown")
    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

print("Current counts by type:")
for t, count in type_counts.items():
    print(f"  {t}: {count}")

# Calculate how many more we need for each type
type_targets = {
    "Tesis": cant_tesis,
    "Articulo": cant_articulos,
    "Objeto de conferencia": cant_object_conference,
    "Libro": cant_libros
}

type_needed = {}
for doc_type, target in type_targets.items():
    current = type_counts.get(doc_type, 0)
    needed = max(0, target - current)
    type_needed[doc_type] = needed
    print(f"  {doc_type}: need {needed} more (have {current}/{target})")

# Track how many we've added for each type
type_added = {t: 0 for t in type_targets.keys()}

# Iterate through validation metadata and collect new items
new_items = {}

for id, metadata in validation_original_metadata.items():
    # Skip if we already have this id
    if id in actual_ids:
        continue

    # Get the document type from the original metadata
    doc_type = metadata.get("type", "Unknown")

    # Skip if type is not one of our targets
    if doc_type not in type_needed:
        continue

    # Skip if we already have enough of this type
    if type_added[doc_type] >= type_needed[doc_type]:
        continue

    # Add this item
    new_items[id] = metadata
    type_added[doc_type] += 1

    print(f"Adding {id} (type: {doc_type}) - {type_added[doc_type]}/{type_needed[doc_type]}")

    # Check if we have all we need
    if all(type_added[t] >= type_needed[t] for t in type_targets.keys()):
        print("Got all needed items!")
        break

print(f"\nTotal new items to add: {len(new_items)}")
print("Added by type:")
for doc_type, count in type_added.items():
    print(f"  {doc_type}: {count}/{type_needed[doc_type]}")

# Write the new items to a file
output_file = RESULT_FOLDER_VALIDATION / "test_metadata_to_validate.json"
write_to_json(output_file,new_items, "utf-8")
print(f"\nWritten {len(new_items)} items to {output_file}")

# Now process each new item - download PDF if needed
# (This section is for later use when you want to download and process the PDFs)
# for id, metadata in new_items.items():
#     filename = PDF_FOLDER / f"{id}.pdf"
#     if not filename.exists():
#         download_pdf(id)
#     # Then call API to extract metadata...
