"""
Base training strategy pattern for model implementations
Defines the interface for training different model types
"""
from abc import ABC, abstractmethod


class TrainingStrategy(ABC):
    """Abstract base class for training strategies"""
    
    @abstractmethod
    def train(self, documents, labels):
        """
        Train the model with the given documents and labels
        
        Args:
            documents: List of text documents
            labels: List of corresponding labels
            
        Returns:
            float: Training accuracy or relevant metric
        """
        pass
    
    @abstractmethod
    def get_model_name(self):
        """Get model name for display"""
        pass
    
    @abstractmethod
    def get_model_files(self):
        """Get list of model files that will be saved"""
        pass
    
    def get_default_params(self):
        """Get default parameters for this strategy"""
        return {}


class TrainingResults:
    """Container for training results"""
    
    def __init__(self, model_name, accuracy, train_time, model_files_saved):
        self.model_name = model_name
        self.accuracy = accuracy
        self.train_time = train_time
        self.model_files_saved = model_files_saved