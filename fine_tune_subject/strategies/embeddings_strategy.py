"""
Embeddings training strategy for subject classification
Uses sentence transformers with centroid similarity
"""
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import numpy as np
import joblib
import pickle
from pathlib import Path
from collections import defaultdict
from constants import SUBJECT_MODEL_FOLDERS
from utils.colors.colors_terminal import Bcolors
from fine_tune_subject.utils.models.training_strategy import TrainingStrategy


class EmbeddingsTrainingStrategy(TrainingStrategy):
    """Embeddings training strategy using sentence transformers"""
    
    def __init__(self):
        self.model_dir = SUBJECT_MODEL_FOLDERS["embeddings"]
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
    def get_model_name(self):
        return "Embeddings (Centroid)"
    
    def get_model_files(self):
        return [
            str(self.model_dir / "embeddings_centroids.pkl"),
            str(self.model_dir / "embeddings_label_encoder.pkl")
        ]
    
    def get_default_params(self):
        return {
            'model_name': 'all-MiniLM-L6-v2',  # Fast and good quality
            'batch_size': 32
        }
    
    def train(self, documents, labels):
        """Train embeddings classifier"""
        print(f"{Bcolors.HEADER}=== Training {self.get_model_name()} ==={Bcolors.ENDC}")
        
        # Encode labels
        le = LabelEncoder()
        y = le.fit_transform(labels)
        print(f"{Bcolors.OKGREEN}Classes: {len(le.classes_)}{Bcolors.ENDC}")
        
        # Load sentence transformer model
        params = self.get_default_params()
        print(f"{Bcolors.OKBLUE}Loading sentence transformer: {params['model_name']}...{Bcolors.ENDC}")
        model = SentenceTransformer(params['model_name'])
        
        # Split data
        X_train_docs, X_test_docs, y_train, y_test = train_test_split(
            documents, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Generate embeddings for training set
        print(f"{Bcolors.OKBLUE}Generating embeddings for training set...{Bcolors.ENDC}")
        train_embeddings = model.encode(X_train_docs, batch_size=params['batch_size'], show_progress_bar=True)
        
        # Calculate centroids for each class
        print(f"{Bcolors.OKBLUE}Calculating class centroids...{Bcolors.ENDC}")
        centroids = {}
        class_embeddings = defaultdict(list)
        
        # Group embeddings by class
        for embedding, label in zip(train_embeddings, y_train):
            class_embeddings[label].append(embedding)
        
        # Calculate centroid for each class
        for class_label, embeddings_list in class_embeddings.items():
            centroids[class_label] = np.mean(embeddings_list, axis=0)
            print(f"Class {le.classes_[class_label]}: {len(embeddings_list)} samples")
        
        # Generate embeddings for test set
        print(f"{Bcolors.OKBLUE}Generating embeddings for test set...{Bcolors.ENDC}")
        test_embeddings = model.encode(X_test_docs, batch_size=params['batch_size'], show_progress_bar=True)
        
        # Make predictions using centroid similarity
        print(f"{Bcolors.OKBLUE}Making predictions...{Bcolors.ENDC}")
        y_pred = []
        
        for test_embedding in test_embeddings:
            # Calculate cosine similarity to each centroid
            similarities = {}
            for class_label, centroid in centroids.items():
                # Cosine similarity
                similarity = np.dot(test_embedding, centroid) / (
                    np.linalg.norm(test_embedding) * np.linalg.norm(centroid)
                )
                similarities[class_label] = similarity
            
            # Predict class with highest similarity
            predicted_class = max(similarities.keys(), key=lambda k: similarities[k])
            y_pred.append(predicted_class)
        
        y_pred = np.array(y_pred)
        
        # Evaluate
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"\nComplete classification report:")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))
        
        # Save models
        print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")
        
        # Save centroids and label encoder
        model_data = {
            'centroids': centroids,
            'model_name': params['model_name'],
            'embedding_dim': train_embeddings.shape[1]
        }
        
        with open(self.model_dir / "embeddings_centroids.pkl", 'wb') as f:
            pickle.dump(model_data, f)
        
        joblib.dump(le, self.model_dir / "embeddings_label_encoder.pkl")
        
        return accuracy

    def load_model(self):
        try:
            with open(self.model_dir / "embeddings_centroids.pkl", 'rb') as f:
                self.model_data = pickle.load(f)
            self.label_encoder = joblib.load(self.model_dir / "embeddings_label_encoder.pkl")
            self.embedding_model = SentenceTransformer(self.model_data['model_name'])
            return True
        except (FileNotFoundError, ImportError):
            return False

    def predict(self, X_test):
        test_embeddings = self.embedding_model.encode(X_test, batch_size=32, show_progress_bar=False)
        centroids = self.model_data['centroids']
        y_pred = []
        for emb in test_embeddings:
            similarities = {}
            for label, centroid in centroids.items():
                sim = np.dot(emb, centroid) / (np.linalg.norm(emb) * np.linalg.norm(centroid))
                similarities[label] = sim
            y_pred.append(max(similarities, key=similarities.get))
        return self.label_encoder.inverse_transform(y_pred)


def train_embeddings_model(documents, labels):
    """Convenience function for backward compatibility"""
    strategy = EmbeddingsTrainingStrategy()
    return strategy.train(documents, labels)