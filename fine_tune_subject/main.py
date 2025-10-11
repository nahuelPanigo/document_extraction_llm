#!/usr/bin/env python3
"""
Unified Subject Classification Training
Single entry point for training all model types using the strategy pattern

Interactive model selection interface
"""
import sys
import numpy as np
from pathlib import Path

from utils.colors.colors_terminal import Bcolors
from fine_tune_subject.utils.dataset.data_loader import load_csv_subjects, create_dataset
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
    """Get mapping of available training strategies"""
    return {
        'svm': lambda: SVMTrainingStrategy(kernel='linear'),
        'svm_rbf': lambda: SVMTrainingStrategy(kernel='rbf'),
        'xgboost': XGBoostTrainingStrategy,
        'random_forest': RandomForestTrainingStrategy,
        'embeddings': EmbeddingsTrainingStrategy,
        'embeddings_knn': EmbeddingsKNNTrainingStrategy,
        'neural': NeuralTorchTrainingStrategy,
        'minilm': MiniLMTrainingStrategy
    }


def display_menu():
    """Display the model selection menu"""
    strategies = get_available_strategies()
    
    print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}SUBJECT CLASSIFICATION - MODEL SELECTION{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    
    print(f"\n{Bcolors.OKBLUE}Available Models:{Bcolors.ENDC}")
    
    menu_options = []
    for i, (key, strategy_class) in enumerate(strategies.items(), 1):
        strategy = strategy_class()
        print(f"{i}. {strategy.get_model_name()}")
        menu_options.append(key)
    
    print(f"{len(menu_options) + 1}. Train All Models")
    print(f"{len(menu_options) + 2}. Exit")
    
    return menu_options


def get_user_choice(menu_options):
    """Get user's model choice"""
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
                print(f"{Bcolors.FAIL}Invalid choice. Please enter a number between 1 and {max_choice}.{Bcolors.ENDC}")
                
        except ValueError:
            print(f"{Bcolors.FAIL}Invalid input. Please enter a number.{Bcolors.ENDC}")
        except KeyboardInterrupt:
            print(f"\n{Bcolors.WARNING}Training cancelled by user.{Bcolors.ENDC}")
            return 'exit'


def ask_pipeline_steps():
    """Ask user about optional pipeline steps"""
    steps = {}
    
    print(f"\n{Bcolors.OKBLUE}Data Pipeline Steps (run once before training):{Bcolors.ENDC}")
    print(f"{Bcolors.WARNING}These steps prepare the dataset. Run them only if needed.{Bcolors.ENDC}")
    
    questions = [
        ('download', 'Download PDFs for missing samples?'),
        ('extract', 'Extract text from PDFs?'), 
        ('balance', 'Balance dataset (limit to 200 samples per subject)?'),
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
    """Run data pipeline steps if requested"""
    
    if not any(steps.values()):
        print(f"\n{Bcolors.OKGREEN}Skipping pipeline steps - using existing data{Bcolors.ENDC}")
        return
    
    print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}RUNNING DATA PIPELINE{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    
    if steps.get('download', False):
        print(f"\n{Bcolors.HEADER}=== Step 1: Downloading PDFs ==={Bcolors.ENDC}")
        try:
            from download_balance_pdfs import main as main_download_pdfs
            main_download_pdfs()
            print(f"{Bcolors.OKGREEN}✓ Download completed{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}✗ Download failed: {e}{Bcolors.ENDC}")
            print(f"{Bcolors.WARNING}Run manually: python3 download_balance_pdfs.py{Bcolors.ENDC}")
    
    if steps.get('extract', False):
        print(f"\n{Bcolors.HEADER}=== Step 2: Extracting Text from PDFs ==={Bcolors.ENDC}")
        try:
            from convert_pdfs_to_txt import main as main_pdf_to_txt
            main_pdf_to_txt()
            print(f"{Bcolors.OKGREEN}✓ Text extraction completed{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}✗ Text extraction failed: {e}{Bcolors.ENDC}")
            print(f"{Bcolors.WARNING}Run manually: python3 convert_pdfs_to_txt.py{Bcolors.ENDC}")
    
    if steps.get('balance', False):
        print(f"\n{Bcolors.HEADER}=== Step 3: Balancing Dataset ==={Bcolors.ENDC}")
        try:
            from balance_dataset import main as main_balance_dataset
            main_balance_dataset()
            print(f"{Bcolors.OKGREEN}✓ Dataset balancing completed{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}✗ Dataset balancing failed: {e}{Bcolors.ENDC}")
            print(f"{Bcolors.WARNING}Run manually: python3 balance_dataset.py{Bcolors.ENDC}")
    
    if steps.get('clean', False):
        print(f"\n{Bcolors.HEADER}=== Step 4: Cleaning XML/HTML Tags ==={Bcolors.ENDC}")
        try:
            from check_and_clean_xml_tags import main as main_clean_tags
            main_clean_tags()
            print(f"{Bcolors.OKGREEN}✓ Text cleaning completed{Bcolors.ENDC}")
        except Exception as e:
            print(f"{Bcolors.FAIL}✗ Text cleaning failed: {e}{Bcolors.ENDC}")
            print(f"{Bcolors.WARNING}Run manually: python3 check_and_clean_xml_tags.py{Bcolors.ENDC}")
    
    print(f"\n{Bcolors.OKGREEN}Pipeline steps completed!{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Ready for model training...{Bcolors.ENDC}")


def train_single_model(model_name):
    """Train a single model using the specified strategy"""
    
    strategies = get_available_strategies()
    
    if model_name not in strategies:
        print(f"{Bcolors.FAIL}Unknown model: {model_name}{Bcolors.ENDC}")
        print(f"Available models: {', '.join(strategies.keys())}")
        return None
    
    # Load data
    print(f"\n{Bcolors.HEADER}=== Loading Data ==={Bcolors.ENDC}")
    subject_mapping = load_csv_subjects()
    documents, labels, document_ids = create_dataset(subject_mapping)
    
    if len(documents) == 0:
        print(f"{Bcolors.FAIL}No documents found!{Bcolors.ENDC}")
        return None
    
    # Initialize and train the selected strategy
    strategy_class = strategies[model_name]
    strategy = strategy_class()
    
    try:
        accuracy = strategy.train(documents, labels)
        
        print(f"\n{Bcolors.OKGREEN}Training completed!{Bcolors.ENDC}")
        print(f"Model: {strategy.get_model_name()}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Model files saved: {strategy.get_model_files()}")
        
        return accuracy
        
    except Exception as e:
        print(f"{Bcolors.FAIL}Training failed: {str(e)}{Bcolors.ENDC}")
        return None


def train_all_models():
    """Train all available models and compare results"""
    
    strategies = get_available_strategies()
    results = {}
    
    # Load data once for all models
    print(f"\n{Bcolors.HEADER}=== Loading Data ==={Bcolors.ENDC}")
    subject_mapping = load_csv_subjects()
    documents, labels, document_ids = create_dataset(subject_mapping)
    
    if len(documents) == 0:
        print(f"{Bcolors.FAIL}No documents found!{Bcolors.ENDC}")
        return
    
    # Train each model
    for model_name, strategy_class in strategies.items():
        print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
        print(f"{Bcolors.HEADER}Training {model_name.upper()}{Bcolors.ENDC}")
        print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
        
        try:
            strategy = strategy_class()
            accuracy = strategy.train(documents, labels)
            results[model_name] = {
                'accuracy': accuracy,
                'model_name': strategy.get_model_name(),
                'files': strategy.get_model_files()
            }
            
        except Exception as e:
            print(f"{Bcolors.FAIL}Training {model_name} failed: {str(e)}{Bcolors.ENDC}")
            results[model_name] = {
                'accuracy': None,
                'model_name': strategy_class().get_model_name(),
                'error': str(e)
            }
    
    # Print summary
    print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}TRAINING SUMMARY{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    
    successful_models = []
    
    for model_name, result in results.items():
        if result['accuracy'] is not None:
            print(f"{Bcolors.OKGREEN}✓ {result['model_name']}: {result['accuracy']:.4f}{Bcolors.ENDC}")
            successful_models.append((model_name, result['accuracy'], result['model_name']))
        else:
            print(f"{Bcolors.FAIL}✗ {result['model_name']}: FAILED{Bcolors.ENDC}")
    
    if successful_models:
        # Sort by accuracy
        successful_models.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n{Bcolors.HEADER}RANKING (by accuracy):{Bcolors.ENDC}")
        for i, (model_name, accuracy, display_name) in enumerate(successful_models, 1):
            print(f"{i}. {display_name}: {accuracy:.4f}")
        
        best_model = successful_models[0]
        print(f"\n{Bcolors.OKGREEN}🏆 Best Model: {best_model[2]} ({best_model[1]:.4f}){Bcolors.ENDC}")


def main():
    """Main entry point with interactive interface"""
    
    # Set random seeds for reproducibility
    np.random.seed(42)
    
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}UNIFIED SUBJECT CLASSIFICATION TRAINING{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    
    # STEP 1: Run data pipeline steps ONCE at the beginning
    pipeline_steps = ask_pipeline_steps()
    run_pipeline_steps(pipeline_steps)
    
    # STEP 2: Model training loop
    while True:
        # Show menu and get choice
        menu_options = display_menu()
        choice = get_user_choice(menu_options)
        
        if choice == 'exit':
            print(f"\n{Bcolors.OKGREEN}Goodbye!{Bcolors.ENDC}")
            break
        
        # Train model(s)
        if choice == 'all':
            train_all_models()
        else:
            accuracy = train_single_model(choice)
            if accuracy is None:
                print(f"{Bcolors.FAIL}Training failed. Please try again.{Bcolors.ENDC}")
        
        # Ask if user wants to train another model
        while True:
            try:
                another = input(f"\n{Bcolors.OKBLUE}Train another model? (y/N): {Bcolors.ENDC}").lower().strip()
                if another in ['y', 'yes']:
                    break
                elif another in ['', 'n', 'no']:
                    print(f"\n{Bcolors.OKGREEN}Training session completed!{Bcolors.ENDC}")
                    return
                else:
                    print(f"{Bcolors.FAIL}Please enter 'y' for yes or 'n' for no.{Bcolors.ENDC}")
            except KeyboardInterrupt:
                print(f"\n{Bcolors.OKGREEN}Training session completed!{Bcolors.ENDC}")
                return


if __name__ == "__main__":
    main()