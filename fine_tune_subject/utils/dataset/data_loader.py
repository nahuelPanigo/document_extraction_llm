"""
Shared dataset loading and creation functions for subject classification.
Thin wrapper around utils.ml_strategies.data_loader with subject-specific defaults.
"""
from utils.ml_strategies.data_loader import load_csv_labels, create_dataset as _create_dataset
from constants import CSV_FOLDER, CSV_SUBJECTS, TXT_FOLDER


def load_csv_subjects():
    """Load subject mapping from subjects CSV"""
    return load_csv_labels(CSV_FOLDER / CSV_SUBJECTS, label_column='subject')


def create_dataset(subject_mapping, min_frequency=5, max_per_subject=200, random_state=42):
    """
    Create dataset from txt files + CSV subjects with max samples per subject.
    Backward-compatible wrapper.
    """
    return _create_dataset(
        subject_mapping,
        TXT_FOLDER,
        min_frequency=min_frequency,
        max_per_label=max_per_subject,
        random_state=random_state
    )


def preprocess_text(text):
    """Simple text preprocessing for consistency across models"""
    if not text:
        return ""
    return " ".join(text.split()).lower()
