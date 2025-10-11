"""
Embeddings + KNN training strategy for subject classification
Uses sentence transformers with KNN classifier
"""
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import numpy as np
import joblib
import pickle
from pathlib import Path
from constants import SUBJECT_MODEL_FOLDERS
from utils.colors.colors_terminal import Bcolors
from fine_tune_subject.utils.models.training_strategy import TrainingStrategy


class EmbeddingsKNNTrainingStrategy(TrainingStrategy):
    """Embeddings + KNN training strategy"""
    
    def __init__(self):
        self.model_dir = SUBJECT_MODEL_FOLDERS["embeddings_knn"]
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
    def get_model_name(self):
        return "Embeddings + KNN"
    
    def get_model_files(self):
        return [
            str(self.model_dir / "embeddings_knn_classifier.pkl"),
            str(self.model_dir / "embeddings_knn_label_encoder.pkl"),
            str(self.model_dir / "embeddings_knn_model_info.pkl")
        ]
    
    def get_default_params(self):
        return {
            'model_name': 'all-MiniLM-L6-v2',
            'batch_size': 32,
            'n_neighbors': 5,
            'weights': 'distance',
            'metric': 'cosine'
        }
    
    def train(self, documents, labels):
        """Train KNN classifier on embeddings"""
        print(f"{Bcolors.HEADER}=== Training {self.get_model_name()} ==={Bcolors.ENDC}")
        
        # Encode labels
        le = LabelEncoder()
        y = le.fit_transform(labels)
        print(f"{Bcolors.OKGREEN}Classes: {len(le.classes_)}{Bcolors.ENDC}")
        
        # Load sentence transformer model
        params = self.get_default_params()
        print(f"{Bcolors.OKBLUE}Loading sentence transformer: {params['model_name']}...{Bcolors.ENDC}")
        embedding_model = SentenceTransformer(params['model_name'])
        
        # Generate embeddings
        print(f"{Bcolors.OKBLUE}Generating embeddings...{Bcolors.ENDC}")
        embeddings = embedding_model.encode(documents, batch_size=params['batch_size'], show_progress_bar=True)
        
        print(f"Embeddings shape: {embeddings.shape}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            embeddings, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train KNN classifier
        print(f"{Bcolors.OKBLUE}Training KNN classifier...{Bcolors.ENDC}")
        knn = KNeighborsClassifier(
            n_neighbors=params['n_neighbors'],
            weights=params['weights'],
            metric=params['metric'],
            n_jobs=-1
        )
        
        knn.fit(X_train, y_train)
        
        # Evaluate
        print(f"{Bcolors.OKBLUE}Making predictions...{Bcolors.ENDC}")
        y_pred = knn.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"\nComplete classification report:")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))
        
        # Show KNN parameters
        print(f"\n{Bcolors.OKBLUE}KNN Parameters:{Bcolors.ENDC}")
        print(f"  k (neighbors): {params['n_neighbors']}")
        print(f"  Weights: {params['weights']}")
        print(f"  Metric: {params['metric']}")
        print(f"  Training samples: {X_train.shape[0]}")
        print(f"  Feature dimension: {X_train.shape[1]}")
        
        # Save models
        print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")
        
        # Save KNN classifier
        joblib.dump(knn, self.model_dir / "embeddings_knn_classifier.pkl")
        
        # Save label encoder
        joblib.dump(le, self.model_dir / "embeddings_knn_label_encoder.pkl")
        
        # Save model information
        model_info = {
            'embedding_model_name': params['model_name'],
            'embedding_dim': embeddings.shape[1],
            'knn_params': {
                'n_neighbors': params['n_neighbors'],
                'weights': params['weights'],
                'metric': params['metric']
            }
        }
        
        with open(self.model_dir / "embeddings_knn_model_info.pkl", 'wb') as f:
            pickle.dump(model_info, f)
        
        return accuracy


def train_embeddings_knn_model(documents, labels):
    """Convenience function for backward compatibility"""
    strategy = EmbeddingsKNNTrainingStrategy()
    return strategy.train(documents, labels)