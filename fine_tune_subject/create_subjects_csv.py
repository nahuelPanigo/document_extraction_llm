"""
Create CSV with ID, Year, and normalized subjects from full sedici.csv
Uses the active SUBJECT_MAPPING from constants to map SEDICI materials to target categories.
To change classification standard, update SUBJECT_MAPPING in constants.py.
"""
import pandas as pd
import sys
from pathlib import Path
from collections import Counter

sys.path.append(str(Path(__file__).parent.parent))
from constants import CSV_FOLDER, CSV_SEDICI, CSV_SUBJECTS, SUBJECT_MAPPING, COLUMNS_TYPES, VALID_TYPES
from utils.colors.colors_terminal import Bcolors
from download_prepare_clean_normalize_sedici_dataset.extract_data_from_csv_sedici import safe_split, transform_subject


def combine_non_nulls(row, values):
    non_nulls = [row[col] for col in values if pd.notna(row[col])]
    if not non_nulls:
        return None
    return non_nulls[0] if len(non_nulls) == 1 else non_nulls


def transform_uri(uri):
    if not isinstance(uri, str):
        return None
    try:
        main_uri = uri.split("||")[0]
        return main_uri.split("handle/")[1].replace("/", "-")
    except Exception as e:
        return None


def extract_year(date_str):
    if not isinstance(date_str, str):
        return None
    try:
        date_obj = pd.to_datetime(date_str, errors='coerce')
        if pd.notna(date_obj):
            return date_obj.year
        return None
    except:
        return None


def create_subjects_csv():
    """Create CSV with ID, Year, and subjects using the active SUBJECT_MAPPING"""

    print(f"{Bcolors.HEADER}=== Creating Subjects CSV ==={Bcolors.ENDC}")

    csv_path = CSV_FOLDER / CSV_SEDICI

    if not csv_path.exists():
        print(f"{Bcolors.FAIL}CSV file not found: {csv_path}{Bcolors.ENDC}")
        return

    print(f"{Bcolors.OKBLUE}Loading CSV: {csv_path}{Bcolors.ENDC}")
    df = pd.read_csv(csv_path, low_memory=False)

    print(f"Original dataset size: {len(df)} rows")

    # STEP 1: Column matching and merging
    print(f"{Bcolors.OKBLUE}Step 1: Column matching and merging...{Bcolors.ENDC}")
    final_columns = {key: [col for col in df.columns if key in col] for key in COLUMNS_TYPES}
    selected_cols = [col for cols in final_columns.values() for col in cols]
    subset_df = df[selected_cols].copy()

    subset_df = subset_df.loc[:, ~subset_df.columns.duplicated()]

    for key, values in final_columns.items():
        if not values:
            continue
        if COLUMNS_TYPES[key]['cant'] == "unique":
            subset_df[key] = subset_df[values].ffill(axis=1).bfill(axis=1).iloc[:, 0]
            subset_df[key] = subset_df[key].where(subset_df[key].notnull(), None)
        else:
            subset_df[key] = subset_df.apply(lambda row: combine_non_nulls(row, values), axis=1)

    extra_cols = [col for col in selected_cols if col not in COLUMNS_TYPES]
    subset_df.drop(extra_cols, axis=1, inplace=True, errors='ignore')

    subset_df = subset_df.loc[:, ~subset_df.columns.duplicated()]

    print(f"After column processing: {len(subset_df)} rows")

    # STEP 2: Date processing - NO FILTERING (we want all years!)
    print(f"{Bcolors.OKBLUE}Step 2: Date processing...{Bcolors.ENDC}")
    subset_df['dc.date.issued'] = pd.to_datetime(subset_df['dc.date.issued'], errors='coerce')
    print(f"Processed dates, keeping all years: {len(subset_df)} rows")

    # STEP 3: Document type filtering
    print(f"{Bcolors.OKBLUE}Step 3: Document type filtering...{Bcolors.ENDC}")
    print(f"Valid types: {VALID_TYPES}")
    if 'dc.type' in subset_df.columns:
        original_size = len(subset_df)
        subset_df = subset_df[subset_df['dc.type'].isin(VALID_TYPES)]
        print(f"After type filter: {len(subset_df)} rows (removed {original_size - len(subset_df)})")
    else:
        print(f"{Bcolors.WARNING}dc.type column not found, skipping type filter{Bcolors.ENDC}")

    # STEP 4: Quality sorting
    print(f"{Bcolors.OKBLUE}Step 4: Quality sorting...{Bcolors.ENDC}")
    subset_df["not_null_count"] = subset_df.notnull().sum(axis=1)
    subset_df = subset_df.sort_values(by='not_null_count', ascending=False).drop(columns=['not_null_count'])

    # STEP 5: Transform URI to ID
    print(f"{Bcolors.OKBLUE}Step 5: Transforming URIs to IDs...{Bcolors.ENDC}")
    subset_df['id'] = subset_df['dc.identifier.uri'].apply(transform_uri)
    original_size = len(subset_df)
    subset_df = subset_df.dropna(subset=['id'])
    print(f"After URI transformation: {len(subset_df)} rows (removed {original_size - len(subset_df)})")

    # STEP 6: Transform subjects using active SUBJECT_MAPPING
    print(f"{Bcolors.OKBLUE}Step 6: Transforming subjects...{Bcolors.ENDC}")
    subset_df['sedici.subject.materias'] = subset_df['sedici.subject.materias'].apply(transform_subject)
    original_size = len(subset_df)
    subset_df = subset_df.dropna(subset=['sedici.subject.materias'])
    print(f"After subject transformation: {len(subset_df)} rows (removed {original_size - len(subset_df)})")

    # STEP 7: Extract year and create final dataset
    print(f"{Bcolors.OKBLUE}Step 7: Creating final dataset...{Bcolors.ENDC}")
    subset_df['year'] = subset_df['dc.date.issued'].dt.year

    final_df = subset_df[['id', 'year', 'sedici.subject.materias']].copy()
    final_df = final_df.rename(columns={'sedici.subject.materias': 'subject'})

    original_size = len(final_df)
    final_df = final_df.drop_duplicates(subset=['id'])
    print(f"After removing duplicates: {len(final_df)} rows (removed {original_size - len(final_df)})")

    print(f"\n{Bcolors.OKGREEN}Processing complete!{Bcolors.ENDC}")

    # Show subject distribution
    subject_counts = final_df['subject'].value_counts()
    print(f"\n{Bcolors.HEADER}=== Subject Distribution ==={Bcolors.ENDC}")
    print(f"Total subjects: {len(subject_counts)}")
    print("Documents per subject:")

    for subject, count in subject_counts.items():
        print(f"  {subject}: {count:,} documents")

    print(f"\n{Bcolors.OKBLUE}Subjects by frequency thresholds:{Bcolors.ENDC}")
    for threshold in [5, 10, 20, 50, 100]:
        subjects_above_threshold = sum(1 for count in subject_counts if count >= threshold)
        print(f"  >= {threshold} documents: {subjects_above_threshold} subjects")

    # Save to CSV
    output_path = CSV_FOLDER / CSV_SUBJECTS
    print(f"\n{Bcolors.OKGREEN}Saving to: {output_path}{Bcolors.ENDC}")
    final_df.to_csv(output_path, index=False)

    print(f"{Bcolors.OKGREEN}CSV created successfully!{Bcolors.ENDC}")

    return output_path

if __name__ == "__main__":
    create_subjects_csv()
