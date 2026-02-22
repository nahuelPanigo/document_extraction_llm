#!/usr/bin/env python3
"""
Dataset creation entry point for type classification.
Runs the data pipeline steps: create types CSV, download PDFs, extract text.

Usage:
    python -m fine_tune_type.make_dataset                 # Interactive mode
    python -m fine_tune_type.make_dataset --all            # Run all steps
    python -m fine_tune_type.make_dataset --types          # Only create types CSV
    python -m fine_tune_type.make_dataset --download --extract  # Specific steps
"""
import sys
import argparse
from utils.colors.colors_terminal import Bcolors


def ask_pipeline_steps():
    """Ask user about optional pipeline steps"""
    steps = {}

    print(f"\n{Bcolors.OKBLUE}Data Pipeline Steps:{Bcolors.ENDC}")
    print(f"{Bcolors.WARNING}These steps prepare the dataset. Run them only if needed.{Bcolors.ENDC}")

    questions = [
        ('types', 'Create/update types CSV from SEDICI data?'),
        ('download', 'Download PDFs balanced by type (target: 500 per type)?'),
        ('extract', 'Extract plain text from PDFs (no tags)?'),
    ]

    for step_key, question in questions:
        while True:
            try:
                answer = input(f"{question} (y/N): ").lower().strip()
                if answer in ['y', 'yes']:
                    steps[step_key] = True
                    break
                elif answer in ['', 'n', 'no']:
                    steps[step_key] = False
                    break
                else:
                    print(f"{Bcolors.FAIL}Please enter 'y' for yes or 'n' for no.{Bcolors.ENDC}")
            except KeyboardInterrupt:
                print(f"\n{Bcolors.WARNING}Using default (no) for remaining steps.{Bcolors.ENDC}")
                steps[step_key] = False
                break

    return steps


def run_pipeline_steps(steps):
    """Run data pipeline steps based on flags"""

    if not any(steps.values()):
        print(f"\n{Bcolors.OKGREEN}No pipeline steps selected - using existing data{Bcolors.ENDC}")
        return

    print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}RUNNING DATA PIPELINE (TYPE){Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    if steps.get('types', False):
        print(f"\n{Bcolors.HEADER}=== Step: Creating Types CSV ==={Bcolors.ENDC}")
        try:
            from fine_tune_type.create_types_csv import create_types_csv
            create_types_csv()
            print(f"{Bcolors.OKGREEN}Types CSV created{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}Types CSV creation failed: {e}{Bcolors.ENDC}")

    if steps.get('download', False):
        print(f"\n{Bcolors.HEADER}=== Step: Downloading PDFs (balanced by type) ==={Bcolors.ENDC}")
        try:
            from fine_tune_type.download_balance_pdfs import main as main_download_pdfs
            main_download_pdfs()
            print(f"{Bcolors.OKGREEN}Download completed{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}Download failed: {e}{Bcolors.ENDC}")

    if steps.get('extract', False):
        print(f"\n{Bcolors.HEADER}=== Step: Extracting Plain Text from PDFs ==={Bcolors.ENDC}")
        try:
            from fine_tune_type.convert_pdfs_to_txt import main as main_pdf_to_txt
            main_pdf_to_txt()
            print(f"{Bcolors.OKGREEN}Text extraction completed{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}Text extraction failed: {e}{Bcolors.ENDC}")

    print(f"\n{Bcolors.OKGREEN}Pipeline steps completed!{Bcolors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description='Dataset creation for type classification')
    parser.add_argument('--all', action='store_true', help='Run all pipeline steps')
    parser.add_argument('--types', action='store_true', help='Create/update types CSV')
    parser.add_argument('--download', action='store_true', help='Download PDFs balanced by type')
    parser.add_argument('--extract', action='store_true', help='Extract plain text from PDFs')

    args = parser.parse_args()

    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}TYPE CLASSIFICATION - DATASET CREATION{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    has_flags = args.all or args.types or args.download or args.extract

    if has_flags:
        steps = {
            'types': args.all or args.types,
            'download': args.all or args.download,
            'extract': args.all or args.extract,
        }
    else:
        steps = ask_pipeline_steps()

    run_pipeline_steps(steps)


if __name__ == "__main__":
    main()
