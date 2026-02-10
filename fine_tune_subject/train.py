#!/usr/bin/env python3
"""
Training entry point for subject classification models.

Usage:
    python -m fine_tune_subject.train                # Interactive model selection
    python -m fine_tune_subject.train svm            # Train single model
    python -m fine_tune_subject.train all             # Train all models + ranking
    python -m fine_tune_subject.train all --compare   # Train all + comparison charts
"""
import sys
import argparse
import numpy as np
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


def train_all_models(run_compare=False):
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
            print(f"{Bcolors.OKGREEN}{result['model_name']}: {result['accuracy']:.4f}{Bcolors.ENDC}")
            successful_models.append((model_name, result['accuracy'], result['model_name']))
        else:
            print(f"{Bcolors.FAIL}{result['model_name']}: FAILED{Bcolors.ENDC}")

    if successful_models:
        # Sort by accuracy
        successful_models.sort(key=lambda x: x[1], reverse=True)

        print(f"\n{Bcolors.HEADER}RANKING (by accuracy):{Bcolors.ENDC}")
        for i, (model_name, accuracy, display_name) in enumerate(successful_models, 1):
            print(f"{i}. {display_name}: {accuracy:.4f}")

        best_model = successful_models[0]
        print(f"\n{Bcolors.OKGREEN}Best Model: {best_model[2]} ({best_model[1]:.4f}){Bcolors.ENDC}")

    # Run comparison framework if requested
    if run_compare:
        print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
        print(f"{Bcolors.HEADER}RUNNING MODEL COMPARISON{Bcolors.ENDC}")
        print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
        try:
            from fine_tune_subject.model_comparison_framework import ModelComparator
            comparator = ModelComparator()
            models_to_test = [m[0] for m in successful_models]
            comparator.run_comparison(models_to_test)
        except Exception as e:
            print(f"{Bcolors.FAIL}Comparison failed: {e}{Bcolors.ENDC}")


def interactive_mode():
    """Interactive training with menu"""
    np.random.seed(42)

    while True:
        menu_options = display_menu()
        choice = get_user_choice(menu_options)

        if choice == 'exit':
            print(f"\n{Bcolors.OKGREEN}Goodbye!{Bcolors.ENDC}")
            break

        if choice == 'all':
            train_all_models()
        else:
            train_single_model(choice)

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


def main():
    parser = argparse.ArgumentParser(description='Train subject classification models')
    parser.add_argument('model', nargs='?', default=None,
                       help='Model to train (svm, svm_rbf, xgboost, random_forest, embeddings, embeddings_knn, neural, minilm, all)')
    parser.add_argument('--compare', action='store_true',
                       help='Run comparison framework after training all models')

    args = parser.parse_args()

    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}SUBJECT CLASSIFICATION - MODEL TRAINING{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    np.random.seed(42)

    if args.model is None:
        # No args → interactive mode
        interactive_mode()
    elif args.model == 'all':
        train_all_models(run_compare=args.compare)
    else:
        train_single_model(args.model)


if __name__ == "__main__":
    main()
