"""
Create CSV with ID, Year, and document type from full sedici.csv.
Filters to VALID_TYPES, takes top SAMPLES_PER_TYPE per type (newest first).
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from constants import CSV_FOLDER, CSV_SEDICI, CSV_TYPES, COLUMNS_TYPES, VALID_TYPES, SAMPLES_PER_TYPE
from utils.colors.colors_terminal import Bcolors


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
    except Exception:
        return None


def create_types_csv():
    """Create CSV with ID, Year, and type from sedici.csv"""

    print(f"{Bcolors.HEADER}=== Creating Types CSV ==={Bcolors.ENDC}")

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

    # STEP 2: Date processing
    print(f"{Bcolors.OKBLUE}Step 2: Date processing...{Bcolors.ENDC}")
    subset_df['dc.date.issued'] = pd.to_datetime(subset_df['dc.date.issued'], errors='coerce')

    # Sort by date descending (newest first)
    subset_df = subset_df.sort_values(by='dc.date.issued', ascending=False, na_position='last')
    print(f"Sorted by date descending (newest first): {len(subset_df)} rows")

    # STEP 3: Document type filtering
    print(f"{Bcolors.OKBLUE}Step 3: Document type filtering...{Bcolors.ENDC}")
    print(f"Valid types: {VALID_TYPES}")
    if 'dc.type' in subset_df.columns:
        original_size = len(subset_df)
        subset_df = subset_df[subset_df['dc.type'].isin(VALID_TYPES)]
        print(f"After type filter: {len(subset_df)} rows (removed {original_size - len(subset_df)})")
    else:
        print(f"{Bcolors.FAIL}dc.type column not found!{Bcolors.ENDC}")
        return

    # STEP 4: Transform URI to ID
    print(f"{Bcolors.OKBLUE}Step 4: Transforming URIs to IDs...{Bcolors.ENDC}")
    subset_df['id'] = subset_df['dc.identifier.uri'].apply(transform_uri)
    original_size = len(subset_df)
    subset_df = subset_df.dropna(subset=['id'])
    print(f"After URI transformation: {len(subset_df)} rows (removed {original_size - len(subset_df)})")

    # STEP 5: Remove duplicates
    original_size = len(subset_df)
    subset_df = subset_df.drop_duplicates(subset=['id'])
    print(f"After removing duplicates: {len(subset_df)} rows (removed {original_size - len(subset_df)})")

    # STEP 6: Take top SAMPLES_PER_TYPE per type (already sorted by date desc)
    print(f"{Bcolors.OKBLUE}Step 5: Taking top {SAMPLES_PER_TYPE} per type...{Bcolors.ENDC}")
    balanced_frames = []
    for doc_type in VALID_TYPES:
        type_df = subset_df[subset_df['dc.type'] == doc_type].head(SAMPLES_PER_TYPE)
        balanced_frames.append(type_df)
        print(f"  {doc_type}: {len(type_df)} documents")

    subset_df = pd.concat(balanced_frames, ignore_index=True)

    # STEP 7: Extract year and create final dataset
    print(f"{Bcolors.OKBLUE}Step 6: Creating final dataset...{Bcolors.ENDC}")
    subset_df['year'] = subset_df['dc.date.issued'].dt.year

    final_df = subset_df[['id', 'year', 'dc.type']].copy()
    final_df = final_df.rename(columns={'dc.type': 'type'})

    print(f"\n{Bcolors.OKGREEN}Processing complete!{Bcolors.ENDC}")

    # Show type distribution
    type_counts = final_df['type'].value_counts()
    print(f"\n{Bcolors.HEADER}=== Type Distribution ==={Bcolors.ENDC}")
    print(f"Total types: {len(type_counts)}")
    print("Documents per type:")

    for doc_type, count in type_counts.items():
        print(f"  {doc_type}: {count:,} documents")

    # Save to CSV
    output_path = CSV_FOLDER / CSV_TYPES
    print(f"\n{Bcolors.OKGREEN}Saving to: {output_path}{Bcolors.ENDC}")
    final_df.to_csv(output_path, index=False)

    print(f"{Bcolors.OKGREEN}CSV created successfully!{Bcolors.ENDC}")

    return output_path


if __name__ == "__main__":
    create_types_csv()
