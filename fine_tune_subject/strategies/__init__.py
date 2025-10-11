"""
Model training strategies for subject classification
Each strategy is implemented in its own file for better maintainability
"""
from .svm_strategy import SVMTrainingStrategy, train_svm_model
from .xgboost_strategy import XGBoostTrainingStrategy, train_xgboost_model
from .random_forest_strategy import RandomForestTrainingStrategy, train_random_forest_model
from .embeddings_strategy import EmbeddingsTrainingStrategy, train_embeddings_model
from .embeddings_knn_strategy import EmbeddingsKNNTrainingStrategy, train_embeddings_knn_model
from .neural_torch_strategy import NeuralTorchTrainingStrategy, train_neural_torch_model
from .minilm_strategy import MiniLMTrainingStrategy, train_minilm_model

__all__ = [
    # Strategy classes
    'SVMTrainingStrategy',
    'XGBoostTrainingStrategy', 
    'RandomForestTrainingStrategy',
    'EmbeddingsTrainingStrategy',
    'EmbeddingsKNNTrainingStrategy',
    'NeuralTorchTrainingStrategy',
    'MiniLMTrainingStrategy',
    # Convenience functions
    'train_svm_model',
    'train_xgboost_model', 
    'train_random_forest_model',
    'train_embeddings_model',
    'train_embeddings_knn_model',
    'train_neural_torch_model',
    'train_minilm_model'
]