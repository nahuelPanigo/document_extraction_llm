"""
Model Comparison Framework for Subject Classification.
Thin wrapper around shared utils/ml_strategies/model_comparison_framework.
"""
from constants import SUBJECT_MODEL_RESULTS_FOLDER
from utils.colors.colors_terminal import Bcolors
from utils.ml_strategies.model_comparison_framework import ModelComparator as _ModelComparator
from utils.ml_strategies.model_comparison_framework import ModelResults
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


def _load_subject_data():
    """Load subject data for comparison"""
    subject_mapping = load_csv_subjects()
    return create_dataset(subject_mapping, min_frequency=5, max_per_subject=200, random_state=42)


class ModelComparator(_ModelComparator):
    """Subject-specific model comparator with default strategies"""

    def __init__(self):
        strategies = {
            'svm': SVMTrainingStrategy(kernel='linear'),
            'random_forest': RandomForestTrainingStrategy(),
            'xgboost': XGBoostTrainingStrategy(),
            'embeddings': EmbeddingsTrainingStrategy(),
            'embeddings_knn': EmbeddingsKNNTrainingStrategy(),
            'neural': NeuralTorchTrainingStrategy(),
            'minilm': MiniLMTrainingStrategy()
        }
        super().__init__(
            strategies=strategies,
            results_folder=SUBJECT_MODEL_RESULTS_FOLDER,
            load_data_fn=_load_subject_data
        )


def main():
    """Main function with user input"""
    print(f"{Bcolors.HEADER}=== Model Comparison Tool ==={Bcolors.ENDC}")

    comparator = ModelComparator()

    available_models = {
        'svm': 'SVM (Linear)',
        'random_forest': 'Random Forest',
        'xgboost': 'XGBoost',
        'embeddings': 'Embeddings + Centroid',
        'embeddings_knn': 'Embeddings + KNN',
        'neural': 'Neural Network (PyTorch)',
        'minilm': 'all-MiniLM-L6-v2 (SVM)'
    }

    print(f"\nAvailable models:")
    for key, name in available_models.items():
        print(f"  {key}: {name}")

    print(f"\nEnter models to compare (comma-separated), or 'all' for all models:")
    print(f"Example: svm,xgboost")

    user_input = input("Models to test: ").strip().lower()

    if user_input == 'all':
        models_to_test = list(available_models.keys())
    else:
        models_to_test = [model.strip() for model in user_input.split(',')]

    print(f"\nTesting models: {models_to_test}")

    comparator.run_comparison(models_to_test)

if __name__ == "__main__":
    main()
