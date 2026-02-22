"""
Embeddings + KNN training strategy for text classification.
Uses sentence transformers with KNN classifier.
Accepts model_dir as parameter for flexibility across modules.
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
from utils.colors.colors_terminal import Bcolors
from utils.ml_strategies.training_strategy import TrainingStrategy


class EmbeddingsKNNTrainingStrategy(TrainingStrategy):
    """Embeddings + KNN training strategy"""

    def __init__(self, model_dir=None):
        if model_dir is not None:
            self.model_dir = Path(model_dir)
        else:
            from constants import SUBJECT_MODEL_FOLDERS
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

        le = LabelEncoder()
        y = le.fit_transform(labels)
        print(f"{Bcolors.OKGREEN}Classes: {len(le.classes_)}{Bcolors.ENDC}")

        params = self.get_default_params()
        print(f"{Bcolors.OKBLUE}Loading sentence transformer: {params['model_name']}...{Bcolors.ENDC}")
        embedding_model = SentenceTransformer(params['model_name'])

        print(f"{Bcolors.OKBLUE}Generating embeddings...{Bcolors.ENDC}")
        embeddings = embedding_model.encode(documents, batch_size=params['batch_size'], show_progress_bar=True)

        print(f"Embeddings shape: {embeddings.shape}")

        X_train, X_test, y_train, y_test = train_test_split(
            embeddings, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"{Bcolors.OKBLUE}Training KNN classifier...{Bcolors.ENDC}")
        knn = KNeighborsClassifier(
            n_neighbors=params['n_neighbors'],
            weights=params['weights'],
            metric=params['metric'],
            n_jobs=-1
        )

        knn.fit(X_train, y_train)

        print(f"{Bcolors.OKBLUE}Making predictions...{Bcolors.ENDC}")
        y_pred = knn.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"\nComplete classification report:")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

        print(f"\n{Bcolors.OKBLUE}KNN Parameters:{Bcolors.ENDC}")
        print(f"  k (neighbors): {params['n_neighbors']}")
        print(f"  Weights: {params['weights']}")
        print(f"  Metric: {params['metric']}")
        print(f"  Training samples: {X_train.shape[0]}")
        print(f"  Feature dimension: {X_train.shape[1]}")

        print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")

        joblib.dump(knn, self.model_dir / "embeddings_knn_classifier.pkl")
        joblib.dump(le, self.model_dir / "embeddings_knn_label_encoder.pkl")

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

    def load_model(self):
        try:
            self.classifier = joblib.load(self.model_dir / "embeddings_knn_classifier.pkl")
            self.label_encoder = joblib.load(self.model_dir / "embeddings_knn_label_encoder.pkl")
            with open(self.model_dir / "embeddings_knn_model_info.pkl", 'rb') as f:
                self.model_info = pickle.load(f)
            self.transformer_model = SentenceTransformer(self.model_info['embedding_model_name'])
            return True
        except (FileNotFoundError, ImportError):
            return False

    def predict(self, X_test):
        test_embeddings = self.transformer_model.encode(X_test, batch_size=32, normalize_embeddings=True)
        y_pred_encoded = self.classifier.predict(test_embeddings)
        return self.label_encoder.inverse_transform(y_pred_encoded)


def train_embeddings_knn_model(documents, labels):
    """Convenience function for backward compatibility"""
    strategy = EmbeddingsKNNTrainingStrategy()
    return strategy.train(documents, labels)
