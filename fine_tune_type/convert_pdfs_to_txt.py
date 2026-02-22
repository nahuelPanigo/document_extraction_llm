"""
Convert PDFs to plain text (no tags) using PdfReader.extract_text().
Saves to TXT_NO_TAGS_FOLDER for type classification training.
Uses multiprocessing for performance.
"""
import os
import sys
from pathlib import Path
from multiprocessing import Pool, cpu_count

sys.path.append(str(Path(__file__).parent.parent))
from constants import PDF_FOLDER, TXT_NO_TAGS_FOLDER, CSV_FOLDER, CSV_TYPES
from utils.colors.colors_terminal import Bcolors
from utils.text_extraction.pdf_reader import PdfReader
import pandas as pd


def get_type_ids():
    """Get list of document IDs from types CSV"""
    csv_path = CSV_FOLDER / CSV_TYPES
    if not csv_path.exists():
        print(f"{Bcolors.FAIL}Types CSV not found: {csv_path}{Bcolors.ENDC}")
        print(f"{Bcolors.WARNING}Run: python -m fine_tune_type.make_dataset --types{Bcolors.ENDC}")
        return []

    df = pd.read_csv(csv_path)
    return [str(row['id']) for _, row in df.iterrows()]


def get_pdfs_to_convert():
    """Get list of PDFs that need to be converted to TXT"""
    type_ids = get_type_ids()
    if not type_ids:
        return []

    TXT_NO_TAGS_FOLDER.mkdir(parents=True, exist_ok=True)

    pdfs_to_convert = []
    already_converted = 0

    for doc_id in type_ids:
        pdf_file = PDF_FOLDER / f"{doc_id}.pdf"
        txt_file = TXT_NO_TAGS_FOLDER / f"{doc_id}.txt"

        if not pdf_file.exists():
            continue

        if txt_file.exists():
            already_converted += 1
            continue

        pdfs_to_convert.append((doc_id, pdf_file))

    print(f"{Bcolors.OKGREEN}PDFs available: {len(pdfs_to_convert) + already_converted}{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Already converted: {already_converted}{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Need to convert: {len(pdfs_to_convert)}{Bcolors.ENDC}")

    return pdfs_to_convert


def convert_single_pdf(args):
    """Convert a single PDF to plain text (for multiprocessing)"""
    doc_id, pdf_path = args
    txt_path = TXT_NO_TAGS_FOLDER / f"{doc_id}.txt"

    try:
        pdf_reader = PdfReader()
        text = pdf_reader.extract_text(str(pdf_path), ocr=False)

        if text and text.strip():
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return (doc_id, True, None)
        else:
            return (doc_id, False, "Empty text extracted")

    except Exception as e:
        return (doc_id, False, str(e))


def main():
    """Main function to convert PDFs to plain text"""
    print(f"{Bcolors.HEADER}=== PDF to Plain Text Converter (Type Classification) ==={Bcolors.ENDC}")
    print(f"PDF folder: {PDF_FOLDER}")
    print(f"TXT folder: {TXT_NO_TAGS_FOLDER}")

    pdfs_to_convert = get_pdfs_to_convert()

    if not pdfs_to_convert:
        print(f"{Bcolors.OKGREEN}All PDFs already converted!{Bcolors.ENDC}")
        return

    # Use multiprocessing
    num_workers = max(1, cpu_count() - 1)
    print(f"\n{Bcolors.OKBLUE}Converting {len(pdfs_to_convert)} PDFs using {num_workers} workers...{Bcolors.ENDC}")

    successful = 0
    failed = 0

    with Pool(num_workers) as pool:
        for i, (doc_id, success, error) in enumerate(pool.imap_unordered(convert_single_pdf, pdfs_to_convert), 1):
            if success:
                successful += 1
                if i % 50 == 0 or i == len(pdfs_to_convert):
                    print(f"{Bcolors.OKGREEN}[{i}/{len(pdfs_to_convert)}] Converted: {successful}, Failed: {failed}{Bcolors.ENDC}")
            else:
                failed += 1
                print(f"{Bcolors.FAIL}[{i}/{len(pdfs_to_convert)}] Failed {doc_id}: {error}{Bcolors.ENDC}")

    print(f"\n{Bcolors.HEADER}=== Conversion Summary ==={Bcolors.ENDC}")
    print(f"{Bcolors.OKGREEN}Successful: {successful}{Bcolors.ENDC}")
    if failed:
        print(f"{Bcolors.FAIL}Failed: {failed}{Bcolors.ENDC}")


if __name__ == "__main__":
    main()
