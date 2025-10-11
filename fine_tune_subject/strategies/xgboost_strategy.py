"""
XGBoost training strategy for subject classification
XGBoost with class weighting for imbalanced datasets
"""
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
import joblib
import numpy as np
from pathlib import Path
from constants import SUBJECT_MODEL_FOLDERS
from utils.colors.colors_terminal import Bcolors
from fine_tune_subject.utils.models.training_strategy import TrainingStrategy


class XGBoostTrainingStrategy(TrainingStrategy):
    """XGBoost training strategy"""
    
    def __init__(self):
        self.model_dir = SUBJECT_MODEL_FOLDERS["xgboost"]
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
    def get_model_name(self):
        return "XGBoost"
    
    def get_model_files(self):
        return [
            str(self.model_dir / "xgboost_classifier.pkl"),
            str(self.model_dir / "xgboost_vectorizer.pkl"),
            str(self.model_dir / "xgboost_label_encoder.pkl")
        ]
    
    def get_default_params(self):
        return {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'random_state': 42,
            'n_jobs': -1,
            'max_features': 15000,
            'ngram_range': (1, 2),
            'min_df': 2,
            'max_df': 0.8
        }
    
    def train(self, documents, labels):
        """Train XGBoost classifier"""
        print(f"{Bcolors.HEADER}=== Training {self.get_model_name()} ==={Bcolors.ENDC}")
        
        # Encode labels
        le = LabelEncoder()
        y = le.fit_transform(labels)
        print(f"{Bcolors.OKGREEN}Classes: {len(le.classes_)}{Bcolors.ENDC}")
        
        # Calculate class weights for imbalanced dataset
        class_weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
        sample_weights = np.array([class_weights[label] for label in y])
        
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
        
        # Get sample weights for training set
        train_weights = np.array([class_weights[label] for label in y_train])
        
        # Train
        print(f"{Bcolors.OKBLUE}Training with class weighting...{Bcolors.ENDC}")
        clf = xgb.XGBClassifier(
            n_estimators=params['n_estimators'],
            max_depth=params['max_depth'],
            learning_rate=params['learning_rate'],
            random_state=params['random_state'],
            n_jobs=params['n_jobs'],
            eval_metric='mlogloss'
        )
        
        # Train with sample weights
        clf.fit(X_train, y_train, sample_weight=train_weights)
        
        # Evaluate
        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"\nComplete classification report:")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))
        
        # Show feature importance (top 10)
        feature_names = vectorizer.get_feature_names_out()
        importances = clf.feature_importances_
        top_features = np.argsort(importances)[-10:][::-1]
        
        print(f"\n{Bcolors.OKBLUE}Top 10 Most Important Features:{Bcolors.ENDC}")
        for i, feat_idx in enumerate(top_features):
            print(f"{i+1:2d}. {feature_names[feat_idx]}: {importances[feat_idx]:.4f}")
        
        # Save models
        print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")
        joblib.dump(clf, self.model_dir / "xgboost_classifier.pkl")
        joblib.dump(vectorizer, self.model_dir / "xgboost_vectorizer.pkl")
        joblib.dump(le, self.model_dir / "xgboost_label_encoder.pkl")
        
        return accuracy


def train_xgboost_model(documents, labels):
    """Convenience function for backward compatibility"""
    strategy = XGBoostTrainingStrategy()
    return strategy.train(documents, labels)