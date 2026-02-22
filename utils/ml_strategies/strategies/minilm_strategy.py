"""
all-MiniLM-L6-v2 / LaBSE training strategy for text classification.
Dedicated strategy using SVM classification with optimized parameters.
Accepts model_dir as parameter for flexibility across modules.
"""
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
import numpy as np
import joblib
import pickle
from pathlib import Path
from utils.colors.colors_terminal import Bcolors
from utils.ml_strategies.training_strategy import TrainingStrategy


class MiniLMTrainingStrategy(TrainingStrategy):
    """all-MiniLM-L6-v2 / LaBSE training strategy using SVM classification"""

    def __init__(self, model_dir=None):
        if model_dir is not None:
            self.model_dir = Path(model_dir)
        else:
            from constants import SUBJECT_MODEL_FOLDERS
            self.model_dir = SUBJECT_MODEL_FOLDERS.get("minilm", Path("models/minilm"))
        self.model_name = "sentence-transformers/LaBSE"
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def get_model_name(self):
        return self.model_name

    def get_model_files(self):
        return [
            str(self.model_dir / "minilm_classifier.pkl"),
            str(self.model_dir / "minilm_label_encoder.pkl"),
            str(self.model_dir / "minilm_model_info.pkl")
        ]

    def get_default_params(self):
        return {
            'model_name': self.model_name,
            'batch_size': 32,
            'classifier': 'svm',
            'tune_hyperparams': True,
            'C': 1.0,
            'kernel': 'rbf',
            'class_weight': 'balanced'
        }

    def train(self, documents, labels):
        """Train all-MiniLM-L6-v2 SVM classifier"""
        print(f"{Bcolors.HEADER}=== Training {self.get_model_name()} ==={Bcolors.ENDC}")

        le = LabelEncoder()
        y = le.fit_transform(labels)
        print(f"{Bcolors.OKGREEN}Classes: {len(le.classes_)}{Bcolors.ENDC}")

        params = self.get_default_params()
        print(f"{Bcolors.OKBLUE}Loading sentence transformer: {params['model_name']}...{Bcolors.ENDC}")
        model = SentenceTransformer(params['model_name'])

        X_train_docs, X_test_docs, y_train, y_test = train_test_split(
            documents, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"{Bcolors.OKBLUE}Generating embeddings for training set ({len(X_train_docs)} samples)...{Bcolors.ENDC}")
        train_embeddings = model.encode(
            X_train_docs,
            batch_size=params['batch_size'],
            show_progress_bar=True,
            normalize_embeddings=True
        )

        print(f"{Bcolors.OKBLUE}Generating embeddings for test set ({len(X_test_docs)} samples)...{Bcolors.ENDC}")
        test_embeddings = model.encode(
            X_test_docs,
            batch_size=params['batch_size'],
            show_progress_bar=True,
            normalize_embeddings=True
        )

        if params.get('tune_hyperparams', True):
            print(f"{Bcolors.OKBLUE}Tuning SVM hyperparameters with GridSearchCV...{Bcolors.ENDC}")

            param_grid = {
                'C': [0.1, 1, 10, 100],
                'kernel': ['rbf', 'linear'],
                'gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1]
            }

            base_svm = SVC(class_weight='balanced', random_state=42)

            grid_search = GridSearchCV(
                base_svm,
                param_grid,
                cv=3,
                scoring='accuracy',
                n_jobs=-1,
                verbose=1
            )

            print(f"{Bcolors.OKBLUE}Training with {len(train_embeddings)} samples...{Bcolors.ENDC}")
            grid_search.fit(train_embeddings, y_train)

            best_params = grid_search.best_params_
            classifier = grid_search.best_estimator_

            print(f"{Bcolors.OKGREEN}Best parameters found:{Bcolors.ENDC}")
            print(f"  C={best_params['C']}, kernel={best_params['kernel']}, gamma={best_params['gamma']}")
            print(f"  CV Score: {grid_search.best_score_:.4f}")

        else:
            print(f"{Bcolors.OKBLUE}Training SVM classifier...{Bcolors.ENDC}")
            classifier = SVC(
                C=params['C'],
                kernel=params['kernel'],
                class_weight=params['class_weight'],
                random_state=42
            )

            classifier.fit(train_embeddings, y_train)
            best_params = {
                'C': params['C'],
                'kernel': params['kernel'],
                'class_weight': params['class_weight']
            }

        print(f"{Bcolors.OKBLUE}Making predictions...{Bcolors.ENDC}")
        y_pred = classifier.predict(test_embeddings)

        accuracy = accuracy_score(y_test, y_pred)

        print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Model: {params['model_name']}")
        print(f"Best SVM parameters: C={best_params.get('C', 'N/A')}, kernel={best_params.get('kernel', 'N/A')}")
        print(f"\nComplete classification report:")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

        print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")

        joblib.dump(classifier, self.model_dir / "minilm_classifier.pkl")
        joblib.dump(le, self.model_dir / "minilm_label_encoder.pkl")

        model_info = {
            'model_name': params['model_name'],
            'embedding_dim': train_embeddings.shape[1],
            'classifier_type': 'svm',
            'C': best_params.get('C', params.get('C')),
            'kernel': best_params.get('kernel', params.get('kernel')),
            'gamma': best_params.get('gamma', 'scale'),
            'accuracy': accuracy,
            'n_classes': len(le.classes_),
            'classes': le.classes_.tolist(),
            'training_samples': len(X_train_docs),
            'test_samples': len(X_test_docs),
            'tuned': params.get('tune_hyperparams', True),
            'best_params': best_params
        }

        with open(self.model_dir / "minilm_model_info.pkl", 'wb') as f:
            pickle.dump(model_info, f)

        print(f"Models saved to: {self.model_dir}")
        print(f"Files: {', '.join([Path(f).name for f in self.get_model_files()])}")

        return accuracy

    def load_model(self):
        try:
            self.classifier = joblib.load(self.model_dir / "minilm_classifier.pkl")
            self.label_encoder = joblib.load(self.model_dir / "minilm_label_encoder.pkl")
            with open(self.model_dir / "minilm_model_info.pkl", 'rb') as f:
                self.model_info = pickle.load(f)
            self.transformer_model = SentenceTransformer(self.model_info['model_name'])
            return True
        except (FileNotFoundError, ImportError):
            return False

    def predict(self, X_test):
        test_embeddings = self.transformer_model.encode(X_test, batch_size=32, normalize_embeddings=True)
        y_pred_encoded = self.classifier.predict(test_embeddings)
        return self.label_encoder.inverse_transform(y_pred_encoded)


def train_minilm_model(documents, labels):
    """Convenience function for backward compatibility"""
    strategy = MiniLMTrainingStrategy()
    return strategy.train(documents, labels)
