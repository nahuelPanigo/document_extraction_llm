"""
SVM training strategy for text classification.
Accepts model_dir as parameter for flexibility across modules.
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
from utils.colors.colors_terminal import Bcolors
from utils.ml_strategies.training_strategy import TrainingStrategy

# Spanish stop words list for academic text
SPANISH_STOP_WORDS = [
    'a', 'al', 'algo', 'algunas', 'algunos', 'ante', 'antes', 'como', 'con', 'contra', 'cual', 'cuando', 'de', 'del', 'desde', 'donde', 'durante', 'e', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 'erais', 'eran', 'eras', 'eres', 'es', 'esa', 'esas', 'ese', 'eso', 'esos', 'esta', 'estaba', 'estabais', 'estaban', 'estabas', 'estad', 'estada', 'estadas', 'estado', 'estados', 'estamos', 'estando', 'estar', 'estaremos', 'estará', 'estarán', 'estarás', 'estaré', 'estaréis', 'estaría', 'estaríais', 'estaríamos', 'estarían', 'estarías', 'estas', 'este', 'estemos', 'esto', 'estos', 'estoy', 'estuve', 'estuviera', 'estuvierais', 'estuvieran', 'estuvieras', 'estuvieron', 'estuviese', 'estuvieseis', 'estuviesen', 'estuvieses', 'estuvimos', 'estuviste', 'estuvisteis', 'estuvo', 'está', 'estábamos', 'estáis', 'están', 'estás', 'esté', 'estéis', 'estén', 'estés', 'fue', 'fuera', 'fuerais', 'fueran', 'fueras', 'fueron', 'fuese', 'fueseis', 'fuesen', 'fueses', 'fui', 'fuimos', 'fuiste', 'fuisteis', 'ha', 'habida', 'habidas', 'habido', 'habidos', 'habiendo', 'habremos', 'habrá', 'habrán', 'habrás', 'habré', 'habréis', 'habría', 'habríais', 'habríamos', 'habrían', 'habrías', 'habéis', 'había', 'habíais', 'habíamos', 'habían', 'habías', 'han', 'has', 'hasta', 'hay', 'haya', 'hayamos', 'hayan', 'hayas', 'hayáis', 'he', 'hemos', 'hube', 'hubiera', 'hubierais', 'hubieran', 'hubieras', 'hubieron', 'hubiese', 'hubieseis', 'hubiesen', 'hubieses', 'hubimos', 'hubiste', 'hubisteis', 'hubo', 'la', 'las', 'le', 'les', 'lo', 'los', 'me', 'mi', 'mis', 'mucho', 'muchos', 'muy', 'más', 'mí', 'mía', 'mías', 'mío', 'míos', 'nada', 'ni', 'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'o', 'os', 'otra', 'otras', 'otro', 'otros', 'para', 'pero', 'poco', 'por', 'porque', 'que', 'quien', 'quienes', 'qué', 'se', 'sea', 'seamos', 'sean', 'seas', 'sentid', 'sentida', 'sentidas', 'sentido', 'sentidos', 'seremos', 'será', 'serán', 'serás', 'seré', 'seréis', 'sería', 'seríais', 'seríamos', 'serían', 'serías', 'seáis', 'sido', 'siendo', 'sin', 'sobre', 'sois', 'somos', 'son', 'soy', 'su', 'sus', 'suya', 'suyas', 'suyo', 'suyos', 'sí', 'también', 'tanto', 'te', 'tendremos', 'tendrá', 'tendrán', 'tendrás', 'tendré', 'tendréis', 'tendría', 'tendríais', 'tendríamos', 'tendrían', 'tendrías', 'tened', 'tenemos', 'tenga', 'tengamos', 'tengan', 'tengas', 'tengo', 'tengáis', 'tenida', 'tenidas', 'tenido', 'tenidos', 'teniendo', 'tenéis', 'tenía', 'teníais', 'teníamos', 'tenían', 'tenías', 'ti', 'tiene', 'tienen', 'tienes', 'todo', 'todos', 'tu', 'tus', 'tuve', 'tuviera', 'tuvierais', 'tuvieran', 'tuvieras', 'tuvieron', 'tuviese', 'tuvieseis', 'tuviesen', 'tuvieses', 'tuvimos', 'tuviste', 'tuvisteis', 'tuvo', 'tuya', 'tuyas', 'tuyo', 'tuyos', 'tú', 'un', 'una', 'uno', 'unos', 'vosotras', 'vosotros', 'vuestra', 'vuestras', 'vuestro', 'vuestros', 'y', 'ya', 'yo', 'él', 'éramos'
]


class SVMTrainingStrategy(TrainingStrategy):
    """SVM training strategy with configurable kernel"""

    def __init__(self, model_dir=None, use_grid_search=False, kernel='linear'):
        from constants import SUBJECT_MODEL_FOLDERS
        # Use specific folder for each kernel type
        if model_dir is not None:
            self.model_dir = Path(model_dir)
        else:
            if kernel == 'linear':
                folder_key = "svm_linear"
            elif kernel == 'rbf':
                folder_key = "svm_rbf"
            else:
                folder_key = "svm"
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
        params = {
            'kernel': self.kernel,
            'class_weight': 'balanced',
            'random_state': 42,
            'max_features': 60000,
            'ngram_range': (1, 3),
            'min_df': 2,
            'max_df': 0.8,
            'analyzer': 'word',
            'stop_words': SPANISH_STOP_WORDS
        }
        if self.kernel == 'linear':
            params['C'] = 1.0
        elif self.kernel == 'rbf':
            params['C'] = 1.0
            params['gamma'] = 'scale'
        return params

    def train(self, documents, labels):
        """Train SVM classifier"""
        print(f"{Bcolors.HEADER}=== Training {self.get_model_name()} ==={Bcolors.ENDC}")

        le = LabelEncoder()
        y = le.fit_transform(labels)
        print(f"{Bcolors.OKGREEN}Classes: {len(le.classes_)}{Bcolors.ENDC}")

        params = self.get_default_params()
        vectorizer = TfidfVectorizer(
            max_features=params['max_features'],
            ngram_range=params['ngram_range'],
            min_df=params['min_df'],
            max_df=params['max_df'],
            analyzer=params['analyzer'],
            stop_words=params['stop_words'],
            sublinear_tf=True
        )

        X = vectorizer.fit_transform(documents)
        print(f"Feature matrix: {X.shape}")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"{Bcolors.OKBLUE}Training...{Bcolors.ENDC}")

        if self.use_grid_search:
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
            svm_params = {
                'kernel': params['kernel'],
                'C': params['C'],
                'class_weight': params['class_weight'],
                'random_state': params['random_state']
            }
            if params['kernel'] == 'rbf' and 'gamma' in params:
                svm_params['gamma'] = params['gamma']
            clf = SVC(**svm_params)
            clf.fit(X_train, y_train)
            best_clf = clf

        y_pred = best_clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"\nComplete classification report:")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

        print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")
        joblib.dump(best_clf, self.model_dir / "svm_classifier.pkl")
        joblib.dump(vectorizer, self.model_dir / "svm_vectorizer.pkl")
        joblib.dump(le, self.model_dir / "svm_label_encoder.pkl")

        return accuracy

    def load_model(self):
        try:
            self.clf = joblib.load(self.model_dir / 'svm_classifier.pkl')
            self.vectorizer = joblib.load(self.model_dir / 'svm_vectorizer.pkl')
            self.label_encoder = joblib.load(self.model_dir / 'svm_label_encoder.pkl')
            return True
        except FileNotFoundError:
            return False

    def predict(self, X_test):
        X_features = self.vectorizer.transform(X_test)
        y_pred_encoded = self.clf.predict(X_features)
        return self.label_encoder.inverse_transform(y_pred_encoded)


def train_svm_model(documents, labels, use_grid_search=False, kernel='linear'):
    """Convenience function for backward compatibility"""
    strategy = SVMTrainingStrategy(use_grid_search=use_grid_search, kernel=kernel)
    return strategy.train(documents, labels)
