"""
SVM training strategy for subject classification
SVM is generally better than Random Forest for text classification
"""
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
import joblib
import numpy as np
from pathlib import Path
from constants import SUBJECT_MODEL_FOLDERS
from utils.colors.colors_terminal import Bcolors
from fine_tune_subject.utils.models.training_strategy import TrainingStrategy

# Spanish stop words list for academic text
SPANISH_STOP_WORDS = [
    'a', 'al', 'algo', 'algunas', 'algunos', 'ante', 'antes', 'como', 'con', 'contra', 'cual', 'cuando', 'de', 'del', 'desde', 'donde', 'durante', 'e', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 'erais', 'eran', 'eras', 'eres', 'es', 'esa', 'esas', 'ese', 'eso', 'esos', 'esta', 'estaba', 'estabais', 'estaban', 'estabas', 'estad', 'estada', 'estadas', 'estado', 'estados', 'estamos', 'estando', 'estar', 'estaremos', 'estará', 'estarán', 'estarás', 'estaré', 'estaréis', 'estaría', 'estaríais', 'estaríamos', 'estarían', 'estarías', 'estas', 'este', 'estemos', 'esto', 'estos', 'estoy', 'estuve', 'estuviera', 'estuvierais', 'estuvieran', 'estuvieras', 'estuvieron', 'estuviese', 'estuvieseis', 'estuviesen', 'estuvieses', 'estuvimos', 'estuviste', 'estuvisteis', 'estuvo', 'está', 'estábamos', 'estáis', 'están', 'estás', 'esté', 'estéis', 'estén', 'estés', 'fue', 'fuera', 'fuerais', 'fueran', 'fueras', 'fueron', 'fuese', 'fueseis', 'fuesen', 'fueses', 'fui', 'fuimos', 'fuiste', 'fuisteis', 'ha', 'habida', 'habidas', 'habido', 'habidos', 'habiendo', 'habremos', 'habrá', 'habrán', 'habrás', 'habré', 'habréis', 'habría', 'habríais', 'habríamos', 'habrían', 'habrías', 'habéis', 'había', 'habíais', 'habíamos', 'habían', 'habías', 'han', 'has', 'hasta', 'hay', 'haya', 'hayamos', 'hayan', 'hayas', 'hayáis', 'he', 'hemos', 'hube', 'hubiera', 'hubierais', 'hubieran', 'hubieras', 'hubieron', 'hubiese', 'hubieseis', 'hubiesen', 'hubieses', 'hubimos', 'hubiste', 'hubisteis', 'hubo', 'la', 'las', 'le', 'les', 'lo', 'los', 'me', 'mi', 'mis', 'mucho', 'muchos', 'muy', 'más', 'mí', 'mía', 'mías', 'mío', 'míos', 'nada', 'ni', 'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'o', 'os', 'otra', 'otras', 'otro', 'otros', 'para', 'pero', 'poco', 'por', 'porque', 'que', 'quien', 'quienes', 'qué', 'se', 'sea', 'seamos', 'sean', 'seas', 'sentid', 'sentida', 'sentidas', 'sentido', 'sentidos', 'seremos', 'será', 'serán', 'serás', 'seré', 'seréis', 'sería', 'seríais', 'seríamos', 'serían', 'serías', 'seáis', 'sido', 'siendo', 'sin', 'sobre', 'sois', 'somos', 'son', 'soy', 'su', 'sus', 'suya', 'suyas', 'suyo', 'suyos', 'sí', 'también', 'tanto', 'te', 'tendremos', 'tendrá', 'tendrán', 'tendrás', 'tendré', 'tendréis', 'tendría', 'tendríais', 'tendríamos', 'tendrían', 'tendrías', 'tened', 'tenemos', 'tenga', 'tengamos', 'tengan', 'tengas', 'tengo', 'tengáis', 'tenida', 'tenidas', 'tenido', 'tenidos', 'teniendo', 'tenéis', 'tenía', 'teníais', 'teníamos', 'tenían', 'tenías', 'ti', 'tiene', 'tienen', 'tienes', 'todo', 'todos', 'tu', 'tus', 'tuve', 'tuviera', 'tuvierais', 'tuvieran', 'tuvieras', 'tuvieron', 'tuviese', 'tuvieseis', 'tuviesen', 'tuvieses', 'tuvimos', 'tuviste', 'tuvisteis', 'tuvo', 'tuya', 'tuyas', 'tuyo', 'tuyos', 'tú', 'un', 'una', 'uno', 'unos', 'vosotras', 'vosotros', 'vuestra', 'vuestras', 'vuestro', 'vuestros', 'y', 'ya', 'yo', 'él', 'éramos'
]


class SVMTrainingStrategy(TrainingStrategy):
    """SVM training strategy with configurable kernel"""
    
    def __init__(self, use_grid_search=False, kernel='linear'):
        # Use specific folder for each kernel type
        if kernel == 'linear':
            folder_key = "svm_linear"
        elif kernel == 'rbf':
            folder_key = "svm_rbf"
        else:
            folder_key = "svm"  # fallback for other kernels
            
        self.model_dir = SUBJECT_MODEL_FOLDERS[folder_key]
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.use_grid_search = use_grid_search
        self.kernel = kernel
        
    def get_model_name(self):
        if self.use_grid_search:
            return "SVM (Grid Search)"
        return f"SVM ({self.kernel.title()})"
    
    def get_model_files(self):
        return [
            str(self.model_dir / "svm_classifier.pkl"),
            str(self.model_dir / "svm_vectorizer.pkl"), 
            str(self.model_dir / "svm_label_encoder.pkl")
        ]
    
    def get_default_params(self):
        # Base parameters
        params = {
            'kernel': self.kernel,
            'class_weight': 'balanced',
            'random_state': 42,
            # Enhanced TF-IDF parameters for better science class separation
            'max_features': 60000,        # More vocabulary for technical terms
            'ngram_range': (1, 3),        # Include 4-grams for domain-specific phrases
            'min_df': 2,                  # Keep minimum document frequency
            'max_df': 0.8,                # Lower max_df to capture more specific terms
            'analyzer': 'word',           # Word-level analysis for academic text
            'stop_words': SPANISH_STOP_WORDS   # Custom Spanish stop words list
        }
        
        # Kernel-specific parameters
        if self.kernel == 'linear':
            params['C'] = 1.0
        elif self.kernel == 'rbf':
            params['C'] = 1.0
            params['gamma'] = 'scale'  # Good default for RBF kernel
        
        return params
    
    def train(self, documents, labels):
        """Train SVM classifier"""
        print(f"{Bcolors.HEADER}=== Training {self.get_model_name()} ==={Bcolors.ENDC}")
        
        # Encode labels
        le = LabelEncoder()
        y = le.fit_transform(labels)
        print(f"{Bcolors.OKGREEN}Classes: {len(le.classes_)}{Bcolors.ENDC}")
        
        # Create features with enhanced parameters for science class separation
        params = self.get_default_params()
        vectorizer = TfidfVectorizer(
            max_features=params['max_features'],    # 50k features for more vocabulary
            ngram_range=params['ngram_range'],      # 1-4 grams for technical phrases
            min_df=params['min_df'],                # Minimum document frequency
            max_df=params['max_df'],                # Lower max_df for specific terms
            analyzer=params['analyzer'],            # Word-level analysis
            stop_words=params['stop_words'],        # Spanish stop words
            sublinear_tf=True                       # Better for SVM
        )
        
        X = vectorizer.fit_transform(documents)
        print(f"Feature matrix: {X.shape}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train
        print(f"{Bcolors.OKBLUE}Training...{Bcolors.ENDC}")
        
        if self.use_grid_search:
            # Grid search for optimal parameters
            pipeline = Pipeline([
                ('svm', SVC(random_state=params['random_state']))
            ])
            
            param_grid = {
                'svm__C': [0.1, 1, 10],
                'svm__kernel': ['linear', 'rbf'],
                'svm__class_weight': ['balanced', None]
            }
            
            print(f"{Bcolors.WARNING}Running Grid Search (this may take a while)...{Bcolors.ENDC}")
            clf = GridSearchCV(pipeline, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
            clf.fit(X_train, y_train)
            
            print(f"{Bcolors.OKGREEN}Best parameters: {clf.best_params_}{Bcolors.ENDC}")
            best_clf = clf.best_estimator_
        else:
            # Use SVM with specified kernel and parameters
            svm_params = {
                'kernel': params['kernel'],
                'C': params['C'],
                'class_weight': params['class_weight'],
                'random_state': params['random_state']
            }
            
            # Add gamma parameter for RBF kernel
            if params['kernel'] == 'rbf' and 'gamma' in params:
                svm_params['gamma'] = params['gamma']
            
            clf = SVC(**svm_params)
            clf.fit(X_train, y_train)
            best_clf = clf
        
        # Evaluate
        y_pred = best_clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"\nComplete classification report:")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))
        
        # Save models
        print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")
        joblib.dump(best_clf, self.model_dir / "svm_classifier.pkl")
        joblib.dump(vectorizer, self.model_dir / "svm_vectorizer.pkl")
        joblib.dump(le, self.model_dir / "svm_label_encoder.pkl")
        
        return accuracy


def train_svm_model(documents, labels, use_grid_search=False, kernel='linear'):
    """Convenience function for backward compatibility"""
    strategy = SVMTrainingStrategy(use_grid_search, kernel)
    return strategy.train(documents, labels)