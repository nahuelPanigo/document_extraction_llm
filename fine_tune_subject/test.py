#!/usr/bin/env python3
"""
Test trained subject classification models on a single PDF.

Usage:
    python -m fine_tune_subject.test                              # Interactive mode
    python -m fine_tune_subject.test /path/to/file.pdf            # Test all models
    python -m fine_tune_subject.test /path/to/file.pdf --model svm
"""
import sys
import argparse
from pathlib import Path

from utils.colors.colors_terminal import Bcolors
from utils.text_extraction.pdf_reader import PdfReader
from fine_tune_subject.strategies import (
    SVMTrainingStrategy,
    XGBoostTrainingStrategy,
    RandomForestTrainingStrategy,
    EmbeddingsTrainingStrategy,
    EmbeddingsKNNTrainingStrategy,
    NeuralTorchTrainingStrategy,
    MiniLMTrainingStrategy
)


def get_available_strategies():
    """Same as train.py - uses default SUBJECT_MODEL_FOLDERS"""
    return {
        'svm':           lambda: SVMTrainingStrategy(kernel='linear'),
        'svm_rbf':       lambda: SVMTrainingStrategy(kernel='rbf'),
        'xgboost':       XGBoostTrainingStrategy,
        'random_forest': RandomForestTrainingStrategy,
        'embeddings':    EmbeddingsTrainingStrategy,
        'embeddings_knn':EmbeddingsKNNTrainingStrategy,
        'neural':        NeuralTorchTrainingStrategy,
        'minilm':        MiniLMTrainingStrategy,
    }


def extract_text(pdf_path: str) -> str:
    print(f"\n{Bcolors.OKBLUE}Extracting text from: {Path(pdf_path).name}{Bcolors.ENDC}")
    text = PdfReader().extract_text(pdf_path)
    if not text.strip():
        print(f"{Bcolors.FAIL}No text extracted from PDF.{Bcolors.ENDC}")
        return ""
    print(f"{Bcolors.OKGREEN}Extracted {len(text)} chars{Bcolors.ENDC}")
    print(f"\n{Bcolors.HEADER}--- Text preview ---{Bcolors.ENDC}")
    print(text[:300].strip())
    print(f"{Bcolors.HEADER}--------------------{Bcolors.ENDC}")
    return text


def test_single_model(model_name: str, text: str):
    strategies = get_available_strategies()
    if model_name not in strategies:
        print(f"{Bcolors.FAIL}Unknown model: {model_name}. Available: {', '.join(strategies.keys())}{Bcolors.ENDC}")
        return
    strategy = strategies[model_name]()
    print(f"\n{Bcolors.HEADER}=== {strategy.get_model_name()} ==={Bcolors.ENDC}")
    if not strategy.load_model():
        print(f"{Bcolors.WARNING}No trained model found. Run training first.{Bcolors.ENDC}")
        return
    prediction = strategy.predict([text])
    print(f"{Bcolors.OKGREEN}Predicted subject: {prediction[0]}{Bcolors.ENDC}")


def test_all_models(text: str):
    strategies = get_available_strategies()
    print(f"\n{Bcolors.HEADER}{'='*55}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}SUBJECT CLASSIFICATION - RESULTS{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*55}{Bcolors.ENDC}")
    for model_name, strategy_class in strategies.items():
        strategy = strategy_class()
        if not strategy.load_model():
            print(f"  {Bcolors.WARNING}{strategy.get_model_name():<28}{Bcolors.ENDC} -> [not trained]")
            continue
        try:
            prediction = strategy.predict([text])
            print(f"  {Bcolors.OKGREEN}{strategy.get_model_name():<28}{Bcolors.ENDC} -> {Bcolors.BOLD}{prediction[0]}{Bcolors.ENDC}")
        except Exception as e:
            print(f"  {Bcolors.FAIL}{strategy.get_model_name():<28}{Bcolors.ENDC} -> ERROR: {e}")


def display_menu(strategies):
    print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}SUBJECT CLASSIFICATION - SELECT MODEL TO TEST{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"\n{Bcolors.OKBLUE}Available Models:{Bcolors.ENDC}")
    menu_options = []
    for i, (key, strategy_class) in enumerate(strategies.items(), 1):
        print(f"{i}. {strategy_class().get_model_name()}")
        menu_options.append(key)
    print(f"{len(menu_options) + 1}. Test All Models")
    print(f"{len(menu_options) + 2}. Exit")
    return menu_options


def get_user_choice(menu_options):
    max_choice = len(menu_options) + 2
    while True:
        try:
            choice = input(f"\n{Bcolors.OKGREEN}Select model (1-{max_choice}): {Bcolors.ENDC}")
            choice_num = int(choice)
            if 1 <= choice_num <= len(menu_options):
                return menu_options[choice_num - 1]
            elif choice_num == len(menu_options) + 1:
                return 'all'
            elif choice_num == len(menu_options) + 2:
                return 'exit'
            else:
                print(f"{Bcolors.FAIL}Invalid choice. Enter a number between 1 and {max_choice}.{Bcolors.ENDC}")
        except ValueError:
            print(f"{Bcolors.FAIL}Invalid input. Enter a number.{Bcolors.ENDC}")
        except KeyboardInterrupt:
            return 'exit'


def ask_pdf_path() -> str:
    while True:
        try:
            path = input(f"\n{Bcolors.OKGREEN}Enter PDF path: {Bcolors.ENDC}").strip()
            if not path:
                print(f"{Bcolors.FAIL}Path cannot be empty.{Bcolors.ENDC}")
                continue
            pdf_path = Path(path)
            if not pdf_path.exists():
                print(f"{Bcolors.FAIL}File not found: {path}{Bcolors.ENDC}")
                continue
            return str(pdf_path)
        except KeyboardInterrupt:
            return ""


def interactive_mode():
    """Called from main.py as Step 3"""
    try:
        answer = input(f"\n{Bcolors.OKBLUE}Do you want to test a PDF with the trained models? (y/N): {Bcolors.ENDC}").lower().strip()
        if answer not in ['y', 'yes']:
            return
    except KeyboardInterrupt:
        return

    while True:
        pdf_path = ask_pdf_path()
        if not pdf_path:
            break

        text = extract_text(pdf_path)
        if not text:
            continue

        strategies = get_available_strategies()
        menu_options = display_menu(strategies)
        choice = get_user_choice(menu_options)

        if choice == 'exit':
            break
        elif choice == 'all':
            test_all_models(text)
        else:
            test_single_model(choice, text)

        try:
            another = input(f"\n{Bcolors.OKBLUE}Test another PDF? (y/N): {Bcolors.ENDC}").lower().strip()
            if another not in ['y', 'yes']:
                break
        except KeyboardInterrupt:
            break

    print(f"\n{Bcolors.OKGREEN}Test session completed!{Bcolors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description='Test subject classification models on a single PDF')
    parser.add_argument('pdf', nargs='?', default=None, help='Path to the PDF file')
    parser.add_argument('--model', default=None,
                        help='Model to use (svm, svm_rbf, xgboost, random_forest, embeddings, embeddings_knn, neural, minilm)')
    args = parser.parse_args()

    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}SUBJECT CLASSIFICATION - TEST ON PDF{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    pdf_path = args.pdf or ask_pdf_path()
    if not pdf_path:
        return
    if not Path(pdf_path).exists():
        print(f"{Bcolors.FAIL}Error: PDF not found: {pdf_path}{Bcolors.ENDC}")
        sys.exit(1)

    text = extract_text(pdf_path)
    if not text:
        sys.exit(1)

    if args.model:
        test_single_model(args.model, text)
    else:
        test_all_models(text)


if __name__ == "__main__":
    main()
