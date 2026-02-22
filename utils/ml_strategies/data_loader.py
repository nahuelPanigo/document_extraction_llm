"""
Shared dataset loading and creation functions.
Generic versions that accept parameters for flexibility across modules.
"""
import pandas as pd
import random
import os
from collections import Counter
from utils.colors.colors_terminal import Bcolors


def load_csv_labels(csv_path, id_column='id', label_column='subject'):
    """
    Generic: load CSV -> {id: label} mapping.

    Args:
        csv_path: Path to the CSV file
        id_column: Name of the ID column
        label_column: Name of the label column

    Returns:
        dict: Mapping of document IDs to labels
    """
    df = pd.read_csv(csv_path)

    label_mapping = {}
    for _, row in df.iterrows():
        doc_id = str(row[id_column])
        label = row[label_column]

        if pd.isna(label) or not label:
            continue

        label_mapping[doc_id] = label

    print(f"{Bcolors.OKGREEN}CSV loaded: {len(label_mapping)} documents with labels{Bcolors.ENDC}")
    return label_mapping


def create_dataset(label_mapping, txt_folder, min_frequency=5, max_per_label=200, random_state=42):
    """
    Generic: read txt files + label mapping -> (documents, labels, doc_ids).

    Args:
        label_mapping: Dictionary mapping document IDs to labels
        txt_folder: Path to folder with .txt files
        min_frequency: Minimum number of documents required per label
        max_per_label: Maximum number of documents per label (for balancing)
        random_state: Random seed for reproducible sampling

    Returns:
        tuple: (documents, labels, document_ids)
    """
    random.seed(random_state)

    if not txt_folder.exists():
        print(f"{Bcolors.FAIL}Folder not found: {txt_folder}{Bcolors.ENDC}")
        return [], [], []

    txt_files = [f for f in os.listdir(txt_folder) if f.endswith('.txt')]
    print(f"{Bcolors.OKBLUE}Found {len(txt_files)} txt files{Bcolors.ENDC}")

    # Get available labels for files we have
    available_labels = []
    for txt_file in txt_files:
        doc_id = txt_file.replace('.txt', '')
        if doc_id in label_mapping:
            available_labels.append(label_mapping[doc_id])

    # Filter by frequency
    label_counts = Counter(available_labels)
    frequent_labels = {label for label, count in label_counts.items()
                       if count >= min_frequency}

    print(f"{Bcolors.OKBLUE}Labels with >= {min_frequency} documents: {len(frequent_labels)}{Bcolors.ENDC}")

    # Group files by label
    label_files = {}
    for txt_file in txt_files:
        doc_id = txt_file.replace('.txt', '')

        if doc_id not in label_mapping:
            continue

        label = label_mapping[doc_id]
        if label not in frequent_labels:
            continue

        if label not in label_files:
            label_files[label] = []
        label_files[label].append(txt_file)

    # Limit files per label and create dataset
    documents = []
    labels = []
    document_ids = []

    for label, files in label_files.items():
        if len(files) > max_per_label:
            files = random.sample(files, max_per_label)
            print(f"{Bcolors.WARNING}Limited {label} to {max_per_label} documents (had {len(label_files[label])}){Bcolors.ENDC}")

        for txt_file in files:
            doc_id = txt_file.replace('.txt', '')

            txt_path = txt_folder / txt_file
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()

                processed_text = " ".join(text_content.split()).lower()

                if processed_text:
                    documents.append(processed_text)
                    labels.append(label)
                    document_ids.append(doc_id)

            except Exception as e:
                print(f"Error reading {txt_file}: {e}")
                continue

    print(f"{Bcolors.OKGREEN}Dataset created: {len(documents)} documents, {len(set(labels))} labels{Bcolors.ENDC}")

    # Show final distribution
    final_counts = Counter(labels)
    print("Final distribution:")
    for label, count in final_counts.most_common():
        print(f"  {label}: {count}")

    return documents, labels, document_ids
