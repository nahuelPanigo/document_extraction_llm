"""
Shared PDF download utility.
Robust download logic with timeout, retries, and rate-limit handling.
"""
import requests
import time
from constants import PDF_URL
from utils.colors.colors_terminal import Bcolors


def transform_id(doc_id):
    """Transform ID from handle format (10915-123) to path format (10915/123)"""
    return doc_id.replace("-", "/")


def download_pdf(doc_id, pdf_folder):
    """
    Download a single PDF. Returns True if done (success or permanent fail),
    False if should retry (e.g. rate limited).
    """
    transformed_id = transform_id(doc_id)
    url = f"{PDF_URL}{transformed_id}/Documento_completo.pdf?sequence=1&isAllowed=y"
    file_path = pdf_folder / f"{doc_id}.pdf"

    if file_path.exists():
        return True

    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return True
        elif response.status_code == 429:
            print(f"{Bcolors.WARNING}  Rate limited. Waiting 10s...{Bcolors.ENDC}")
            time.sleep(10)
            return False  # Retry
        else:
            print(f"{Bcolors.FAIL}  HTTP {response.status_code}{Bcolors.ENDC}")
            return True  # Don't retry

    except requests.exceptions.RequestException as e:
        print(f"{Bcolors.FAIL}  Error: {e}{Bcolors.ENDC}")
        return True  # Don't retry


def download_batch(ids_to_download, pdf_folder, label_key=None):
    """
    Download a batch of PDFs with retry logic and progress.

    Args:
        ids_to_download: list of (doc_id, label) tuples or list of doc_ids
        pdf_folder: Path to save PDFs
        label_key: optional label name for display (e.g. 'subject', 'type')
    """
    if not ids_to_download:
        print(f"{Bcolors.OKGREEN}Nothing to download!{Bcolors.ENDC}")
        return

    pdf_folder.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    failed = 0
    skipped = 0
    total = len(ids_to_download)

    for i, item in enumerate(ids_to_download, 1):
        # Support both (doc_id, label) tuples and plain doc_ids
        if isinstance(item, tuple):
            doc_id, label = item
        else:
            doc_id, label = item, None

        file_path = pdf_folder / f"{doc_id}.pdf"
        if file_path.exists():
            skipped += 1
            continue

        display = f"[{i}/{total}] {doc_id}"
        if label:
            display += f" ({label})"
        print(display, end=" ")

        max_retries = 3
        success = False
        for attempt in range(max_retries):
            done = download_pdf(doc_id, pdf_folder)
            if done:
                if file_path.exists():
                    print(f"{Bcolors.OKGREEN}OK{Bcolors.ENDC}")
                    downloaded += 1
                    success = True
                else:
                    failed += 1
                    success = True
                break

        if not success:
            print(f"{Bcolors.FAIL}FAILED (max retries){Bcolors.ENDC}")
            failed += 1

        time.sleep(1)  # Be respectful to the server

    print(f"\n{Bcolors.HEADER}=== Download Summary ==={Bcolors.ENDC}")
    print(f"{Bcolors.OKGREEN}Downloaded: {downloaded}{Bcolors.ENDC}")
    if skipped:
        print(f"{Bcolors.OKBLUE}Already existed: {skipped}{Bcolors.ENDC}")
    if failed:
        print(f"{Bcolors.FAIL}Failed: {failed}{Bcolors.ENDC}")
