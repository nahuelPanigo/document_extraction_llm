"""
Shared evaluation and model saving utilities
Eliminates duplication across training scripts
"""
import joblib
import pickle
from sklearn.metrics import classification_report, accuracy_score
from utils.colors.colors_terminal import Bcolors


def print_results(accuracy, y_test, y_pred, label_encoder_or_classes, model_name="Model"):
    """
    Standardized results printing across all training scripts
    
    Args:
        accuracy: Model accuracy score
        y_test: True labels (encoded or string)
        y_pred: Predicted labels (encoded or string) 
        label_encoder_or_classes: LabelEncoder object or list of class names
        model_name: Name of the model for display
    """
    print(f"\n{Bcolors.HEADER}=== {model_name} Results ==={Bcolors.ENDC}")
    print(f"Accuracy: {accuracy:.4f}")
    
    # Handle both LabelEncoder objects and direct class lists
    if hasattr(label_encoder_or_classes, 'classes_'):
        target_names = label_encoder_or_classes.classes_
    else:
        target_names = label_encoder_or_classes
    
    print(f"\nComplete classification report:")
    print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))


def save_model_artifacts(model, vectorizer, label_encoder, model_prefix, additional_data=None):
    """
    Standardized model saving across all training scripts
    
    Args:
        model: Trained model object
        vectorizer: TF-IDF vectorizer or None for embedding models
        label_encoder: LabelEncoder object
        model_prefix: Prefix for model files (e.g., 'svm', 'xgboost')
        additional_data: Dict with additional data to save (for embedding models)
    """
    print(f"\n{Bcolors.OKGREEN}Saving {model_prefix} model artifacts...{Bcolors.ENDC}")
    
    # Save main model
    model_filename = f'{model_prefix}_classifier.pkl'
    joblib.dump(model, model_filename)
    print(f"Model saved: {model_filename}")
    
    # Save vectorizer if provided
    if vectorizer is not None:
        vectorizer_filename = f'{model_prefix}_vectorizer.pkl'
        joblib.dump(vectorizer, vectorizer_filename)
        print(f"Vectorizer saved: {vectorizer_filename}")
    
    # Save label encoder
    encoder_filename = f'{model_prefix}_label_encoder.pkl'
    joblib.dump(label_encoder, encoder_filename)
    print(f"Label encoder saved: {encoder_filename}")
    
    # Save additional data if provided (for embedding models)
    if additional_data:
        additional_filename = f'{model_prefix}_additional_data.pkl'
        with open(additional_filename, 'wb') as f:
            pickle.dump(additional_data, f)
        print(f"Additional data saved: {additional_filename}")
    
    print(f"{Bcolors.OKGREEN}All artifacts saved successfully!{Bcolors.ENDC}")


def calculate_accuracy(y_test, y_pred):
    """Calculate accuracy score with consistent handling"""
    return accuracy_score(y_test, y_pred)