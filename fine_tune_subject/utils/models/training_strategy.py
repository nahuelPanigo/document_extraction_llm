"""
Base training strategy pattern - re-exports from shared utils/ml_strategies.
Kept for backward compatibility.
"""
from utils.ml_strategies.training_strategy import TrainingStrategy, TrainingResults

__all__ = ['TrainingStrategy', 'TrainingResults']
