"""
Create CSV with ID, Year, and FORD-normalized subjects from full sedici.csv
Uses EXACT same logic as download_prepare_clean_normalize_sedici_dataset
"""
import pandas as pd
import sys
from pathlib import Path
from collections import Counter

# Add parent directory to path to import constants
sys.path.append(str(Path(__file__).parent.parent))
from constants import CSV_FOLDER, CSV_SEDICI, CSV_FORD_SUBJECTS, FORD_SEDICI_MATERIAS, COLUMNS_TYPES, VALID_TYPES
from utils.colors.colors_terminal import Bcolors

def combine_non_nulls(row, values):
    """EXACT same function as original"""
    non_nulls = [row[col] for col in values if pd.notna(row[col])]
    if not non_nulls:
        return None
    return non_nulls[0] if len(non_nulls) == 1 else non_nulls

def safe_split(value, delimiter, part=0):
    """EXACT same function as original"""
    if isinstance(value, str) and delimiter in value:
        return value.split(delimiter)[part].strip()
    return value

def transform_uri(uri):
    """EXACT same function as original"""
    if not isinstance(uri, str):
        return None
    try:
        main_uri = uri.split("||")[0]  # Quedarse con la parte de sedici
        return main_uri.split("handle/")[1].replace("/", "-")
    except Exception as e:
        return None
    
def transform_subject(subject):
    """EXACT same function as original"""
    if not isinstance(subject, str):
        return None
    try:
        key = safe_split(safe_split(subject, "||"), "::")
        return FORD_SEDICI_MATERIAS.get(key, None)
    except Exception as e:
        return None

def extract_year(date_str):
    """Extract year from date string"""
    if not isinstance(date_str, str):
        return None
    try:
        date_obj = pd.to_datetime(date_str, errors='coerce')
        if pd.notna(date_obj):
            return date_obj.year
        return None
    except:
        return None

def create_ford_subjects_csv():
    """Create CSV with ID, Year, and FORD subjects - following EXACT original logic"""
    
    print(f"{Bcolors.HEADER}=== Creating FORD Subjects CSV ==={Bcolors.ENDC}")
    
    # Load full sedici.csv
    csv_path = CSV_FOLDER / CSV_SEDICI
    
    if not csv_path.exists():
        print(f"{Bcolors.FAIL}CSV file not found: {csv_path}{Bcolors.ENDC}")
        return
    
    print(f"{Bcolors.OKBLUE}Loading CSV: {csv_path}{Bcolors.ENDC}")
    df = pd.read_csv(csv_path, low_memory=False)
    
    print(f"Original dataset size: {len(df)} rows")
    
    # STEP 1: Column matching and merging - EXACT same logic as original
    print(f"{Bcolors.OKBLUE}Step 1: Column matching and merging...{Bcolors.ENDC}")
    final_columns = {key: [col for col in df.columns if key in col] for key in COLUMNS_TYPES}
    selected_cols = [col for cols in final_columns.values() for col in cols]
    subset_df = df[selected_cols].copy()

    # Remove duplicated columns
    subset_df = subset_df.loc[:, ~subset_df.columns.duplicated()]

    # Merge multiple columns
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

    # Delete duplicated columns again
    subset_df = subset_df.loc[:, ~subset_df.columns.duplicated()]
    
    print(f"After column processing: {len(subset_df)} rows")

    # STEP 2: Date processing - NO FILTERING (we want all years!)
    print(f"{Bcolors.OKBLUE}Step 2: Date processing...{Bcolors.ENDC}")
    subset_df['dc.date.issued'] = pd.to_datetime(subset_df['dc.date.issued'], errors='coerce')
    print(f"Processed dates, keeping all years: {len(subset_df)} rows")

    # STEP 3: Document type filtering - EXACT same logic as original
    print(f"{Bcolors.OKBLUE}Step 3: Document type filtering...{Bcolors.ENDC}")
    print(f"Valid types: {VALID_TYPES}")
    if 'dc.type' in subset_df.columns:
        original_size = len(subset_df)
        subset_df = subset_df[subset_df['dc.type'].isin(VALID_TYPES)]
        print(f"After type filter: {len(subset_df)} rows (removed {original_size - len(subset_df)})")
    else:
        print(f"{Bcolors.WARNING}dc.type column not found, skipping type filter{Bcolors.ENDC}")

    # STEP 4: Quality sorting - EXACT same logic as original
    print(f"{Bcolors.OKBLUE}Step 4: Quality sorting...{Bcolors.ENDC}")
    subset_df["not_null_count"] = subset_df.notnull().sum(axis=1)
    subset_df = subset_df.sort_values(by='not_null_count', ascending=False).drop(columns=['not_null_count'])

    # STEP 5: Transform URI to ID - EXACT same logic as original
    print(f"{Bcolors.OKBLUE}Step 5: Transforming URIs to IDs...{Bcolors.ENDC}")
    subset_df['id'] = subset_df['dc.identifier.uri'].apply(transform_uri)
    original_size = len(subset_df)
    subset_df = subset_df.dropna(subset=['id'])
    print(f"After URI transformation: {len(subset_df)} rows (removed {original_size - len(subset_df)})")

    # STEP 6: Transform subjects to FORD - EXACT same logic as original
    print(f"{Bcolors.OKBLUE}Step 6: Transforming subjects to FORD...{Bcolors.ENDC}")
    subset_df['sedici.subject.materias'] = subset_df['sedici.subject.materias'].apply(transform_subject)
    original_size = len(subset_df)
    subset_df = subset_df.dropna(subset=['sedici.subject.materias'])
    print(f"After subject transformation: {len(subset_df)} rows (removed {original_size - len(subset_df)})")

    # STEP 7: Extract year and create final dataset
    print(f"{Bcolors.OKBLUE}Step 7: Creating final dataset...{Bcolors.ENDC}")
    subset_df['year'] = subset_df['dc.date.issued'].dt.year

    # Create final dataset with only the columns we need
    final_df = subset_df[['id', 'year', 'sedici.subject.materias']].copy()
    final_df = final_df.rename(columns={'sedici.subject.materias': 'subject'})
    
    # Remove duplicates based on ID
    original_size = len(final_df)
    final_df = final_df.drop_duplicates(subset=['id'])
    print(f"After removing duplicates: {len(final_df)} rows (removed {original_size - len(final_df)})")

    print(f"\n{Bcolors.OKGREEN}Processing complete!{Bcolors.ENDC}")

    # Show year distribution
    year_counts = final_df['year'].value_counts().sort_index()
    print(f"\n{Bcolors.HEADER}=== Year Distribution ==={Bcolors.ENDC}")
    print(f"Years range: {year_counts.index.min()} - {year_counts.index.max()}")
    print("Documents per year:")
    for year, count in year_counts.items():
        print(f"  {year}: {count:,} documents")

    # Show subject distribution
    subject_counts = final_df['subject'].value_counts()
    print(f"\n{Bcolors.HEADER}=== Subject Distribution ==={Bcolors.ENDC}")
    print(f"Total subjects: {len(subject_counts)}")
    print("Documents per subject:")
    
    for subject, count in subject_counts.items():
        print(f"  {subject}: {count:,} documents")

    # Show subjects with different frequency thresholds
    print(f"\n{Bcolors.OKBLUE}Subjects by frequency thresholds:{Bcolors.ENDC}")
    for threshold in [5, 10, 20, 50, 100]:
        subjects_above_threshold = sum(1 for count in subject_counts if count >= threshold)
        print(f"  >= {threshold} documents: {subjects_above_threshold} subjects")

    # Show year distribution for subjects with < 200 documents
    print(f"\n{Bcolors.HEADER}=== Year Analysis for Subjects < 200 Documents ==={Bcolors.ENDC}")
    low_count_subjects = [subject for subject, count in subject_counts.items() if count < 200]
    
    for subject in low_count_subjects:
        subject_data = final_df[final_df['subject'] == subject]
        years = sorted(subject_data['year'].unique())
        year_range = f"{min(years)}-{max(years)}" if len(years) > 1 else str(years[0])
        
        print(f"  {subject} ({len(subject_data)} docs): {year_range}")
        print(f"    Years: {sorted(years)}")

    # Save to CSV
    output_path = CSV_FOLDER / CSV_FORD_SUBJECTS
    print(f"\n{Bcolors.OKGREEN}Saving to: {output_path}{Bcolors.ENDC}")
    final_df.to_csv(output_path, index=False)
    
    print(f"{Bcolors.OKGREEN}CSV created successfully!{Bcolors.ENDC}")
    
    return output_path

if __name__ == "__main__":
    create_ford_subjects_csv()