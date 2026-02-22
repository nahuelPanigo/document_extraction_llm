"""
ML training strategies - shared implementations.
Each strategy accepts model_dir as constructor parameter for flexibility.
"""
from .svm_strategy import SVMTrainingStrategy
from .xgboost_strategy import XGBoostTrainingStrategy
from .random_forest_strategy import RandomForestTrainingStrategy
from .embeddings_strategy import EmbeddingsTrainingStrategy
from .embeddings_knn_strategy import EmbeddingsKNNTrainingStrategy
from .neural_torch_strategy import NeuralTorchTrainingStrategy
from .minilm_strategy import MiniLMTrainingStrategy

__all__ = [
    'SVMTrainingStrategy',
    'XGBoostTrainingStrategy',
    'RandomForestTrainingStrategy',
    'EmbeddingsTrainingStrategy',
    'EmbeddingsKNNTrainingStrategy',
    'NeuralTorchTrainingStrategy',
    'MiniLMTrainingStrategy',
]
