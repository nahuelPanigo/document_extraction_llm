"""
Base strategy pattern for model implementations
Moved from model_comparison_framework.py for reuse in training scripts
"""
from abc import ABC, abstractmethod


class ModelStrategy(ABC):
    """Abstract base class for model strategies"""
    
    @abstractmethod
    def load_model(self):
        """Load the trained model"""
        pass
    
    @abstractmethod
    def predict(self, X_test):
        """Make predictions on test data"""
        pass
    
    @abstractmethod
    def get_model_name(self):
        """Get model name for display"""
        pass
    
    @abstractmethod
    def get_model_files(self):
        """Get list of required model files"""
        pass


class ModelResults:
    """Container for model results - moved from comparison framework"""
    
    def __init__(self, model_name, accuracy, precision, recall, f1, predictions, confusion_matrix, 
                 total_test_time, avg_prediction_time, load_time):
        self.model_name = model_name
        self.accuracy = accuracy
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.predictions = predictions
        self.confusion_matrix = confusion_matrix
        self.total_test_time = total_test_time  # Total time to test all samples
        self.avg_prediction_time = avg_prediction_time  # Average time per sample (production metric)
        self.load_time = load_time  # Time to load the model