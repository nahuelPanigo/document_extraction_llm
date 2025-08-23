"""
Simple Subject Classification Training
Uses: TXT files + CSV subjects only
"""
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from constants import CSV_FOLDER, CSV_SEDICI_FILTERED, TXT_FOLDER
import pandas as pd
import numpy as np
import random
import os
import joblib
from collections import Counter
from utils.colors.colors_terminal import Bcolors

def preprocess_text(text):
    """Simple text preprocessing"""
    if not text:
        return ""
    return " ".join(text.split()).lower()

def load_csv_subjects():
    """Load subject mapping from CSV"""
    csv_path = CSV_FOLDER / CSV_SEDICI_FILTERED
    df = pd.read_csv(csv_path)
    
    subject_mapping = {}
    for _, row in df.iterrows():
        doc_id = str(row['id'])
        subject = row['sedici.subject.materias']
        
        if pd.isna(subject) or not subject:
            continue
            
        subject_mapping[doc_id] = subject
    
    print(f"{Bcolors.OKGREEN}CSV loaded: {len(subject_mapping)} documents with subjects{Bcolors.ENDC}")
    return subject_mapping

def create_dataset(subject_mapping, min_frequency=5):
    """Create dataset from txt files + CSV subjects"""
    
    if not TXT_FOLDER.exists():
        print(f"{Bcolors.FAIL}TXT_FOLDER not found: {TXT_FOLDER}{Bcolors.ENDC}")
        return [], [], []
    
    txt_files = [f for f in os.listdir(TXT_FOLDER) if f.endswith('.txt')]
    print(f"{Bcolors.OKBLUE}Found {len(txt_files)} txt files{Bcolors.ENDC}")
    
    # Get available subjects for files we have
    available_subjects = []
    for txt_file in txt_files:
        doc_id = txt_file.replace('.txt', '')
        if doc_id in subject_mapping:
            available_subjects.append(subject_mapping[doc_id])
    
    # Filter by frequency
    subject_counts = Counter(available_subjects)
    frequent_subjects = {subject for subject, count in subject_counts.items() 
                        if count >= min_frequency}
    
    print(f"{Bcolors.OKBLUE}Subjects with >= {min_frequency} documents: {len(frequent_subjects)}{Bcolors.ENDC}")
    
    # Create dataset
    documents = []
    labels = []
    document_ids = []
    
    for txt_file in txt_files:
        doc_id = txt_file.replace('.txt', '')
        
        if doc_id not in subject_mapping:
            continue
            
        subject = subject_mapping[doc_id]
        if subject not in frequent_subjects:
            continue
        
        # Read text file
        txt_path = TXT_FOLDER / txt_file
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
                
            processed_text = preprocess_text(text_content)
            
            if processed_text:
                documents.append(processed_text)
                labels.append(subject)
                document_ids.append(doc_id)
                
        except Exception as e:
            print(f"Error reading {txt_file}: {e}")
            continue
    
    print(f"{Bcolors.OKGREEN}Dataset created: {len(documents)} documents, {len(set(labels))} subjects{Bcolors.ENDC}")
    
    # Show top subjects
    label_counts = Counter(labels)
    print("Top subjects:")
    for subject, count in label_counts.most_common(10):
        print(f"  {subject}: {count}")
    
    return documents, labels, document_ids

def train_classifier(documents, labels):
    """Train the classifier"""
    
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(labels)
    print(f"{Bcolors.OKGREEN}Classes: {len(le.classes_)}{Bcolors.ENDC}")
    
    # Create features
    vectorizer = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.8,
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
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n{Bcolors.HEADER}=== Results ==={Bcolors.ENDC}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"\nTop 10 subjects report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))
    
    # Save models
    print(f"\n{Bcolors.OKGREEN}Saving models...{Bcolors.ENDC}")
    joblib.dump(clf, 'subject_classifier.pkl')
    joblib.dump(vectorizer, 'vectorizer.pkl')
    joblib.dump(le, 'label_encoder.pkl')
    
    return accuracy

if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    
    print(f"{Bcolors.HEADER}=== Subject Classification Training ==={Bcolors.ENDC}")
    
    # Load data
    subject_mapping = load_csv_subjects()
    documents, labels, document_ids = create_dataset(subject_mapping)
    
    if len(documents) == 0:
        print(f"{Bcolors.FAIL}No documents found!{Bcolors.ENDC}")
        exit(1)
    
    # Train
    accuracy = train_classifier(documents, labels)
    
    print(f"\n{Bcolors.OKGREEN}Training completed! Accuracy: {accuracy:.4f}{Bcolors.ENDC}")