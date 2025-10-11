"""
Random Forest training strategy for subject classification
"""
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import joblib
import numpy as np
from pathlib import Path
from constants import SUBJECT_MODEL_FOLDERS
from utils.colors.colors_terminal import Bcolors
from fine_tune_subject.utils.models.training_strategy import TrainingStrategy


class RandomForestTrainingStrategy(TrainingStrategy):
    """Random Forest training strategy"""
    
    def __init__(self):
        self.model_dir = SUBJECT_MODEL_FOLDERS["random_forest"]
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
    def get_model_name(self):
        return "Random Forest"
    
    def get_model_files(self):
        return [
            str(self.model_dir / "subject_classifier.pkl"),
            str(self.model_dir / "vectorizer.pkl"), 
            str(self.model_dir / "label_encoder.pkl")
        ]
    
    def get_default_params(self):
        return {
            'n_estimators': 100,
            'random_state': 42,
            'n_jobs': -1,
            'max_features': 15000,
            'ngram_range': (1, 2),
            'min_df': 2,
            'max_df': 0.8
        }
    
    def train(self, documents, labels):
        """Train Random Forest classifier"""
        print(f"{Bcolors.HEADER}=== Training {self.get_model_name()} ==={Bcolors.ENDC}")
        
        # Encode labels
        le = LabelEncoder()
        y = le.fit_transform(labels)
        print(f"{Bcolors.OKGREEN}Classes: {len(le.classes_)}{Bcolors.ENDC}")
        
        # Create features
        params = self.get_default_params()
        vectorizer = TfidfVectorizer(
            max_features=params['max_features'],
            ngram_range=params['ngram_range'],
            min_df=params['min_df'],
            max_df=params['max_df'],
            stop_words=None
        )
        
        X = vectorizer.fit_transform(documents)
        print(f"Feature matrix: {X.shape}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train
        print(f"{Bcolors.OKBLUE}Training...{Bcolors.ENDC}")
        clf = RandomForestClassifier(
            n_estimators=params['n_estimators'],
            random_state=params['random_state'],
            n_jobs=params['n_jobs']
        )
        clf.fit(X_train, y_train)
        
        # Evaluate
        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"\nComplete classification report (all classes):")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))
        
        # Save models
        print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")
        joblib.dump(clf, self.model_dir / "subject_classifier.pkl")
        joblib.dump(vectorizer, self.model_dir / "vectorizer.pkl")
        joblib.dump(le, self.model_dir / "label_encoder.pkl")
        
        return accuracy


def train_random_forest_model(documents, labels):
    """Convenience function for backward compatibility"""
    strategy = RandomForestTrainingStrategy()
    return strategy.train(documents, labels)