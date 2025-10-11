"""
Shared dataset loading and creation functions
Centralized to eliminate duplication across all main training scripts
"""
import pandas as pd
import random
import os
from collections import Counter
from constants import CSV_FOLDER, CSV_FORD_SUBJECTS, TXT_FOLDER
from utils.colors.colors_terminal import Bcolors


def load_csv_subjects():
    """Load subject mapping from FORD subjects CSV"""
    csv_path = CSV_FOLDER / CSV_FORD_SUBJECTS
    df = pd.read_csv(csv_path)
    
    subject_mapping = {}
    for _, row in df.iterrows():
        doc_id = str(row['id'])
        subject = row['subject']
        
        if pd.isna(subject) or not subject:
            continue
            
        subject_mapping[doc_id] = subject
    
    print(f"{Bcolors.OKGREEN}FORD CSV loaded: {len(subject_mapping)} documents with subjects{Bcolors.ENDC}")
    return subject_mapping


def create_dataset(subject_mapping, min_frequency=5, max_per_subject=200, random_state=42):
    """
    Create dataset from txt files + CSV subjects with max samples per subject
    
    Args:
        subject_mapping: Dictionary mapping document IDs to subjects
        min_frequency: Minimum number of documents required per subject
        max_per_subject: Maximum number of documents per subject (for balancing)
        random_state: Random seed for reproducible sampling
        
    Returns:
        tuple: (documents, labels, document_ids)
    """
    # Set random seed for reproducible results
    random.seed(random_state)
    
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
    
    # Group files by subject
    subject_files = {}
    for txt_file in txt_files:
        doc_id = txt_file.replace('.txt', '')
        
        if doc_id not in subject_mapping:
            continue
            
        subject = subject_mapping[doc_id]
        if subject not in frequent_subjects:
            continue
        
        if subject not in subject_files:
            subject_files[subject] = []
        subject_files[subject].append(txt_file)
    
    # Limit files per subject and create dataset
    documents = []
    labels = []
    document_ids = []
    
    for subject, files in subject_files.items():
        # Randomly sample max_per_subject files (consistent random state)
        if len(files) > max_per_subject:
            files = random.sample(files, max_per_subject)
            print(f"{Bcolors.WARNING}Limited {subject} to {max_per_subject} documents (had {len(subject_files[subject])}){Bcolors.ENDC}")
        
        for txt_file in files:
            doc_id = txt_file.replace('.txt', '')
            
            # Read text file
            txt_path = TXT_FOLDER / txt_file
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                    
                # Basic preprocessing - normalize whitespace and lowercase
                processed_text = " ".join(text_content.split()).lower()
                
                if processed_text:
                    documents.append(processed_text)
                    labels.append(subject)
                    document_ids.append(doc_id)
                    
            except Exception as e:
                print(f"Error reading {txt_file}: {e}")
                continue
    
    print(f"{Bcolors.OKGREEN}Dataset created: {len(documents)} documents, {len(set(labels))} subjects{Bcolors.ENDC}")
    
    # Show final subjects distribution
    label_counts = Counter(labels)
    print("Final subjects distribution:")
    for subject, count in label_counts.most_common():
        print(f"  {subject}: {count}")
    
    return documents, labels, document_ids


def preprocess_text(text):
    """Simple text preprocessing for consistency across models"""
    if not text:
        return ""
    return " ".join(text.split()).lower()