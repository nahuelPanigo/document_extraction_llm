"""
Download PDFs balanced by document type.
Analyzes current distribution, identifies what's needed, and downloads in one step.
Target: SAMPLES_PER_TYPE PDFs per type.
"""
import pandas as pd
from constants import PDF_FOLDER, CSV_FOLDER, CSV_TYPES, SAMPLES_PER_TYPE
from utils.colors.colors_terminal import Bcolors
from utils.download.pdf_downloader import download_batch


def load_type_mapping():
    """Load type mapping from types CSV"""
    csv_path = CSV_FOLDER / CSV_TYPES
    if not csv_path.exists():
        print(f"{Bcolors.FAIL}Types CSV not found: {csv_path}{Bcolors.ENDC}")
        print(f"{Bcolors.WARNING}Run: python -m fine_tune_type.make_dataset --types{Bcolors.ENDC}")
        return {}

    df = pd.read_csv(csv_path)
    type_mapping = {}
    for _, row in df.iterrows():
        doc_id = str(row['id'])
        doc_type = row['type']
        if pd.notna(doc_type) and doc_type:
            type_mapping[doc_id] = doc_type

    print(f"{Bcolors.OKGREEN}Loaded {len(type_mapping)} documents with types{Bcolors.ENDC}")
    return type_mapping


def analyze_and_plan(type_mapping):
    """
    Analyze current PDFs, calculate what's needed per type, return IDs to download.
    Returns list of (doc_id, type) tuples to download.
    """
    existing_pdfs = set()
    if PDF_FOLDER.exists():
        for pdf_file in PDF_FOLDER.glob("*.pdf"):
            existing_pdfs.add(pdf_file.stem)

    print(f"{Bcolors.OKBLUE}Existing PDFs: {len(existing_pdfs)}{Bcolors.ENDC}")

    # Group all available IDs by type
    type_to_ids = {}
    for doc_id, doc_type in type_mapping.items():
        if doc_type not in type_to_ids:
            type_to_ids[doc_type] = []
        type_to_ids[doc_type].append(doc_id)

    ids_to_download = []

    print(f"\n{Bcolors.HEADER}=== Type Distribution ==={Bcolors.ENDC}")
    print(f"{'Type':<30} {'Have':>6} {'Available':>10} {'Need':>6}")
    print("-" * 56)

    for doc_type in sorted(type_to_ids.keys()):
        all_ids = type_to_ids[doc_type]
        have_ids = [doc_id for doc_id in all_ids if doc_id in existing_pdfs]
        missing_ids = [doc_id for doc_id in all_ids if doc_id not in existing_pdfs]

        have_count = len(have_ids)
        available_count = len(all_ids)

        need_count = max(0, SAMPLES_PER_TYPE - have_count)

        if need_count > 0:
            to_download = missing_ids[:need_count]
            ids_to_download.extend([(doc_id, doc_type) for doc_id in to_download])
            actual = len(to_download)
            shortfall = need_count - actual
            suffix = f" ({shortfall} unavailable)" if shortfall > 0 else ""
            print(f"  {doc_type:<28} {have_count:>6} {available_count:>10} {actual:>6}{suffix}")
        else:
            print(f"  {doc_type:<28} {have_count:>6} {available_count:>10} {'OK':>6}")

    print(f"\n{Bcolors.OKBLUE}Total PDFs to download: {len(ids_to_download)}{Bcolors.ENDC}")
    return ids_to_download


def main():
    """Analyze distribution and download PDFs to balance the dataset"""
    print(f"{Bcolors.HEADER}=== Balanced PDF Download (by Type) ==={Bcolors.ENDC}")
    print(f"Target: {SAMPLES_PER_TYPE} per type\n")

    # Step 1: Load type mapping
    type_mapping = load_type_mapping()
    if not type_mapping:
        return

    # Step 2: Analyze and plan downloads
    ids_to_download = analyze_and_plan(type_mapping)

    if not ids_to_download:
        print(f"{Bcolors.OKGREEN}All types already have {SAMPLES_PER_TYPE}+ PDFs!{Bcolors.ENDC}")
        return

    # Step 3: Confirm and download
    response = input(f"\nDownload {len(ids_to_download)} PDFs? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print(f"{Bcolors.OKBLUE}Cancelled.{Bcolors.ENDC}")
        return

    download_batch(ids_to_download, PDF_FOLDER)


if __name__ == "__main__":
    main()
