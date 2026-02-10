#!/usr/bin/env python3
"""
Dataset creation entry point for subject classification.
Runs the data pipeline steps: create subjects CSV, download PDFs (balanced), extract text, clean.

Usage:
    python -m fine_tune_subject.make_dataset                 # Interactive mode
    python -m fine_tune_subject.make_dataset --all           # Run all steps
    python -m fine_tune_subject.make_dataset --subjects      # Only create subjects CSV
    python -m fine_tune_subject.make_dataset --download --extract  # Specific steps
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
        ('subjects', 'Create/update subjects CSV from SEDICI data?'),
        ('download', 'Download PDFs balanced by subject (target: 200 per subject)?'),
        ('extract', 'Extract text from PDFs?'),
        ('clean', 'Clean XML/HTML tags from extracted text?')
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
    print(f"{Bcolors.HEADER}RUNNING DATA PIPELINE{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    if steps.get('subjects', False):
        print(f"\n{Bcolors.HEADER}=== Step: Creating Subjects CSV ==={Bcolors.ENDC}")
        try:
            from fine_tune_subject.create_subjects_csv import create_subjects_csv
            create_subjects_csv()
            print(f"{Bcolors.OKGREEN}Subjects CSV created{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}Subjects CSV creation failed: {e}{Bcolors.ENDC}")

    if steps.get('download', False):
        print(f"\n{Bcolors.HEADER}=== Step: Downloading PDFs (balanced) ==={Bcolors.ENDC}")
        try:
            from fine_tune_subject.download_balance_pdfs import main as main_download_pdfs
            main_download_pdfs()
            print(f"{Bcolors.OKGREEN}Download completed{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}Download failed: {e}{Bcolors.ENDC}")

    if steps.get('extract', False):
        print(f"\n{Bcolors.HEADER}=== Step: Extracting Text from PDFs ==={Bcolors.ENDC}")
        try:
            from fine_tune_subject.convert_pdfs_to_txt import main as main_pdf_to_txt
            main_pdf_to_txt()
            print(f"{Bcolors.OKGREEN}Text extraction completed{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}Text extraction failed: {e}{Bcolors.ENDC}")

    if steps.get('clean', False):
        print(f"\n{Bcolors.HEADER}=== Step: Cleaning XML/HTML Tags ==={Bcolors.ENDC}")
        try:
            from fine_tune_subject.check_and_clean_xml_tags import main as main_clean_tags
            main_clean_tags()
            print(f"{Bcolors.OKGREEN}Text cleaning completed{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}Text cleaning failed: {e}{Bcolors.ENDC}")

    print(f"\n{Bcolors.OKGREEN}Pipeline steps completed!{Bcolors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description='Dataset creation for subject classification')
    parser.add_argument('--all', action='store_true', help='Run all pipeline steps')
    parser.add_argument('--subjects', action='store_true', help='Create/update subjects CSV')
    parser.add_argument('--download', action='store_true', help='Download PDFs balanced by subject')
    parser.add_argument('--extract', action='store_true', help='Extract text from PDFs')
    parser.add_argument('--clean', action='store_true', help='Clean XML/HTML tags')

    args = parser.parse_args()

    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}SUBJECT CLASSIFICATION - DATASET CREATION{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    # Check if any CLI flags were provided
    has_flags = args.all or args.subjects or args.download or args.extract or args.clean

    if has_flags:
        # Non-interactive mode
        steps = {
            'subjects': args.all or args.subjects,
            'download': args.all or args.download,
            'extract': args.all or args.extract,
            'clean': args.all or args.clean,
        }
    else:
        # Interactive mode
        steps = ask_pipeline_steps()

    run_pipeline_steps(steps)


if __name__ == "__main__":
    main()
