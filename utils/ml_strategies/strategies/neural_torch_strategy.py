"""
PyTorch Neural Network training strategy for text classification.
Uses embeddings as input features for a neural network.
Accepts model_dir as parameter for flexibility across modules.
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import numpy as np
import joblib
from pathlib import Path
from utils.colors.colors_terminal import Bcolors
from utils.ml_strategies.training_strategy import TrainingStrategy


class TextClassifier(nn.Module):
    """Neural network for text classification"""

    def __init__(self, input_dim, hidden_dim, num_classes, dropout_rate=0.3):
        super(TextClassifier, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, num_classes)
        self.dropout = nn.Dropout(dropout_rate)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x


class NeuralTorchTrainingStrategy(TrainingStrategy):
    """PyTorch Neural Network training strategy"""

    def __init__(self, model_dir=None):
        if model_dir is not None:
            self.model_dir = Path(model_dir)
        else:
            from constants import SUBJECT_MODEL_FOLDERS
            self.model_dir = SUBJECT_MODEL_FOLDERS["neural"]
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def get_model_name(self):
        return "Neural Network (PyTorch)"

    def get_model_files(self):
        return [
            str(self.model_dir / "neural_torch_classifier.pth"),
            str(self.model_dir / "neural_torch_label_encoder.pkl")
        ]

    def get_default_params(self):
        return {
            'model_name': 'all-MiniLM-L6-v2',
            'batch_size': 32,
            'hidden_dim': 256,
            'dropout_rate': 0.3,
            'learning_rate': 0.001,
            'epochs': 50,
            'patience': 10
        }

    def train(self, documents, labels):
        """Train PyTorch Neural Network classifier"""
        print(f"{Bcolors.HEADER}=== Training {self.get_model_name()} ==={Bcolors.ENDC}")
        print(f"Using device: {self.device}")

        le = LabelEncoder()
        y = le.fit_transform(labels)
        num_classes = len(le.classes_)
        print(f"{Bcolors.OKGREEN}Classes: {num_classes}{Bcolors.ENDC}")

        params = self.get_default_params()
        print(f"{Bcolors.OKBLUE}Loading sentence transformer: {params['model_name']}...{Bcolors.ENDC}")
        embedding_model = SentenceTransformer(params['model_name'])

        print(f"{Bcolors.OKBLUE}Generating embeddings...{Bcolors.ENDC}")
        embeddings = embedding_model.encode(documents, batch_size=params['batch_size'], show_progress_bar=True)

        X_train, X_test, y_train, y_test = train_test_split(
            embeddings, y, test_size=0.2, random_state=42, stratify=y
        )

        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.LongTensor(y_train).to(self.device)
        X_test_tensor = torch.FloatTensor(X_test).to(self.device)
        y_test_tensor = torch.LongTensor(y_test).to(self.device)

        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=params['batch_size'], shuffle=True)

        input_dim = embeddings.shape[1]
        model = TextClassifier(
            input_dim=input_dim,
            hidden_dim=params['hidden_dim'],
            num_classes=num_classes,
            dropout_rate=params['dropout_rate']
        ).to(self.device)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=params['learning_rate'])

        print(f"{Bcolors.OKBLUE}Training neural network...{Bcolors.ENDC}")
        best_val_accuracy = 0
        patience_counter = 0

        for epoch in range(params['epochs']):
            model.train()
            total_loss = 0

            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            model.eval()
            with torch.no_grad():
                val_outputs = model(X_test_tensor)
                val_predictions = torch.argmax(val_outputs, dim=1)
                val_accuracy = accuracy_score(y_test, val_predictions.cpu().numpy())

            avg_loss = total_loss / len(train_loader)

            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{params['epochs']}, Loss: {avg_loss:.4f}, Val Acc: {val_accuracy:.4f}")

            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                patience_counter = 0
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'input_dim': input_dim,
                    'hidden_dim': params['hidden_dim'],
                    'num_classes': num_classes,
                    'dropout_rate': params['dropout_rate'],
                    'embedding_model_name': params['model_name']
                }, self.model_dir / "neural_torch_classifier.pth")
            else:
                patience_counter += 1
                if patience_counter >= params['patience']:
                    print(f"{Bcolors.WARNING}Early stopping at epoch {epoch+1}{Bcolors.ENDC}")
                    break

        checkpoint = torch.load(self.model_dir / "neural_torch_classifier.pth")
        model.load_state_dict(checkpoint['model_state_dict'])

        model.eval()
        with torch.no_grad():
            test_outputs = model(X_test_tensor)
            y_pred = torch.argmax(test_outputs, dim=1).cpu().numpy()

        accuracy = accuracy_score(y_test, y_pred)

        print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
        print(f"Best Validation Accuracy: {best_val_accuracy:.4f}")
        print(f"Final Test Accuracy: {accuracy:.4f}")
        print(f"\nComplete classification report:")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

        print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")
        joblib.dump(le, self.model_dir / "neural_torch_label_encoder.pkl")

        return accuracy

    def load_model(self):
        try:
            checkpoint = torch.load(self.model_dir / "neural_torch_classifier.pth", map_location=self.device)
            self.nn_model = TextClassifier(
                checkpoint['input_dim'], checkpoint['hidden_dim'],
                checkpoint['num_classes'], checkpoint['dropout_rate']
            ).to(self.device)
            self.nn_model.load_state_dict(checkpoint['model_state_dict'])
            self.nn_model.eval()
            self.label_encoder = joblib.load(self.model_dir / "neural_torch_label_encoder.pkl")
            self.transformer_model = SentenceTransformer(checkpoint['embedding_model_name'])
            return True
        except (FileNotFoundError, ImportError):
            return False

    def predict(self, X_test):
        test_embeddings = self.transformer_model.encode(X_test, batch_size=32, normalize_embeddings=True)
        X_tensor = torch.FloatTensor(test_embeddings).to(self.device)
        with torch.no_grad():
            outputs = self.nn_model(X_tensor)
            y_pred_encoded = torch.argmax(outputs, dim=1).cpu().numpy()
        return self.label_encoder.inverse_transform(y_pred_encoded)


def train_neural_torch_model(documents, labels):
    """Convenience function for backward compatibility"""
    strategy = NeuralTorchTrainingStrategy()
    return strategy.train(documents, labels)
