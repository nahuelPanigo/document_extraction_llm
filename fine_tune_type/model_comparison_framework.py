"""
Model Comparison Framework for Type Classification.
Thin wrapper around shared utils/ml_strategies/model_comparison_framework.
"""
from constants import TYPE_MODEL_FOLDERS, TYPE_MODEL_RESULTS_FOLDER, CSV_FOLDER, CSV_TYPES, TXT_NO_TAGS_FOLDER, SAMPLES_PER_TYPE
from utils.colors.colors_terminal import Bcolors
from utils.ml_strategies.model_comparison_framework import ModelComparator as _ModelComparator
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


def _load_type_data():
    """Load type data for comparison"""
    type_mapping = load_csv_labels(CSV_FOLDER / CSV_TYPES, label_column='type')
    return create_dataset(
        type_mapping, TXT_NO_TAGS_FOLDER,
        min_frequency=5, max_per_label=SAMPLES_PER_TYPE, random_state=42
    )


class TypeModelComparator(_ModelComparator):
    """Type-specific model comparator with default strategies"""

    def __init__(self):
        strategies = {
            'svm': SVMTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['svm_linear'], kernel='linear'),
            'random_forest': RandomForestTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['random_forest']),
            'xgboost': XGBoostTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['xgboost']),
            'embeddings': EmbeddingsTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['embeddings']),
            'embeddings_knn': EmbeddingsKNNTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['embeddings_knn']),
            'neural': NeuralTorchTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['neural']),
            'minilm': MiniLMTrainingStrategy(model_dir=TYPE_MODEL_FOLDERS['minilm'])
        }
        super().__init__(
            strategies=strategies,
            results_folder=TYPE_MODEL_RESULTS_FOLDER,
            load_data_fn=_load_type_data
        )


def main():
    """Main function with user input"""
    print(f"{Bcolors.HEADER}=== Type Model Comparison Tool ==={Bcolors.ENDC}")

    comparator = TypeModelComparator()

    available_models = {
        'svm': 'SVM (Linear)',
        'random_forest': 'Random Forest',
        'xgboost': 'XGBoost',
        'embeddings': 'Embeddings + Centroid',
        'embeddings_knn': 'Embeddings + KNN',
        'neural': 'Neural Network (PyTorch)',
        'minilm': 'LaBSE (SVM)'
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
