"""
Download PDFs balanced by subject.
Analyzes current distribution, identifies what's needed, and downloads in one step.
Target: 200 PDFs per subject, skips subjects with < 5 available docs.
"""
import pandas as pd
from constants import PDF_FOLDER, CSV_FOLDER, CSV_SUBJECTS
from utils.colors.colors_terminal import Bcolors
from utils.download.pdf_downloader import download_batch


TARGET_PER_SUBJECT = 200
MIN_AVAILABLE = 5


def load_subject_mapping():
    """Load subject mapping from subjects CSV"""
    csv_path = CSV_FOLDER / CSV_SUBJECTS
    if not csv_path.exists():
        print(f"{Bcolors.FAIL}Subjects CSV not found: {csv_path}{Bcolors.ENDC}")
        print(f"{Bcolors.WARNING}Run: python -m fine_tune_subject.make_dataset --subjects{Bcolors.ENDC}")
        return {}

    df = pd.read_csv(csv_path)
    subject_mapping = {}
    for _, row in df.iterrows():
        doc_id = str(row['id'])
        subject = row['subject']
        if pd.notna(subject) and subject:
            subject_mapping[doc_id] = subject

    print(f"{Bcolors.OKGREEN}Loaded {len(subject_mapping)} documents with subjects{Bcolors.ENDC}")
    return subject_mapping


def analyze_and_plan(subject_mapping):
    """
    Analyze current PDFs, calculate what's needed per subject, return IDs to download.
    Returns list of (doc_id, subject) tuples to download.
    """
    # Get existing PDFs
    existing_pdfs = set()
    if PDF_FOLDER.exists():
        for pdf_file in PDF_FOLDER.glob("*.pdf"):
            existing_pdfs.add(pdf_file.stem)

    print(f"{Bcolors.OKBLUE}Existing PDFs: {len(existing_pdfs)}{Bcolors.ENDC}")

    # Group all available IDs by subject
    subject_to_ids = {}
    for doc_id, subject in subject_mapping.items():
        if subject not in subject_to_ids:
            subject_to_ids[subject] = []
        subject_to_ids[subject].append(doc_id)

    # Analyze per subject: what we have vs what we need
    ids_to_download = []

    print(f"\n{Bcolors.HEADER}=== Subject Distribution ==={Bcolors.ENDC}")
    print(f"{'Subject':<40} {'Have':>6} {'Available':>10} {'Need':>6}")
    print("-" * 66)

    for subject in sorted(subject_to_ids.keys()):
        all_ids = subject_to_ids[subject]
        have_ids = [doc_id for doc_id in all_ids if doc_id in existing_pdfs]
        missing_ids = [doc_id for doc_id in all_ids if doc_id not in existing_pdfs]

        have_count = len(have_ids)
        available_count = len(all_ids)

        # Skip subjects with too few available docs
        if available_count < MIN_AVAILABLE:
            print(f"  {subject:<38} {have_count:>6} {available_count:>10} {'SKIP':>6} (< {MIN_AVAILABLE} available)")
            continue

        # Calculate how many more we need
        need_count = max(0, TARGET_PER_SUBJECT - have_count)

        if need_count > 0:
            # Take up to need_count from missing IDs
            to_download = missing_ids[:need_count]
            ids_to_download.extend([(doc_id, subject) for doc_id in to_download])
            actual = len(to_download)
            shortfall = need_count - actual
            suffix = f" ({shortfall} unavailable)" if shortfall > 0 else ""
            print(f"  {subject:<38} {have_count:>6} {available_count:>10} {actual:>6}{suffix}")
        else:
            print(f"  {subject:<38} {have_count:>6} {available_count:>10} {'OK':>6}")

    print(f"\n{Bcolors.OKBLUE}Total PDFs to download: {len(ids_to_download)}{Bcolors.ENDC}")
    return ids_to_download


def main():
    """Analyze distribution and download PDFs to balance the dataset"""
    print(f"{Bcolors.HEADER}=== Balanced PDF Download ==={Bcolors.ENDC}")
    print(f"Target: {TARGET_PER_SUBJECT} per subject, min {MIN_AVAILABLE} available\n")

    # Step 1: Load subject mapping
    subject_mapping = load_subject_mapping()
    if not subject_mapping:
        return

    # Step 2: Analyze and plan downloads
    ids_to_download = analyze_and_plan(subject_mapping)

    if not ids_to_download:
        print(f"{Bcolors.OKGREEN}All subjects already have {TARGET_PER_SUBJECT}+ PDFs!{Bcolors.ENDC}")
        return

    # Step 3: Confirm and download
    response = input(f"\nDownload {len(ids_to_download)} PDFs? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print(f"{Bcolors.OKBLUE}Cancelled.{Bcolors.ENDC}")
        return

    download_batch(ids_to_download, PDF_FOLDER)


if __name__ == "__main__":
    main()
