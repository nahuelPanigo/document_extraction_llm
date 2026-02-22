#!/usr/bin/env python3
"""
Training entry point for type classification models.

Usage:
    python -m fine_tune_type.train                # Interactive model selection
    python -m fine_tune_type.train svm            # Train single model
    python -m fine_tune_type.train all             # Train all models + ranking
    python -m fine_tune_type.train all --compare   # Train all + comparison charts
    python -m fine_tune_type.train --compare-only  # Compare already-trained models (no training)
"""
import sys
import argparse
import numpy as np
from constants import CSV_FOLDER, CSV_TYPES, TXT_NO_TAGS_FOLDER, TYPE_MODEL_FOLDERS, SAMPLES_PER_TYPE
from utils.colors.colors_terminal import Bcolors
from utils.ml_strategies.data_loader import load_csv_labels, create_dataset
from utils.ml_strategies.strategies import (
    SVMTrainingStrategy,
    XGBoostTrainingStrategy,
    RandomForestTrainingStrategy,
    EmbeddingsTrainingStrategy,
    EmbeddingsKNNTrainingStrategy,
    NeuralTorchTrainingStrategy,
    MiniLMTrainingStrategy
)


def load_type_data():
    """Load type classification data"""
    type_mapping = load_csv_labels(CSV_FOLDER / CSV_TYPES, label_column='type')
    return create_dataset(
        type_mapping, TXT_NO_TAGS_FOLDER,
        min_frequency=5, max_per_label=SAMPLES_PER_TYPE, random_state=42
    )


def get_available_strategies():
    """Get mapping of available training strategies with type-specific model dirs"""
    return {
        'svm': lambda: SVMTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['svm_linear'], kernel='linear'),
        'svm_rbf': lambda: SVMTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['svm_rbf'], kernel='rbf'),
        'xgboost': lambda: XGBoostTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['xgboost']),
        'random_forest': lambda: RandomForestTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['random_forest']),
        'embeddings': lambda: EmbeddingsTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['embeddings']),
        'embeddings_knn': lambda: EmbeddingsKNNTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['embeddings_knn']),
        'neural': lambda: NeuralTorchTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['neural']),
        'minilm': lambda: MiniLMTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['minilm']),
    }


def display_menu():
    """Display the model selection menu"""
    strategies = get_available_strategies()

    print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}TYPE CLASSIFICATION - MODEL SELECTION{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    print(f"\n{Bcolors.OKBLUE}Available Models:{Bcolors.ENDC}")

    menu_options = []
    for i, (key, strategy_fn) in enumerate(strategies.items(), 1):
        strategy = strategy_fn()
        print(f"{i}. {strategy.get_model_name()}")
        menu_options.append(key)

    print(f"{len(menu_options) + 1}. Train All Models")
    print(f"{len(menu_options) + 2}. Compare Models (no training)")
    print(f"{len(menu_options) + 3}. Exit")

    return menu_options


def get_user_choice(menu_options):
    """Get user's model choice"""
    max_choice = len(menu_options) + 3

    while True:
        try:
            choice = input(f"\n{Bcolors.OKGREEN}Select model (1-{max_choice}): {Bcolors.ENDC}")
            choice_num = int(choice)

            if 1 <= choice_num <= len(menu_options):
                return menu_options[choice_num - 1]
            elif choice_num == len(menu_options) + 1:
                return 'all'
            elif choice_num == len(menu_options) + 2:
                return 'compare'
            elif choice_num == len(menu_options) + 3:
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
    documents, labels, document_ids = load_type_data()

    if len(documents) == 0:
        print(f"{Bcolors.FAIL}No documents found!{Bcolors.ENDC}")
        return None

    strategy = strategies[model_name]()

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
    documents, labels, document_ids = load_type_data()

    if len(documents) == 0:
        print(f"{Bcolors.FAIL}No documents found!{Bcolors.ENDC}")
        return

    # Train each model
    for model_name, strategy_fn in strategies.items():
        print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
        print(f"{Bcolors.HEADER}Training {model_name.upper()}{Bcolors.ENDC}")
        print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

        try:
            strategy = strategy_fn()
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
                'model_name': strategy_fn().get_model_name(),
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
            from fine_tune_type.model_comparison_framework import TypeModelComparator
            comparator = TypeModelComparator()
            models_to_test = [m[0] for m in successful_models]
            comparator.run_comparison(models_to_test)
        except Exception as e:
            print(f"{Bcolors.FAIL}Comparison failed: {e}{Bcolors.ENDC}")


def run_comparison_only():
    """Run comparison framework on already-trained models (no training)"""
    print(f"\n{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}MODEL COMPARISON (using saved models){Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    from fine_tune_type.model_comparison_framework import TypeModelComparator
    comparator = TypeModelComparator()
    all_models = list(get_available_strategies().keys())
    comparator.run_comparison(all_models)


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
            train_all_models(run_compare=True)
        elif choice == 'compare':
            run_comparison_only()
        else:
            train_single_model(choice)

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
    parser = argparse.ArgumentParser(description='Train type classification models')
    parser.add_argument('model', nargs='?', default=None,
                       help='Model to train (svm, svm_rbf, xgboost, random_forest, embeddings, embeddings_knn, neural, minilm, all)')
    parser.add_argument('--compare', action='store_true',
                       help='Run comparison framework after training all models')
    parser.add_argument('--compare-only', action='store_true',
                       help='Only compare already-trained models (no training)')

    args = parser.parse_args()

    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}TYPE CLASSIFICATION - MODEL TRAINING{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    np.random.seed(42)

    if args.compare_only:
        run_comparison_only()
    elif args.model is None:
        interactive_mode()
    elif args.model == 'all':
        train_all_models(run_compare=args.compare)
    else:
        train_single_model(args.model)


if __name__ == "__main__":
    main()
